"""
encoding_bench.py
Benchmark: pendekatan encoding mana yang paling efisien token untuk A2A?

METODOLOGI
----------
Membandingkan encoding "apel ke apel" dengan cara MENGUNCI KAPASITAS MAKNA.
Semua kandidat mengekspresikan frame yang sama: 3 field x 256 nilai = 24 bit
(16.777.216 pesan berbeda). Jadi yang dibandingkan bukan "pesan mana yang
lebih pendek", tapi "berapa ongkos token untuk kapasitas makna yang sama".

Metrik utama = BIT PER TOKEN. Plafonnya log2(vocab_size); tidak ada encoding
yang bisa melampauinya, karena satu token maksimal membawa log2(V) bit.

PENTING SOAL TOKENIZER
----------------------
Pengukuran token HANYA lewat endpoint resmi `count_tokens` (butuh kredensial).
JANGAN pakai tiktoken/gpt-tokenizer sebagai pengganti: itu tokenizer OpenAI,
undercount ~15-20% untuk Claude dan jauh lebih meleset untuk simbol non-ASCII
-- persis kasus yang sedang kita uji. Lebih baik kolom kosong daripada angka
yang menyesatkan (lihat data/README_token_measurements.md).

Tanpa kredensial, tool ini tetap menghasilkan analisis STRUKTURAL yang eksak
dan tidak butuh tokenizer sama sekali: kapasitas bit, karakter, byte UTF-8,
bit/karakter, dan jumlah karakter non-ASCII.

PEMAKAIAN
    python3 claude_tools/encoding_bench.py analyze
    python3 claude_tools/encoding_bench.py analyze --out data/encoding_bench.csv
    python3 claude_tools/encoding_bench.py measure --model claude-opus-5   # butuh kredensial
    python3 claude_tools/encoding_bench.py validate-codebook --model claude-opus-5
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Frame semantik yang dikunci: 3 field x 8 bit
# ---------------------------------------------------------------------------

FIELD_BITS = 8
FIELD_COUNT = 3
TOTAL_BITS = FIELD_BITS * FIELD_COUNT          # 24 bit
CAPACITY = 2 ** TOTAL_BITS                      # 16.777.216 makna berbeda

# Instance konkret yang di-encode semua kandidat (arti identik):
#   action=17 -> "retrieve", object=42 -> "user.profile", modifier=7 -> "activity_logs"
SAMPLE = (17, 42, 7)
SAMPLE_INT = (SAMPLE[0] << 16) | (SAMPLE[1] << 8) | SAMPLE[2]

# Codebook kata: HARUS diverifikasi 1-token via `validate-codebook` sebelum dipakai.
# Ini baru kandidat awal, bukan hasil ukur.
CODEBOOK_SEED = [
    "get", "set", "add", "run", "read", "send", "find", "make",
    "user", "file", "data", "list", "task", "node", "item", "log",
    "all", "new", "old", "one", "two", "top", "end", "now",
]


def _base_n(value: int, alphabet: str, width: int) -> str:
    """Encode integer ke basis len(alphabet), dipad ke lebar tetap."""
    if value < 0:
        raise ValueError("value harus non-negatif")
    base = len(alphabet)
    out = []
    v = value
    while v:
        v, rem = divmod(v, base)
        out.append(alphabet[rem])
    s = "".join(reversed(out)) or alphabet[0]
    return s.rjust(width, alphabet[0])


def _fixed_width(value: int, alphabet: str) -> str:
    """Lebar tetap = lebar minimum yang muat TOTAL_BITS pada alfabet itu."""
    width = math.ceil(TOTAL_BITS / math.log2(len(alphabet)))
    return _base_n(value, alphabet, width)


# ---------------------------------------------------------------------------
# Kandidat encoding
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """Satu skema encoding beserta teks hasil encode-nya."""
    scheme_id: str
    family: str
    text: str
    note: str = ""
    # Diisi tahap `measure` (butuh kredensial). None = belum diukur.
    tokens: Optional[int] = None

    # -- metrik struktural: eksak, tidak butuh tokenizer --------------------
    @property
    def characters(self) -> int:
        return len(self.text)

    @property
    def utf8_bytes(self) -> int:
        return len(self.text.encode("utf-8"))

    @property
    def non_ascii_chars(self) -> int:
        return sum(1 for ch in self.text if ord(ch) > 127)

    @property
    def bits_per_char(self) -> float:
        return TOTAL_BITS / self.characters if self.characters else 0.0

    @property
    def bits_per_byte(self) -> float:
        return TOTAL_BITS / self.utf8_bytes if self.utf8_bytes else 0.0

    # -- metrik token: hanya valid setelah diukur resmi ---------------------
    @property
    def bits_per_token(self) -> Optional[float]:
        if not self.tokens:
            return None
        return TOTAL_BITS / self.tokens

    def pct_of_ceiling(self, vocab_size: int) -> Optional[float]:
        bpt = self.bits_per_token
        if bpt is None:
            return None
        return round(bpt / math.log2(vocab_size) * 100, 1)


def build_candidates(codebook: Optional[list[str]] = None) -> list[Candidate]:
    """Semua kandidat meng-encode SAMPLE, jadi kapasitas maknanya identik."""
    book = codebook or CODEBOOK_SEED
    a, o, m = SAMPLE

    def cb(idx: int) -> str:
        return book[idx % len(book)]

    return [
        Candidate(
            "natural_full", "natural",
            "Can you please retrieve the user's profile information from the "
            "database and include their recent activity logs?",
            "baseline: bahasa natural lengkap",
        ),
        Candidate(
            "natural_terse", "natural",
            "retrieve user profile with activity logs",
            "bahasa natural dipadatkan, masih transparan",
        ),
        Candidate(
            "json_min", "json",
            '{"act":"retrieve","obj":"user.profile","inc":"activity_logs"}',
            "JSON minified, key pendek",
        ),
        Candidate(
            "json_min_numeric", "json",
            '{"a":%d,"o":%d,"m":%d}' % (a, o, m),
            "JSON minified dengan ID numerik",
        ),
        Candidate(
            "ailang_v01_spaced", "ailang",
            "{act: retrieve | data: {obj: user.profile, inc: activity_logs}}",
            "AILang v0.1 persis seperti di AILANG_DRAFT.md (ada spasi)",
        ),
        Candidate(
            "ailang_min", "ailang",
            "{act:retrieve|data:{obj:user.profile,inc:activity_logs}}",
            "AILang zero-whitespace (checkpoint #1)",
        ),
        Candidate(
            "ailang_unicode", "ailang",
            "{act:retrieve|obj:user.profile∧inc:activity_logs◆Δ:∅}",
            "AILang pakai simbol Unicode -- menguji hipotesis simbol mahal",
        ),
        Candidate(
            "binary_fixed", "fixed_width",
            _fixed_width(SAMPLE_INT, "01"),
            "IDE USER: pola biner, panjang tetap 24 char",
        ),
        Candidate(
            "hex_fixed", "fixed_width",
            _fixed_width(SAMPLE_INT, "0123456789ABCDEF"),
            "basis 16, panjang tetap",
        ),
        Candidate(
            "base36_fixed", "fixed_width",
            _fixed_width(SAMPLE_INT, "0123456789abcdefghijklmnopqrstuvwxyz"),
            "basis 36, panjang tetap",
        ),
        Candidate(
            "base64_fixed", "fixed_width",
            _fixed_width(
                SAMPLE_INT,
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
            ),
            "basis 64, panjang tetap",
        ),
        Candidate(
            "codebook_word_space", "codebook",
            " ".join([cb(a), cb(o), cb(m)]),
            "codebook kata dipisah spasi -- 1 token per konsep (target)",
        ),
        Candidate(
            "codebook_word_pipe", "codebook",
            "|".join([cb(a), cb(o), cb(m)]),
            "codebook kata dipisah pipe (tanpa spasi)",
        ),
    ]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "scheme_id", "family", "text", "semantic_bits", "semantic_capacity",
    "characters", "utf8_bytes", "non_ascii_chars", "bits_per_char",
    "bits_per_byte", "tokens", "bits_per_token", "pct_of_ceiling",
    "tokenizer_source", "measured_date", "note",
]


def write_csv(cands: list[Candidate], path: str, tokenizer_source: str,
              vocab_size: int) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_COLUMNS)
        for c in cands:
            bpt = c.bits_per_token
            w.writerow([
                c.scheme_id, c.family, c.text, TOTAL_BITS, CAPACITY,
                c.characters, c.utf8_bytes, c.non_ascii_chars,
                round(c.bits_per_char, 3), round(c.bits_per_byte, 3),
                c.tokens if c.tokens is not None else "",
                round(bpt, 3) if bpt is not None else "",
                c.pct_of_ceiling(vocab_size) if bpt is not None else "",
                tokenizer_source, date.today().isoformat(), c.note,
            ])


def print_table(cands: list[Candidate], vocab_size: int) -> None:
    measured = any(c.tokens is not None for c in cands)
    hdr = f"{'scheme_id':<22}{'char':>6}{'byte':>6}{'~ascii':>7}{'bit/char':>10}"
    if measured:
        hdr += f"{'token':>7}{'bit/token':>11}{'%plafon':>9}"
    print(hdr)
    print("-" * len(hdr))
    ordered = sorted(cands, key=lambda c: -c.bits_per_char)
    for c in ordered:
        row = (f"{c.scheme_id:<22}{c.characters:>6}{c.utf8_bytes:>6}"
               f"{c.non_ascii_chars:>7}{c.bits_per_char:>10.2f}")
        if measured:
            bpt = c.bits_per_token
            row += f"{c.tokens if c.tokens is not None else '-':>7}"
            row += f"{bpt:>11.2f}" if bpt is not None else f"{'-':>11}"
            pct = c.pct_of_ceiling(vocab_size)
            row += f"{pct:>8.1f}%" if pct is not None else f"{'-':>9}"
        print(row)


# ---------------------------------------------------------------------------
# Tahap measure (butuh kredensial resmi)
# ---------------------------------------------------------------------------

def measure(cands: list[Candidate], model: str) -> str:
    """Isi kolom tokens lewat endpoint resmi count_tokens."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import token_counter as tc  # reuse wrapper resmi yang sudah ada

    client = tc.get_client()
    for c in cands:
        c.tokens = tc.count_tokens(c.text, model=model, client=client)
    return f"anthropic count_tokens / {model}"


def validate_codebook(words: list[str], model: str) -> tuple[list[str], list[str]]:
    """Pisahkan kata yang TEPAT 1 token dari yang lebih. Butuh kredensial."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import token_counter as tc

    client = tc.get_client()
    base = tc.count_tokens("x", model=model, client=client)
    single, multi = [], []
    for w in words:
        n = tc.count_tokens(w, model=model, client=client)
        (single if n <= base else multi).append(f"{w}({n})")
    return single, multi


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_VOCAB = 100_000  # asumsi kasar untuk hitung plafon; ganti bila diketahui


def _die(exc: Exception) -> "None":
    """Keluar rapi tanpa traceback saat kredensial/dependency belum siap."""
    print(f"TIDAK BISA MENGUKUR: {exc}", file=sys.stderr)
    print(
        "\nTahap `measure` butuh kredensial Anthropic yang sah.\n"
        "Sementara itu jalankan `analyze` -- metrik strukturalnya eksak dan\n"
        "tidak butuh tokenizer sama sekali.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    p.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB,
                   help=f"ukuran vocabulary untuk plafon bit/token (default {DEFAULT_VOCAB})")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("analyze", help="analisis struktural (TANPA tokenizer)")
    pa.add_argument("--out", help="tulis hasil ke CSV")

    pm = sub.add_parser("measure", help="ukur token via endpoint resmi (butuh kredensial)")
    pm.add_argument("--model", default=DEFAULT_MODEL)
    pm.add_argument("--out", help="tulis hasil ke CSV")

    pv = sub.add_parser("validate-codebook", help="saring kata yang tepat 1 token")
    pv.add_argument("--model", default=DEFAULT_MODEL)
    pv.add_argument("--wordlist", help="file berisi 1 kata per baris (default: seed bawaan)")

    args = p.parse_args()
    ceiling = math.log2(args.vocab_size)

    if args.cmd == "validate-codebook":
        words = CODEBOOK_SEED
        if args.wordlist:
            with open(args.wordlist, encoding="utf-8") as fh:
                words = [ln.strip() for ln in fh if ln.strip()]
        try:
            single, multi = validate_codebook(words, args.model)
        except (EnvironmentError, ImportError) as exc:
            _die(exc)
        print(f"1 token  ({len(single)}): {', '.join(single)}")
        print(f">1 token ({len(multi)}): {', '.join(multi)}")
        return

    cands = build_candidates()
    print(f"Frame semantik terkunci: {FIELD_COUNT} field x {FIELD_BITS} bit "
          f"= {TOTAL_BITS} bit ({CAPACITY:,} makna berbeda)")
    print(f"Plafon teoretis: log2({args.vocab_size:,}) = {ceiling:.2f} bit/token\n")

    if args.cmd == "measure":
        try:
            source = measure(cands, args.model)
        except (EnvironmentError, ImportError) as exc:
            _die(exc)
    else:
        source = "BELUM DIUKUR (analisis struktural saja)"

    print_table(cands, args.vocab_size)
    print(f"\ntokenizer_source: {source}")

    if args.cmd == "analyze":
        print("\nCATATAN: kolom token/bit-per-token sengaja KOSONG. Endpoint resmi\n"
              "count_tokens butuh kredensial. Jangan isi pakai tiktoken -- itu\n"
              "tokenizer OpenAI dan undercount ~15-20% untuk Claude.")

    if getattr(args, "out", None):
        write_csv(cands, args.out, source, args.vocab_size)
        print(f"\nDitulis ke: {args.out}")


if __name__ == "__main__":
    main()
