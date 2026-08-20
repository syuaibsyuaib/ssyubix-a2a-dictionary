# Ssyubix A2A Dictionary (AI-to-AI Communication Protocol)

**Project**: Token-Efficient AI Communication Framework  
**Status**: Project Formation  
**Created**: 2026-07-31

## Overview
Ssyubix A2A Dictionary adalah sistem komunikasi teroptimasi token antara AI agents. Project ini bertujuan untuk:
1. Mengembangkan "bahasa AI" yang highly efficient dalam penggunaan tokens
2. Membuat bidirectional translator (AI Language ↔ Human Language)
3. Mendokumentasikan semantic compression patterns
4. Mengimplementasikan proof-of-concept system

## Why This Matters
- **Token efficiency**: Mengurangi overhead komunikasi antar AI hingga 60-70%
- **Transparency**: AI translator memastikan humans dapat audit/understand any A2A communication
- **Standardization**: Membuat standard protocol untuk interoperability antar AI systems

## 🔥 Critical Findings (2026-07-31)

### 1. Whitespace DOES Consume Tokens
- **Discovery**: Every space, newline, tab in messages = counted tokens
- **Impact**: Minified JSON saves ~15% tokens vs pretty-printed
- **Implication**: AILang MUST be ultra-minified for max efficiency

**Token Comparison Example:**
```
Pretty JSON:     {"context": "task"}           → ~8 tokens
Minified JSON:   {"context":"task"}            → ~7 tokens
AILang minified: {ctx:task}                    → ~4 tokens
                                       Savings: 50% vs pretty, 43% vs minified
```

**Design Decision**: AILang messages use ZERO whitespace (except string literals)

### 2. Extended Thinking is Token-Expensive
- **Discovery**: Reasoning tokens cost same as output tokens ($15/M)
- **Impact**: 10K tokens reasoning = expensive overhead
- **Implication**: AILang optimized for API calls, NOT reasoning tasks

**Cost Analysis:**
```
Use Case A (API call):
  Natural lang: 200 tokens → AILang: 80 tokens (60% saving) ✅
  
Use Case B (with reasoning):
  Natural lang: 200 tokens → AILang: 80 tokens
  PLUS: Extended thinking 5000 tokens
  NET RESULT: 96% MORE EXPENSIVE ❌
```

**Design Decision**: AILang targets API-call efficiency, defer reasoning optimization

### 3. Arsitektur: Opaque-by-Design (REVISI 2026-08-20)

Wire format A2A dioptimasi **murni untuk efisiensi token** dan **tidak wajib
dapat dibaca manusia**. Log menyimpan wire format **verbatim**. Keterbacaan
dipindahkan sepenuhnya ke **Translator Agent** yang membaca log sebagai MITM.

- **Transmission**: wire format token-optimal (tidak wajib terbaca manusia)
- **Log**: verbatim, persis seperti dikirim — *tanpa* lapis konversi
- **Translator Agent**: natural language, **on-demand** saja

**Example Flow:**
```
A2A Transmission: {ctx:task|ref:prev_5|act:compute|data:{x:1}}
                  |
                  +--> Log (verbatim, apa adanya)
                            |
                            +--> Translator Agent  [on-demand, di samping jalur]
                                 "Execute task based on previous message with x=1"
```

**Perubahan**: lapis "Storage: Formatted JSON" **dihapus** — log tidak lagi
menyimpan hasil konversi. Satu lapis konversi hilang dari desain.

**Asumsi kerja** (belum diverifikasi angka, lihat `CRITICAL_FINDINGS.md`):
- **ASM-1**: translasi **on-demand**, bukan tiap pesan
- **ASM-2**: translator **di samping jalur**, bukan relay di jalur kirim

### 4. ⚠️ Biaya Token ≠ Jumlah Karakter (temuan baru)

Data ukur sendiri di `data/token_measurements.csv`:

| Pattern | Karakter | Token |
|---|---|---|
| A (tanpa simbol Unicode) | 63 | **20** |
| B (pakai `Δ`, `°`) | 36 | **23** |

Pattern B **43% lebih pendek** secara karakter tapi **lebih mahal** tokennya.
Memampatkan ke simbol eksotis justru **menaikkan** biaya. Target optimasi yang
benar adalah **token berfrekuensi tinggi**, bukan string terpendek.

---

## Project Goals
- [ ] Define AI language specification (AILang v0.1)
- [ ] Build compression dictionary dengan semantic rules
- [ ] Implement bidirectional translator
- [ ] Create unit tests & performance benchmarks
- [ ] Documentation & examples
- [ ] Proof-of-concept with Claude API

## Architecture
```
ssyubix-a2a-dictionary/
├── README.md
├── TASKS.md
├── src/
│   ├── ailang_spec.py          # AI Language specification
│   ├── compressor.py           # Text → AILang compression
│   ├── decompressor.py         # AILang → Human readable
│   ├── translator.py           # Main translator API
│   └── __init__.py
├── claude_tools/
│   ├── token_counter.py        # Count tokens
│   ├── semantic_analyzer.py    # Analyze semantic density
│   └── benchmark.py            # Performance testing
├── tests/
│   ├── test_compression.py
│   ├── test_decompression.py
│   └── test_integration.py
├── data/
│   ├── sample_messages.json
│   └── compression_rules.json
└── docs/
    ├── ailang_spec.md
    ├── compression_rules.md
    └── api_reference.md
```

## Key Phases
1. **Phase 1 - Definition** (Week 1): Spec out AILang, define compression rules
2. **Phase 2 - Implementation** (Week 2-3): Code translator, tests
3. **Phase 3 - Optimization** (Week 3-4): Performance tuning, benchmarking
4. **Phase 4 - Documentation** (Week 4): Complete docs, examples, deployment guide

## Tech Stack
- Python 3.10+
- Anthropic Claude API
- JSON for configuration
- Pytest for testing

## Next Steps

### Status Checkpoint (per 2026-08-20)
1. **Whitespace Strategy** — ✅ DISETUJUI (ultra-minified)
2. **Use Case Focus** — ⏳ **MASIH TERBUKA**, satu-satunya checkpoint pemblokir
3. **Hybrid Approach** — ✅ DISETUJUI DENGAN REVISI (2 lapis, bukan 3)

### Prioritas Berikutnya
1. Lengkapi kolom `natural_tokens` di `data/token_measurements.csv`
   (8 baris; saat ini kosong semua → belum ada efisiensi yang terhitung)
2. Verifikasi dugaan Pattern B justru MEMPERBESAR pesan
3. Uji arah **codebook**: konsep → satu token berfrekuensi tinggi
4. Jawab checkpoint #2 + OPEN-Q1 (translator deterministik atau agen LLM?)

### Documentation Updated
- [x] README.md - Arsitektur opaque-by-design + temuan token vs karakter
- [x] CRITICAL_FINDINGS.md - Keputusan desain, ASM-1/ASM-2, RISK-T1, OPEN-Q1
- [x] TASKS.md - Blocker #1 resolved, asumsi baru, status usang dikoreksi
- [ ] AILANG_DRAFT.md - Klaim "Savings" §3 perlu diukur ulang
- [ ] PROJECT_CHARTER.md - Janji >99% accuracy perlu ditinjau (lihat OPEN-Q1)
