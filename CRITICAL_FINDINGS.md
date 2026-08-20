# Critical Findings Summary - Ssyubix A2A Dictionary

**Date**: 2026-07-31 (dibuat) / 2026-08-20 (revisi arsitektur)  
**Status**: CHECKPOINT #1 & #3 DIPUTUSKAN — #2 MASIH TERBUKA  
**Keputusan arsitektur aktif**: opaque-by-design · pangkas envelope + handshake wajib  
**Risiko terbuka**: RISK-T1 (biaya translator) · RISK-T2 (korupsi diam-diam)  
**Updated Files**: README.md, TASKS.md, AILANG_DRAFT.md

---

## 🔒 KEPUTUSAN DESAIN: A2A OPAQUE-BY-DESIGN (2026-08-20)

**Sumber**: klarifikasi langsung dari project owner  
**Status**: DITETAPKAN — menggantikan sebagian "Recommended Strategy" di bawah

### Inti Keputusan

Komunikasi antar agen dioptimasi **murni untuk efisiensi token**. Wire format
**tidak punya kewajiban dapat dibaca manusia**. Semua kebutuhan keterbacaan
dipindahkan ke **Translator Agent** yang berperan sebagai MITM pembaca log.

### Arsitektur Hasil Revisi (2 lapis + translasi on-demand)

| Lapis | Isi | Wajib terbaca manusia? |
|---|---|---|
| L1 — Transmission | wire format, token-optimal | **tidak** |
| L2 — Log | **verbatim, persis seperti dikirim** | **tidak** |
| Translator Agent | natural language | ya, tapi **on-demand** |

**Perubahan dari strategi lama**: "Layer 2: Storage/Audit (Formatted JSON)"
di bagian bawah dokumen ini **DIHAPUS**. Log tidak lagi menyimpan hasil
konversi apa pun — log menyimpan wire format apa adanya. Satu lapis konversi
hilang dari desain, dan biaya konversi saat penulisan log jadi nol.

### Asumsi Kerja (dicatat atas instruksi owner, belum diverifikasi angka)

- **ASM-1 — Frekuensi translasi: ON-DEMAND.**  
  Translasi dijalankan hanya saat dibutuhkan (audit, investigasi insiden,
  sampling), **bukan** untuk setiap pesan. Lihat RISK-T1 — asumsi ini yang
  menentukan seluruh arsitektur untung atau rugi.

- **ASM-2 — Posisi translator: DI SAMPING JALUR (out-of-band).**  
  Translator membaca log secara asinkron dan **tidak merelay** pesan A2A.
  Konsekuensi: biaya token dan latensi translator = **nol di jalur utama**.
  Istilah "MITM" di sini berarti pengamat yang punya akses penuh ke lalu
  lintas, bukan perantara yang menyisip di jalur kirim.

Kedua asumsi ini dipakai sebagai dasar kerja sampai owner menyatakan lain.

---

## 🔥 TEMUAN #4: BIAYA TOKEN ≠ JUMLAH KARAKTER ⚠️ (2026-08-20)

> Temuan #1–#3 ada di bagian **Major Discoveries** lebih bawah. Temuan #4 ditaruh di atas karena langsung mengoreksi asumsi Temuan #1.

Konsekuensi langsung dari keputusan di atas: begitu keterbacaan manusia tidak
lagi jadi batasan, godaan alaminya adalah memampatkan pesan ke simbol-simbol
eksotis. **Data ukur di `data/token_measurements.csv` menunjukkan arah itu
justru menaikkan biaya.**

| Pattern | Karakter | Token | char/token |
|---|---|---|---|
| A (tanpa simbol Unicode) | 63 | **20** | 3,2 |
| B (pakai `Δ`, `°`) | 36 | **23** | 1,6 |

Pattern B **43% lebih pendek** secara karakter tetapi **lebih mahal** tokennya.
Rata-rata teks Inggris biasa ~4 char/token; Pattern B hanya 1,6.

**Sebab**: biaya ditentukan oleh seberapa umum sebuah token di vocabulary
model, bukan oleh panjang string. Simbol Unicode langka pecah jadi banyak token.

**Implikasi desain**: target optimasi yang benar adalah **rangkaian token
berfrekuensi tinggi**, bukan string terpendek. Arah yang paling diuntungkan
oleh keputusan opaque-by-design adalah **codebook**: tiap konsep dipetakan ke
**satu token umum** yang sudah ada di vocabulary model. Pemetaan boleh tampak
arbitrer bagi manusia — Translator Agent yang memegang kamusnya.

**Catatan**: sebagian klaim "Savings" di `AILANG_DRAFT.md` §3 belum terukur.
Estimasi kasar Pattern B (natural ~13-14 token vs AILang terukur 23 token)
menunjukkan pola itu kemungkinan **memperbesar** pesan, bukan memampatkan,
padahal draft mengklaim hemat 55%. Wajib diverifikasi sebelum spec difinalkan.

---

## RISK-T1: BIAYA TRANSLATOR BISA MEMBATALKAN SELURUH PENGHEMATAN

Translator Agent ikut mengonsumsi token: input (isi log) + output (natural
language). Kalau **setiap** pesan diterjemahkan, biaya sistem total bisa
melampaui biaya mengirim natural language sejak awal.

Bentuk kesalahannya identik dengan Temuan #2 (extended thinking): hemat di satu
titik, rugi secara global.

| Frekuensi translasi | Dampak |
|---|---|
| On-demand (ASM-1) | penghematan A2A utuh ✅ |
| ~100% pesan | kemungkinan **net negatif** ❌ |

**Mitigasi**: ASM-1. **Konsekuensi**: kalau ASM-1 gugur, seluruh perhitungan
efisiensi project ini harus dihitung ulang dari nol.

---

## OPEN-Q1: TRANSLATOR DETERMINISTIK ATAU AGEN LLM?

Belum diputuskan, dan ini punya konsekuensi ke janji akurasi di charter.

| Opsi | Akurasi rekonstruksi | Catatan |
|---|---|---|
| Decompressor deterministik (kamus) | dijamin, dapat diaudit | encoding harus terstruktur formal |
| Agen LLM | probabilistik, **tak dijamin** | fleksibel, tapi bisa berhalusinasi di jejak audit |

`PROJECT_CHARTER.md` §7 menjanjikan rekonstruksi **>99% accuracy**. Agen LLM
tidak bisa menjamin angka itu secara deterministik. Kalau translator berupa
agen LLM, janji di charter perlu direvisi atau perlu lapisan verifikasi.

---

## 🔥 TEMUAN #5: ENVELOPE MENDOMINASI PAYLOAD (2026-08-20)

Envelope di `AILANG_DRAFT.md` §5 berukuran **3,4x lebih besar** dari payload
yang dibungkusnya. Selama ini seluruh usaha optimasi diarahkan ke payload --
bagian yang justru paling kecil.

```
envelope §5 (v, sender, receiver, msg_id, prev_id,
             ts, encoding, orig_tokens, ailang_tokens,
             efficiency)                          212 char  ~53 token
payload AILang                                     63 char  ~16 token
payload codebook                                   12 char   ~3 token
```

Dampaknya ke total biaya per pesan:

| Skenario | ~token/pesan | Hemat |
|---|---|---|
| AILang v0.1 + envelope penuh | 69 | — |
| Codebook + envelope penuh | 56 | **19%** |
| Codebook + envelope dipangkas | 7 | **90%** |

**Ini hukum Amdahl.** Memampatkan payload 81% (16 -> 3 token) hanya
menghasilkan 19% secara total, karena 77% biaya ada di envelope yang tidak
disentuh. Target >=60% di charter TIDAK MUNGKIN tercapai tanpa memangkas
envelope, seberapa pun bagus encoding payload-nya.

> Angka di atas estimasi char/4, BELUM diukur `count_tokens` resmi.
> Yang penting rasionya (3,4x), bukan digit persisnya.

Field yang bisa keluar dari tiap pesan:
- `orig_tokens`, `ailang_tokens`, `efficiency` -- telemetri, tempatnya di log
- `encoding`, `v` -- konstan, sepakati sekali di handshake
- `sender`, `receiver` -- implisit dari channel/sesi
- Sisakan `msg_id` + `prev_id` ringkas + payload

---

## 🔒 KEPUTUSAN DESAIN: PANGKAS ENVELOPE + HANDSHAKE WAJIB (2026-08-20)

**Sumber**: usulan Claude (pangkas envelope), disempurnakan owner (handshake)
**Status**: DITETAPKAN

Envelope dipangkas dengan memindahkan field konstan ke **state tingkat sesi**,
yang disepakati lewat **handshake** sebelum pesan pertama.

### Handshake bukan biaya tambahan -- dia PRASYARAT KEAMANAN

Lihat RISK-T2. Tanpa handshake, pemangkasan envelope memindahkan risiko dari
"boros token" ke "salah tafsir tanpa ketahuan" -- pertukaran yang buruk.

### Titik impas

`N > H / penghematan_per_pesan`, dengan penghematan ~53 token/pesan:

| Isi handshake | H (token) | Impas di N pesan |
|---|---|---|
| Referensi codebook saja (id + versi + skema) | 30 | **1** |
| + negosiasi kemampuan singkat | 80 | **2** |
| Kirim codebook 256 entri inline | 700 | 13 |
| Kirim codebook 4096 entri inline | 11.000 | 208 |

**ATURAN: jangan kirim codebook-nya, kirim rujukannya.** Codebook di-share
di luar jalur (versioned, di system prompt), handshake cuma menyebut
`codebook: v3`. Selisihnya 30 token versus 11.000.

Bonus: codebook yang tinggal di system prompt kena **prompt caching** --
konten stabil di posisi paling depan, dibayar sekali lalu jadi cache read
untuk semua panggilan berikutnya.

### Isi handshake (semua konstan sepanjang sesi)

- `codebook_id` + versi -- PALING KRITIS, sumber RISK-T2
- Skema posisi (slot 1 = action, slot 2 = object, dst.)
- Versi protokol + id encoding
- Identitas kedua agen
- `session_id` -- supaya `msg_id` cukup jadi nomor urut pendek
- **Model/tokenizer target** -- properti "1 token" tervalidasi PER MODEL;
  kalau lawan bicara pakai model lain, arti tetap benar tapi kepadatan
  diam-diam merosot

### Aturan turunan

1. **Handshake tidak boleh dikompresi oleh codebook yang dinegosiasikannya**
   (ayam-telur). Handshake polos dan verbose. Hanya sekali, jadi tidak apa-apa.
2. **Wajib ada fallback**: kalau tidak ada codebook yang sama-sama dimiliki,
   turun ke bahasa natural -- jangan gagal. Degradasi bertahap.
3. **Codebook transparan, bukan arbitrer.** Keduanya berbiaya SAMA (1 token
   per konsep), jadi arbitrer tidak memberi keuntungan kepadatan sedikit pun
   -- hanya memperbesar ruang alamat yang sudah berlebih. Tapi arbitrer
   menambah dua biaya nyata: codebook harus masuk context penerima DAN
   translator, plus risiko akurasi karena model harus melakukan indireksi.
   Keuntungan nol, kerugian nyata -> transparan menang.

### Prior art

Ini pada dasarnya **HPACK** (kompresi header HTTP/2): tabel statis disepakati
di muka + tabel dinamis per-koneksi + representasi terindeks. Masalahnya
identik -- header berulang mendominasi payload kecil -- dan solusinya sudah
teruji di produksi. Baca terutama bagian penanganan desinkronisasi tabel
sebelum merancang dari nol.

---

## RISK-T2: KORUPSI DIAM-DIAM AKIBAT CODEBOOK TIDAK COCOK ⚠️

**Severity: TINGGI.** Ini risiko terparah dalam desain, karena tidak terlihat.

Begitu envelope dipangkas, pesan tidak lagi membawa keterangan codebook mana
yang dipakai. Kalau Agent A memakai codebook v3 dan Agent B masih v2:

```
Agent A kirim:  get user log      (codebook v3)
Agent B dekode: get user log      (codebook v2) -> ARTI BERBEDA
```

Pesan **terdekode dengan sukses**. Tidak ada error, tidak ada exception,
tidak ada yang gagal. Hanya agen yang mengerjakan hal salah dengan penuh
keyakinan. Ini lebih berbahaya daripada crash -- crash setidaknya terlihat.

**Mitigasi**: handshake WAJIB memverifikasi `codebook_id` + versi sebelum
pesan pertama. Ketidakcocokan ditolak di muka, bukan ditemukan belakangan.

---

## KONSEKUENSI: FORMAT LOG BERUBAH (dampak ke ASM-1 / ASM-2)

Pemangkasan envelope mengubah sifat log secara mendasar. Entri log **tidak
lagi berdiri sendiri**: `get user log` tanpa konteks sesi tidak bermakna
apa pun.

Akibatnya:

1. **Handshake wajib jadi header di log.** Translator harus membacanya
   sebelum bisa mendekode satu pesan pun di sesi itu.
2. **Log berubah dari kumpulan entri independen jadi stream ber-sesi.**
3. **Untuk ASM-1 (translasi on-demand)**: translator tidak bisa disuruh
   menerjemahkan satu pesan acak -- dia butuh header sesinya juga.
4. **Retensi log**: header sesi HARUS tersimpan selama pesan-pesannya masih
   ada. Header yang kadaluarsa duluan = seluruh sesi jadi tidak terbaca.

---

## 🔥 Major Discoveries

### 1. WHITESPACE CONSUMES TOKENS ⚠️
```
Discovery:  Every space, newline, tab = counts as tokens
Impact:     Minified JSON saves 15% vs pretty-printed
            AILang minified saves 50% more vs minified JSON

Recommendation: Use ULTRA-MINIFIED AILang (zero whitespace except in strings)

Example Token Costs:
  {"context": "task"}              → 8 tokens (pretty)
  {"context":"task"}               → 7 tokens (minified)
  {ctx:task}                       → 4 tokens (AILang)
                                     50% savings vs minified!
```

**DECISION NEEDED**: Approve ultra-minified approach? (affects readability)

---

### 2. REASONING TOKENS ARE EXPENSIVE 💰
```
Discovery:  Extended thinking costs same as output tokens ($15/M)
Impact:     10K tokens reasoning = $0.15 cost
            Negates AILang compression savings for reasoning tasks

Cost Example:
  API call: "get users" 200 tokens → AILang 80 tokens (60% saving) ✅
  
  Reasoning: "analyze data" 200 tokens → AILang 80 tokens
             + extended thinking 5000 tokens
             = 96% MORE EXPENSIVE ❌
```

**DECISION NEEDED**: Should AILang focus on API calls only? (defer reasoning to v0.2)

---

### 3. USE CASE CLARITY REQUIRED 🎯
```
Three Options:

A) API-Call Focus (recommended)
   ├─ Queries, data retrieval, task dispatch
   ├─ 60-70% efficiency gains ✅
   └─ Perfect for AILang ✅

B) Reasoning Focus
   ├─ Complex decision-making, analysis
   ├─ Limited efficiency (reasoning dominates)
   └─ Not ideal for AILang ❌

C) Mixed Approach
   ├─ Both API calls and some reasoning
   ├─ Requires hybrid strategy
   └─ More complex but possible ⚠️
```

**DECISION NEEDED**: Which use case is PRIMARY?

---

## 📋 Updated Strategy

### ~~Recommended: Hybrid Approach (3-Layer)~~ — DIREVISI jadi 2 lapis (lihat KEPUTUSAN DESAIN di atas)

**Layer 1: Transmission (Ultra-Minified)**
```
{ctx:task|ref:prev_5|act:compute|data:{x:1,y:2}}
• Zero whitespace
• Max efficiency (60-70% savings)
• Only for A2A communication
```

**Layer 2: Storage/Audit (Formatted JSON)** — ~~DIHAPUS 2026-08-20~~ (log kini verbatim, lihat KEPUTUSAN DESAIN di atas)
```json
{
  "context": "task",
  "reference": "previous_5",
  "action": "compute",
  "data": { "x": 1, "y": 2 }
}
// Human-readable for audit trail
// Used for logging & debugging
```

**Layer 3: Display (Natural Language)**
```
Execute this task based on previous message (5):
compute the result with x=1 and y=2
// Translator-generated for humans
// Fully transparent & auditable
```

**Benefits:**
- ✅ Max efficiency in transmission
- ✅ Max readability for audit
- ✅ Full transparency
- ✅ Fully reversible (no information loss)

---

## ✋ Critical Checkpoints

**STATUS PER 2026-08-20** — lihat "KEPUTUSAN DESAIN" di bagian atas dokumen.

- [x] **Whitespace Strategy**: ultra-minified — **DISETUJUI**
  - Dasar: wire format tidak wajib terbaca manusia
  - ⚠️ Catatan penting: minifikasi ≠ optimal token. Lihat Temuan #4 —
    memperpendek string tidak otomatis memurahkan token.

- [ ] **Use Case Focus**: API-call efficiency saja? — **MASIH TERBUKA**
  - Belum diputuskan owner. Satu-satunya checkpoint yang masih memblokir.

- [x] **Hybrid Approach**: — **DISETUJUI DENGAN REVISI**
  - Bukan 3 lapis lagi, tapi **2 lapis + translasi on-demand**
  - Layer 2 lama (JSON ter-format untuk audit) DIHAPUS; log = verbatim

### Asumsi yang menunggu konfirmasi (dipakai sebagai dasar kerja)
- [ ] **ASM-1**: translasi on-demand, bukan tiap pesan → lihat RISK-T1
- [ ] **ASM-2**: translator di samping jalur, bukan relay di jalur
- [ ] **OPEN-Q1**: translator deterministik atau agen LLM?

**Boleh jalan**: Phase 1 untuk hal yang tidak bergantung checkpoint #2
(pengukuran token, benchmark, codebook eksperimental).

**Belum boleh final**: spec AILang v0.1, selama #2 dan OPEN-Q1 belum dijawab.

---

## 📝 Files Updated

| File | Section | Change |
|------|---------|--------|
| README.md | New | Added "Critical Findings" section |
| README.md | Next Steps | Added user review checkpoints |
| TASKS.md | Blockers | Updated with whitespace/reasoning findings |
| TASKS.md | Blockers | Clarified use-case options |
| This file | (new) | Findings summary for quick reference |

---

## 🚀 Next Actions

### Immediate (User Side):
1. Review findings above
2. Answer 3 checkpoints
3. Confirm or request changes

### Immediate (Claude Side - If Approved):
1. Update AILANG_DRAFT.md with minification rules
2. Update PROJECT_CHARTER.md with use-case clarification
3. Refine Phase 1 specification
4. Ready for implementation start

---

## 📚 Reference Documents
- `README.md` - Project overview + findings
- `TASKS.md` - Blockers + critical questions
- `PROJECT_CHARTER.md` - Formal project agreement
- `AILANG_DRAFT.md` - Language specification (needs update)

---

**STATUS**: Ready for user confirmation  
**LOCATION**: D:\MCP\ssyubix-a2a-dictionary\  
**NEXT SYNC**: Awaiting user feedback on checkpoints
