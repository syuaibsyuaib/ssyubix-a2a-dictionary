# Project Tasks - Ssyubix A2A Dictionary

**Last Updated**: 2026-08-20  
**Active Phases**: Phase 1 (Definition) — arsitektur direvisi ke opaque-by-design

## 🎯 Phase 1: Definition & Specification (IN PROGRESS)

### Critical Path
- [~] **[P0]** Penyamaan persepsi dengan user
  - [x] Arah arsitektur: A2A **opaque-by-design** (wire format tidak wajib
        terbaca manusia; log verbatim; Translator Agent sebagai MITM pembaca)
  - [x] Checkpoint #1 (ultra-minified) — DISETUJUI
  - [x] Checkpoint #3 (hybrid) — DISETUJUI DENGAN REVISI: 2 lapis, bukan 3
  - [ ] Checkpoint #2 (fokus API-call vs reasoning) — **MASIH TERBUKA**
  - [ ] Confirm project scope / success metrics / timeline
  - Status: SEBAGIAN DIKONFIRMASI (detail: CRITICAL_FINDINGS.md)

- [ ] **[P0]** Pangkas envelope + spesifikasi handshake  ← PRIORITAS TERTINGGI
  - Envelope §5 = 3,4x payload; tanpa dipangkas, target >=60% MUSTAHIL
    (TEMUAN #5, hukum Amdahl)
  - [ ] Tetapkan field mana yang keluar dari tiap pesan (telemetri -> log,
        konstanta -> handshake)
  - [ ] Spesifikasi handshake: codebook_id+versi, skema posisi, session_id,
        model/tokenizer target
  - [ ] Aturan fallback bila tidak ada codebook yang sama-sama dimiliki
  - [ ] Verifikasi codebook_id di muka (mitigasi RISK-T2)
  - [ ] Pelajari HPACK (HTTP/2) — prior art, terutama desinkronisasi tabel
  - Status: TODO — tidak butuh riset, murni keputusan desain

- [ ] **[P0]** Format log ber-sesi (konsekuensi pangkas envelope)
  - Entri log tidak lagi berdiri sendiri; handshake jadi header sesi
  - [ ] Translator harus baca header sebelum dekode pesan mana pun
  - [ ] Retensi: header WAJIB hidup selama pesannya masih ada
  - Status: TODO

- [ ] **[P0]** Bangun codebook transparan posisi-tetap
  - [ ] Jalankan `encoding_bench.py validate-codebook` (butuh kredensial)
  - [ ] Kurasi entri yang TEPAT 1 token pada model target
  - [ ] Beri versi; codebook terikat versi tokenizer
  - Status: BLOCKED — butuh ANTHROPIC_API_KEY

- [ ] **[P0]** AILang Specification v0.1
  - Define core syntax & semantics
  - ~~Document symbol system (→, ↔, ∴, etc)~~ — **DIBATALKAN**: simbol Unicode
    menaikkan biaya token (TEMUAN #4). §2.2 draft perlu DIBUANG, bukan direvisi
  - JSON/struct format examples
  - Status: TODO

- [ ] **[P1]** Compression Rules Dictionary
  - Identify 50+ common patterns in AI communication
  - Map to compression rules
  - Measure theoretical token savings
  - Status: TODO

- [ ] **[P1]** Design Bidirectional Translator Architecture
  - Compressor logic flow
  - Decompressor logic flow
  - Ambiguity resolution strategy
  - Status: TODO

### Research & Planning
- [ ] Literature review on existing AI communication protocols
- [~] Benchmark current Claude → Claude communication efficiency
  - `data/token_measurements.csv` dibuat; 5/8 baris sisi compressed terukur
  - **BLOKER**: kolom `natural_tokens` masih kosong di SEMUA baris, jadi
    belum ada satu pun `efficiency_pct` yang benar-benar terhitung
- [ ] Document edge cases & failure modes
- [ ] Identify technical constraints (context window, model limitations)

---

## 🛠️ Phase 2: Implementation (NOT STARTED)

### Core Components
- [ ] **[P0]** Implement AILang Specification
  - Parser
  - Validator
  - Error handling
  - Status: TODO

- [ ] **[P0]** Build Compressor Engine
  - Pattern matching
  - Symbol substitution
  - Semantic hashing
  - Status: TODO

- [ ] **[P0]** Build Decompressor Engine
  - AILang → Human text reconstruction
  - Ambiguity resolution
  - Readability optimization
  - Status: TODO

- [ ] **[P1]** Main Translator API
  - compress(text) → ailang_output
  - decompress(ailang) → human_text
  - metrics() → efficiency stats
  - Status: TODO

### Quality Assurance
- [ ] Unit tests for compressor (95%+ coverage)
- [ ] Unit tests for decompressor (95%+ coverage)
- [ ] Integration tests (10+ scenarios)
- [ ] Fuzzing & edge case testing
- [ ] Performance tests

---

## 📊 Phase 3: Optimization & Benchmarking (NOT STARTED)

- [ ] Token usage comparison (original vs AILang)
- [ ] Latency measurements
- [ ] Compression ratio analysis
- [ ] Accuracy metrics (reconstruction fidelity)
- [ ] Performance optimization (>70% efficiency target)

---

## 📚 Phase 4: Documentation (NOT STARTED)

- [ ] Complete API reference
- [ ] Usage examples (10+ scenarios)
- [ ] AILang language tutorial
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] FAQ

---

## 🔧 Infrastructure & Support

- [x] Setup project folder structure
- [x] Create TASKS.md
- [ ] Create abstract.md (when needed)
- [x] Setup claude_tools/ utilities
  - `claude_tools/token_counter.py` (wrapper endpoint resmi count_tokens)
  - `tests/test_token_counter.py` — 9 test, semua lulus (verified 2026-08-20)
- [ ] Configure pytest & testing framework
  - ⚠️ **Divergensi**: test yang ada pakai `unittest`, bukan `pytest`,
    padahal README §Tech Stack, Charter D4, Charter App.B, dan
    PROJECT_STRUCTURE.txt (`conftest.py`) semua menyebut pytest.
    Perlu keputusan: migrasi test ke pytest, ATAU turunkan dokumen ke unittest.
- [ ] Tambah `requirements.txt` — `anthropic` sudah jadi dependency riil
- [ ] Tambah `.gitignore` — `__pycache__/*.pyc` saat ini ikut ter-commit
- [ ] Setup CI/CD (if needed)

---

## ❓ Blockers & Questions (RESOLVED WHEN CONFIRMED)

### Critical Findings (2026-07-31)
1. ~~**Whitespace Consumption**~~ — **RESOLVED 2026-08-20**: ultra-minified
   disetujui (wire format tidak wajib terbaca manusia).
   - ⚠️ **KOREKSI penting atas asumsi lama**: klaim "drops 50% more tokens"
     tidak berlaku umum. Data ukur sendiri membantahnya untuk simbol Unicode:
     Pattern A = 63 karakter/**20 token**, Pattern B = 36 karakter/**23 token**.
     Pattern B 43% lebih pendek tapi LEBIH MAHAL. Memperpendek string tidak
     otomatis memurahkan token — lihat Temuan #4 di CRITICAL_FINDINGS.md.

2. **Extended Thinking Cost**: Reasoning tokens expensive ($15/M, same as output)
   - Finding: Reasoning tasks negate AILang savings
   - Question: Should AILang focus on API-call efficiency only?
   - Implication: Defer reasoning optimization to v0.2

3. **Use Case Clarification**: What's the PRIMARY use case?  ← **MASIH TERBUKA**
   - Option A: Quick API calls (queries, retrieval) → AILang PERFECT ✅
   - Option B: Complex reasoning (decision-making) → AILang LIMITED ❌
   - Option C: Mixed (both) → Need hybrid strategy ⚠️

### Asumsi Arsitektur Baru (2026-08-20, menunggu konfirmasi)
- **ASM-1** — Frekuensi translasi **on-demand**, bukan tiap pesan.
  - RISK-T1: kalau ~100% pesan diterjemahkan, biaya Translator Agent
    (input log + output natural language) bisa membuat sistem **net negatif**.
    Pola kesalahannya sama dengan temuan extended thinking.
- **ASM-2** — Translator **di samping jalur** (baca log asinkron), bukan relay.
  - Konsekuensi: biaya & latensi translator = nol di jalur utama A2A.
- **OPEN-Q1** — Translator deterministik (kamus) atau agen LLM?
  - Charter §7 menjanjikan rekonstruksi >99%. Agen LLM tidak bisa menjamin
    angka itu secara deterministik → charter perlu revisi, atau perlu
    lapisan verifikasi.

### Arah Desain Baru yang Perlu Diuji
- [ ] **Codebook**: petakan tiap konsep ke **satu token berfrekuensi tinggi**
      di vocabulary model (bukan simbol Unicode, bukan singkatan).
      Ini arah yang paling diuntungkan oleh keputusan opaque-by-design.
- [ ] Ukur ulang seluruh Pattern A-E dengan sisi natural ikut terukur
- [ ] Verifikasi dugaan Pattern B justru MEMPERBESAR pesan (~13-14 → 23 token)

### Original Blockers
1. What is the target token efficiency improvement? (updated: 60-70% for API calls)
2. Is production deployment required or proof-of-concept sufficient?
3. Should AILang support ALL types of communication or **API calls specifically**?
4. Timeline constraints? (assumption: flexible)
5. Integration with existing systems? (current: Claude API only)

---

## 📈 Success Criteria

- ✅ AILang specification documented & validated
- ✅ Bidirectional translator working (>90% reconstruction accuracy)
- ✅ >60% token efficiency improvement demonstrated
- ✅ Comprehensive test suite (>90% code coverage)
- ✅ Production-ready documentation
- ✅ Public repository with examples

---

## 📌 Notes
- All decisions pending user confirmation on project scope
- This is a **formal project** with version control and proper structure
- Using claude_tools/ folder for efficiency & reusability
- Weekly reviews recommended
