# Panduan Pencatatan Pengukuran Token (Manual via claude-tokenizer.vercel.app)

**Lokasi file kerja**: `data/token_measurements.csv`
**Update terakhir**: 2026-07-31

## ⚠️ Batasan Penting (WAJIB DIBACA SEBELUM ISI DATA)

1. **Tokenizer situs = Claude Sonnet 4 / Opus 4 family**, BUKAN Sonnet 5.
   Model target project ini kemungkinan pakai model lebih baru. Berdasarkan
   dokumentasi resmi Anthropic: model Claude 4.7 ke atas menghasilkan
   kurang lebih 30% LEBIH BANYAK token untuk teks yang sama dibanding
   tokenizer lama. Jadi angka di file ini adalah PERKIRAAN BAWAH
   (lower-bound), bukan angka final untuk produksi.

2. Situs `claude-tokenizer.vercel.app` adalah tool pihak ketiga, tidak
   berafiliasi dengan Anthropic. Gunakan sebagai alat bantu sementara,
   bukan sumber kebenaran resmi.

3. Setiap baris di CSV WAJIB diisi kolom `tokenizer_source` dan
   `measured_date` supaya jelas kapan dan pakai tokenizer versi apa data
   itu diambil -- jangan campur data dari sumber berbeda tanpa keterangan.

## Cara Isi

1. Buka https://claude-tokenizer.vercel.app/
2. Paste teks di kolom `natural_text` pada CSV -> catat jumlah token ke
   kolom `natural_tokens`
3. Paste teks di kolom `ailang_text` -> catat ke kolom `compressed_tokens`
4. Kolom `tokens_saved` = natural_tokens - compressed_tokens
5. Kolom `efficiency_pct` = (tokens_saved / natural_tokens) * 100
6. Isi `measured_date` (format YYYY-MM-DD) dan `tokenizer_source`
   (contoh: "claude-tokenizer.vercel.app / Claude Sonnet 4")

## Kapan Migrasi ke Pengukuran Resmi

Begitu ada akses ke `ANTHROPIC_API_KEY` berkredit, ulangi semua baris
pakai `claude_tools/token_counter.py compare` dengan `--model claude-sonnet-5`
(atau model final yang akan dipakai), lalu bandingkan selisihnya dengan
data manual ini. Jangan menggantikan data lama diam-diam -- tambahkan
kolom/baris baru supaya kedua sumber tetap bisa diaudit.
