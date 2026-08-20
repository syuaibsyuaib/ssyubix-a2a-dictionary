# AILang v0.1 - AI-to-AI Communication Language (DRAFT)

**Version**: 0.1.0 (Specification)  
**Status**: DRAFT - Awaiting User Feedback  
**Created**: 2026-07-31

---

## 1. OVERVIEW

AILang adalah bahasa terkompresi dirancang khusus untuk komunikasi antar AI systems dengan efisiensi token maksimal sambil mempertahankan semantic accuracy.

### Design Principles
- **Tersier Efficiency**: Minimize tokens 60-70% vs natural language
- **Unambiguous**: Dapat di-decompress dengan akurasi >99%
- **Human-Auditable**: Bisa diterjemahkan back ke natural language
- **Extensible**: Support diverse AI communication patterns
- **Performant**: Parse & execute dalam milliseconds

---

## 2. CORE SYNTAX

### 2.1 Basic Structure
```
{ctx: <context> | ref: <reference> | act: <action> | data: <payload>}
```

**Components:**
- `ctx`: Konteks komunikasi (task_exec, query, decision, etc)
- `ref`: Referensi ke state prior (prev_msg_N, doc_ID, etc)
- `act`: Tindakan/intent (clarify, retrieve, compute, etc)
- `data`: Payload berisi informasi actual

### 2.2 Symbol Substitutions

> ⚠️ **BAGIAN INI TERBANTAH OLEH DATA — JANGAN DIPAKAI TANPA PENGUKURAN ULANG.**
> Substitusi simbol Unicode di bawah diasumsikan menghemat token, tetapi
> pengukuran menunjukkan sebaliknya: Pattern B (`Δ`, `°`) menghasilkan 23 token
> untuk 36 karakter (~1,6 char/token), jauh lebih boros dari rata-rata ~4.
> Simbol langka pecah menjadi banyak token. Lihat TEMUAN #4 di
> `CRITICAL_FINDINGS.md`. Arah v0.2 memakai **codebook kata terverifikasi
> 1-token** (§5.3), bukan simbol.


#### Logical Operators
| Natural | AILang | Use Case |
|---------|--------|----------|
| and | ∧ | Conjunction |
| or | ∨ | Disjunction |
| not | ¬ | Negation |
| implies | → | Conditional |
| equivalent | ↔ | Biconditional |
| therefore | ∴ | Conclusion |

#### Comparison
| Natural | AILang | Abbreviation |
|---------|--------|--------------|
| equals | = | == |
| not equals | ≠ | != |
| greater | > | > |
| less | < | < |
| greater/equal | ≥ | >= |
| less/equal | ≤ | <= |

#### Collection
| Natural | AILang | Abbreviation |
|---------|--------|--------------|
| in | ∈ | ∈ |
| not in | ∉ | ∉ |
| subset | ⊆ | ⊆ |
| superset | ⊇ | ⊇ |
| union | ∪ | U |
| intersection | ∩ | ∩ |

#### Special Symbols
- `_`: Wildcard/any value
- `Δ`: Delta/change/difference
- `≈`: Approximately/fuzzy match
- `∞`: Unbounded/infinite
- `∅`: Empty/null
- `◆`: Priority/important
- `▬`: Skip/omit
- `⤳`: Chained/sequence

---

## 3. DATA COMPRESSION PATTERNS

### Pattern A: Intent-Based Omission
```
NATURAL:
"Can you please retrieve the user's profile information 
from the database and include their recent activity logs?"

AILANG:
{act: retrieve | data: {obj: user.profile, inc: activity_logs}}
```
**Tokens**: 20
**Characters**: 63
**Savings**: 60% tokens

### Pattern B: Coordinate Delta
```
NATURAL:
"The temperature was 25°C yesterday, and today it's 28°C"

AILANG:
{val: temp, t0: 25, Δ: +3, unit: °C}
```
**Savings**: 55% tokens

### Pattern C: Semantic Hashing
```
NATURAL:
"Has the API response time degraded significantly 
compared to the baseline established last month?"

AILANG:
{q: api.latency | cmp: baseline.month_ago | sig: true}
```
**Savings**: 70% tokens

### Pattern D: Multi-Ref Compression
```
NATURAL:
"Using the analysis from doc_ID_123, the results 
show that variables X and Y are correlated"

AILANG:
{ref: doc_123 | rel: X↔Y}
```
**Savings**: 65% tokens

### Pattern E: Conditional Chaining
```
NATURAL:
"If the score is above 80, flag it as high priority,
otherwise if it's between 50-80, mark as medium,
and anything below 50 should be ignored"

AILANG:
score >80 → flag=high
score ∈[50,80) → flag=med
score <50 → ▬
```
**Savings**: 72% tokens

---

## 4. TYPE SYSTEM

### Primitive Types
```
str    : "text" or 'text' or `literal`
num    : 42, 3.14, -100
bool   : T (true) | F (false)
null   : ∅
```

### Collection Types
```
[a,b,c]        : Array/list
{k:v, k:v}     : Object/dict
(a:T, b:F)     : Tuple/struct
```

### Special Types
```
ref{type:ID}   : Reference (e.g., ref{user:123})
fn(x,y)→z      : Function signature
∴ expr         : Assertion/conclusion
```

---

## 5. MESSAGE FORMAT (v0.2 — SESSION-SCOPED)

> **REVISI BESAR dari v0.1.** Envelope v0.1 di bawah (dipertahankan sebagai
> arsip di §5.5) berukuran **3,4x lebih besar** daripada payload yang
> dibungkusnya — 212 karakter envelope untuk 63 karakter payload. Artinya 77%
> biaya token ada di metadata, bukan di isi pesan. Memampatkan payload
> secanggih apa pun tidak akan menembus target ≥60% selama envelope tetap.
> Lihat TEMUAN #5 di `CRITICAL_FINDINGS.md`.
>
> Solusinya: pindahkan semua field konstan ke **state tingkat sesi** yang
> disepakati sekali lewat handshake, sehingga pesan hanya membawa yang
> benar-benar berubah.

### 5.1 Dua Fase

```
FASE 1 — HANDSHAKE   sekali per sesi, verbose, TIDAK dikompresi
FASE 2 — PESAN       berkali-kali, ramping, hanya delta
```

Handshake **tidak boleh** dikompresi memakai codebook yang sedang
dinegosiasikannya sendiri (ayam-telur). Dia polos dan boros — dan itu tidak
masalah, karena hanya sekali.

### 5.2 Fase 1 — Handshake

**HELLO** (pemrakarsa → lawan bicara):

```json
{
  "type": "hello",
  "proto": "ailang/0.2",
  "session": "s_7f3a",
  "from": "agent_a",
  "to": "agent_b",
  "codebook": {"id": "core", "version": 3, "hash": "sha256:ab12cd34"},
  "schema": {"slots": ["act", "obj", "mod"]},
  "model": "claude-opus-5",
  "fallback": "natural"
}
```

**HELLO_ACK** (menerima):

```json
{"type":"hello_ack","session":"s_7f3a","codebook_hash":"sha256:ab12cd34"}
```

**HELLO_NACK** (menolak — WAJIB menyebut kemampuannya sendiri):

```json
{"type":"hello_nack","session":"s_7f3a","reason":"codebook_version_mismatch",
 "have":[{"id":"core","version":2,"hash":"sha256:99ff00aa"}],
 "fallback":"natural"}
```

#### Kenapa ada `hash`, bukan cuma `version`

Nomor versi bisa sama tapi isinya sudah menyimpang — misalnya satu pihak
menambal codebook secara lokal tanpa menaikkan versi. `hash` menangkap
divergensi yang nomor versi lewatkan. **Kedua pihak wajib mencocokkan hash,
bukan hanya versi.** Ini mitigasi utama RISK-T2 (korupsi diam-diam).

#### Field handshake

| Field | Wajib | Fungsi |
|---|---|---|
| `proto` | ya | versi protokol; beda mayor = tolak |
| `session` | ya | membuat `msg_id` cukup jadi nomor urut pendek |
| `codebook.id` + `.version` + `.hash` | ya | **paling kritis** — sumber RISK-T2 |
| `schema.slots` | ya | urutan slot posisi; menghapus kebutuhan kunci `act:`/`obj:` |
| `model` | ya | properti "1 token" tervalidasi PER MODEL; model beda = kepadatan diam-diam merosot |
| `from` / `to` | ya | identitas, dipakai sekali lalu implisit |
| `fallback` | ya | perilaku saat negosiasi gagal |

#### Aturan kegagalan

1. Hash tidak cocok → **TOLAK**, jangan lanjut. Jangan pernah "coba saja dulu".
2. NACK diterima → turun ke `fallback` (bahasa natural), **jangan gagal total**.
3. Tidak ada codebook yang sama-sama dimiliki → bahasa natural sepenuhnya.
4. `proto` beda versi mayor → tolak.

### 5.3 Fase 2 — Format Pesan

Setelah handshake, pesan hanya membawa nomor urut + payload posisional:

```
7 get user log
```

- `7` — nomor urut dalam sesi (bukan UUID; sesi sudah diketahui)
- `get user log` — payload posisional; slot mengikuti `schema.slots`
  yang disepakati, jadi `get`=act, `user`=obj, `log`=mod

Membalas pesan tertentu memakai `:`

```
8:7 ok data
```

= pesan ke-8, membalas pesan ke-7.

Tiap simbol payload adalah entri codebook yang **sudah diverifikasi tepat
1 token** pada `model` yang disepakati (lihat
`claude_tools/encoding_bench.py validate-codebook`).

### 5.4 Perbandingan Biaya

| | ~token/pesan | Hemat |
|---|---|---|
| v0.1: envelope penuh + payload AILang | 69 | — |
| v0.2: envelope ramping + codebook | **7** | **~90%** |

Handshake sekitar 30 token dan **impas di pesan pertama** (penghematan
~53 token/pesan). Rincian titik impas ada di `CRITICAL_FINDINGS.md`.

> ⚠️ Semua angka di atas estimasi `char/4`, **BELUM diukur** dengan endpoint
> `count_tokens` resmi. Rasionya yang bisa dipegang, bukan digit persisnya.

### 5.5 Konsekuensi ke Log dan Translator

Pemangkasan envelope mengubah sifat log secara mendasar: entri log **tidak
lagi berdiri sendiri**. `7 get user log` tanpa konteks sesi tidak bermakna
apa pun.

Karena itu:

1. **Handshake WAJIB ditulis sebagai header sesi di log.**
2. Translator Agent harus membaca header itu sebelum bisa mendekode satu
   pesan pun di sesi tersebut.
3. Log berubah dari kumpulan entri independen menjadi **stream ber-sesi**.
4. **Retensi**: header sesi harus bertahan selama pesan-pesannya masih ada.
   Header yang kadaluarsa lebih dulu = seluruh sesi menjadi tidak terbaca.

### 5.6 ARSIP — Envelope v0.1 (JANGAN DIPAKAI)

Dipertahankan sebagai catatan sejarah. 212 karakter, ~53 token per pesan.

```json
{
  "v": "0.1",
  "sender": "ai_model_A",
  "receiver": "ai_model_B",
  "msg_id": "msg_abc123",
  "prev_id": "msg_xyz789",
  "ts": 1722451200,
  "payload": "{ctx: task_exec | ref: prev_5 | act: compute | data: {...}}",
  "encoding": "ailang_v0.1",
  "orig_tokens": 450,
  "ailang_tokens": 135,
  "efficiency": 0.70
}
```

Ke mana perginya tiap field di v0.2:

| Field v0.1 | Nasib di v0.2 |
|---|---|
| `orig_tokens`, `ailang_tokens`, `efficiency` | **dibuang dari kabel** — telemetri, tempatnya di log |
| `v`, `encoding` | pindah ke handshake (konstan) |
| `sender`, `receiver` | pindah ke handshake (konstan) |
| `ts` | dibuang — log sudah punya timestamp sendiri |
| `msg_id` | jadi nomor urut pendek (sesi sudah diketahui) |
| `prev_id` | jadi notasi `:n` |
| `payload` | tetap, tapi jadi posisional |

### 5.7 Prior Art

Pendekatan ini pada dasarnya **HPACK** (kompresi header HTTP/2): tabel
statis disepakati di muka, tabel dinamis per-koneksi, representasi
terindeks. Masalahnya identik — header berulang mendominasi payload kecil.
Sebelum merancang detail lebih jauh, baca penanganan **desinkronisasi
tabel** di HPACK; itu kegagalan yang sama dengan RISK-T2.

---

## 6. RESERVED KEYWORDS

```
act, ctx, ref, data, type, obj, val, inc, exc, 
cmp, sig, rel, flag, score, status, T, F, Δ, 
∴, →, ↔, ∈, ∉, ∪, ∩, ⊆, ⊇, ◆, ▬, ⤳
```

---

## 7. AMBIGUITY RESOLUTION

When decompressing AILang back to natural language, decompressor should:

1. **Context Stacking**: Maintain context from previous messages
2. **Type Inference**: Infer types from symbol usage
3. **Pronoun Resolution**: Map pronouns (it, this, that) to actual objects
4. **Expansion Rules**: Expand compressed structures into full sentences
5. **Validation**: Ensure reconstructed text is unambiguous

---

## 8. EXAMPLES

### Example 1: Database Query
```
INPUT (Natural):
"Get all users from the EU region who have logged in 
within the last 30 days and are currently active"

OUTPUT (AILang):
{act: query | data: {from: users, filter: region=EU∧login∈[now-30d,now]∧status=active}}

EFFICIENCY: Original 23 tokens → Compressed 18 tokens (22% savings)
```

### Example 2: Decision Logic
```
INPUT (Natural):
"If the error rate exceeds 5%, immediately roll back 
the deployment. If it's between 2-5%, send an alert. 
Otherwise, continue monitoring."

OUTPUT (AILang):
error_rate >0.05 → rollback
error_rate ∈(0.02,0.05] → alert
_ → monitor

EFFICIENCY: Original 35 tokens → Compressed 12 tokens (66% savings)
```

### Example 3: Data Transformation
```
INPUT (Natural):
"Transform the user dataset by filtering only active users, 
mapping their IDs to profile objects, and grouping by region"

OUTPUT (AILang):
{act: transform | data: {src: users | filter: active=T | map: id→profile | group: region}}

EFFICIENCY: Original 24 tokens → Compressed 15 tokens (38% savings)
```

---

## 9. LIMITATIONS & EDGE CASES

| Edge Case | Handling | Notes |
|-----------|----------|-------|
| Ambiguous pronouns | Use explicit refs | Decompressor adds object names |
| Nested conditions | Use ⤳ chaining | Max depth: 5 levels |
| Free-form text | Quotes only | Limited compression benefit |
| Domain-specific jargon | Domain mappings | Extensible via plugins |
| Floating point precision | num+precision tag | E.g., `3.14[2]` = 2 decimals |

---

## 10. NEXT STEPS (PHASE 1 CONTINUATION)

- [ ] Finalize symbol definitions with user
- [ ] Add 20+ more compression patterns
- [ ] Create formal grammar (BNF/EBNF)
- [ ] Build parser/tokenizer
- [ ] Define error handling & recovery
- [ ] Create comprehensive examples (50+ scenarios)
- [ ] Get user approval for v0.1 final

---

**FEEDBACK NEEDED:**
1. Are symbol choices intuitive?
2. Are we missing critical patterns?
3. Should we add namespace support for domain-specific keywords?
4. Context window size assumptions? (assume Claude 100K+)
5. Any security/safety concerns with this approach?
