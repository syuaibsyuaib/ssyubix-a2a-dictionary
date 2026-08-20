"""
token_counter.py
Wrapper resmi untuk endpoint count_tokens dari Claude Platform API.

Sumber referensi (dibaca 2026-07-31):
https://platform.claude.com/docs/en/build-with-claude/token-counting

Catatan penting dari dokumentasi resmi:
- Endpoint ini GRATIS (tidak kena biaya), tapi tetap kena rate limit RPM.
- Hasilnya adalah ESTIMASI; jumlah token aktual saat message dibuat bisa
  sedikit berbeda.
- Claude 4.7+ (termasuk Claude Fable 5 / Claude Mythos 5) memakai tokenizer
  BARU yang menghasilkan kurang lebih 30% LEBIH BANYAK token dibanding
  model-model sebelumnya untuk teks yang sama. JANGAN pakai ulang hasil
  hitung dari satu model untuk model lain -- selalu hitung ulang dengan
  `model` yang benar-benar akan dipakai di produksi.

Requirement:
    pip install anthropic
    set ANTHROPIC_API_KEY di environment variable
"""

from __future__ import annotations
import os
import argparse
import json
from dataclasses import dataclass, asdict
from typing import Optional

try:
    import anthropic
except ImportError as e:
    raise ImportError(
        "Package 'anthropic' belum terinstall. Jalankan: pip install anthropic"
    ) from e


DEFAULT_MODEL = "claude-sonnet-5"


@dataclass
class CompressionResult:
    """Hasil perbandingan token natural language vs AILang (atau teks lain)."""
    model: str
    natural_tokens: int
    compressed_tokens: int
    tokens_saved: int
    efficiency_pct: float


def get_client() -> "anthropic.Anthropic":
    """Buat client Anthropic. Membaca ANTHROPIC_API_KEY dari environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY tidak ditemukan di environment variable. "
            "Set dulu sebelum menjalankan tool ini."
        )
    return anthropic.Anthropic(api_key=api_key)


def count_tokens(
    text: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    client: Optional["anthropic.Anthropic"] = None,
) -> int:
    """
    Hitung jumlah input_tokens untuk satu pesan user via endpoint resmi
    count_tokens. TIDAK mengirim message asli (tidak kena biaya generasi).
    """
    if client is None:
        client = get_client()

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }
    if system:
        kwargs["system"] = system

    response = client.messages.count_tokens(**kwargs)
    return response.input_tokens


def compare_efficiency(
    natural_text: str,
    compressed_text: str,
    model: str = DEFAULT_MODEL,
    client: Optional["anthropic.Anthropic"] = None,
) -> CompressionResult:
    """
    Bandingkan token natural_text vs compressed_text (mis. AILang) pada
    model yang SAMA. Ini yang dipakai untuk memvalidasi klaim efisiensi
    di README.md / CRITICAL_FINDINGS.md secara empiris.
    """
    if client is None:
        client = get_client()

    natural_tokens = count_tokens(natural_text, model=model, client=client)
    compressed_tokens = count_tokens(compressed_text, model=model, client=client)

    tokens_saved = natural_tokens - compressed_tokens
    efficiency_pct = (
        round((tokens_saved / natural_tokens) * 100, 2)
        if natural_tokens > 0
        else 0.0
    )

    return CompressionResult(
        model=model,
        natural_tokens=natural_tokens,
        compressed_tokens=compressed_tokens,
        tokens_saved=tokens_saved,
        efficiency_pct=efficiency_pct,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hitung/bandingkan token via endpoint resmi Claude count_tokens."
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Model target (default: {DEFAULT_MODEL}). "
             "PENTING: hasil beda antar model, jangan dicampur.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_count = sub.add_parser("count", help="Hitung token 1 teks")
    p_count.add_argument("text", help="Teks yang mau dihitung")

    p_cmp = sub.add_parser("compare", help="Bandingkan 2 teks (natural vs compressed)")
    p_cmp.add_argument("natural", help="Teks natural language")
    p_cmp.add_argument("compressed", help="Teks terkompresi (mis. AILang)")

    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    client = get_client()

    if args.cmd == "count":
        n = count_tokens(args.text, model=args.model, client=client)
        print(json.dumps({"model": args.model, "input_tokens": n}, indent=2))
    elif args.cmd == "compare":
        result = compare_efficiency(
            args.natural, args.compressed, model=args.model, client=client
        )
        print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
