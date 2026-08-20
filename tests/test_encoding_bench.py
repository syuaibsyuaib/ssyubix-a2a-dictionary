"""
Unit test untuk claude_tools/encoding_bench.py

Fokus pada hal yang BISA diuji tanpa kredensial: kebenaran encoding
panjang-tetap (harus reversible), konsistensi kapasitas antar kandidat,
dan kalkulasi metrik. Tahap `measure` diuji pakai mock, sama seperti
test_token_counter.py -- tidak memanggil API sungguhan.
"""
import math
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "claude_tools"))

import encoding_bench as eb


class TestFixedWidthEncoding(unittest.TestCase):
    def test_binary_roundtrip(self):
        s = eb._fixed_width(eb.SAMPLE_INT, "01")
        self.assertEqual(int(s, 2), eb.SAMPLE_INT)

    def test_hex_roundtrip(self):
        s = eb._fixed_width(eb.SAMPLE_INT, "0123456789ABCDEF")
        self.assertEqual(int(s, 16), eb.SAMPLE_INT)

    def test_binary_width_is_exactly_total_bits(self):
        self.assertEqual(len(eb._fixed_width(eb.SAMPLE_INT, "01")), eb.TOTAL_BITS)

    def test_width_is_constant_across_all_values(self):
        # inti ide "panjang tetap": nilai terkecil dan terbesar sama panjangnya
        lo = eb._fixed_width(0, "01")
        hi = eb._fixed_width(eb.CAPACITY - 1, "01")
        self.assertEqual(len(lo), len(hi))

    def test_max_value_fits(self):
        for alpha in ("01", "0123456789ABCDEF"):
            s = eb._fixed_width(eb.CAPACITY - 1, alpha)
            width = math.ceil(eb.TOTAL_BITS / math.log2(len(alpha)))
            self.assertEqual(len(s), width)

    def test_negative_value_rejected(self):
        with self.assertRaises(ValueError):
            eb._base_n(-1, "01", 8)


class TestCandidates(unittest.TestCase):
    def setUp(self):
        self.cands = eb.build_candidates()

    def test_scheme_ids_unique(self):
        ids = [c.scheme_id for c in self.cands]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_candidates_nonempty(self):
        for c in self.cands:
            self.assertGreater(c.characters, 0, c.scheme_id)

    def test_unicode_variant_inflates_bytes_beyond_chars(self):
        # justru ini hipotesis yang diuji: simbol non-ASCII bikin byte > char
        uni = next(c for c in self.cands if c.scheme_id == "ailang_unicode")
        self.assertGreater(uni.non_ascii_chars, 0)
        self.assertGreater(uni.utf8_bytes, uni.characters)

    def test_ascii_variants_have_bytes_equal_chars(self):
        for c in self.cands:
            if c.non_ascii_chars == 0:
                self.assertEqual(c.utf8_bytes, c.characters, c.scheme_id)

    def test_binary_is_denser_per_char_than_natural(self):
        b = next(c for c in self.cands if c.scheme_id == "binary_fixed")
        n = next(c for c in self.cands if c.scheme_id == "natural_full")
        self.assertGreater(b.bits_per_char, n.bits_per_char)

    def test_higher_base_beats_binary_per_char(self):
        by_id = {c.scheme_id: c for c in self.cands}
        self.assertGreater(by_id["hex_fixed"].bits_per_char,
                           by_id["binary_fixed"].bits_per_char)
        self.assertGreater(by_id["base64_fixed"].bits_per_char,
                           by_id["hex_fixed"].bits_per_char)


class TestMetrics(unittest.TestCase):
    def test_bits_per_token_none_before_measurement(self):
        c = eb.Candidate("x", "f", "abc")
        self.assertIsNone(c.bits_per_token)
        self.assertIsNone(c.pct_of_ceiling(100_000))

    def test_bits_per_token_after_measurement(self):
        c = eb.Candidate("x", "f", "abc", tokens=3)
        self.assertAlmostEqual(c.bits_per_token, eb.TOTAL_BITS / 3)

    def test_pct_of_ceiling_caps_at_100_for_ideal_codebook(self):
        # 1 token per field pada vocab 2^8 = tepat menyentuh plafon
        c = eb.Candidate("ideal", "codebook", "a b c", tokens=eb.FIELD_COUNT)
        self.assertAlmostEqual(c.pct_of_ceiling(2 ** eb.FIELD_BITS), 100.0)

    def test_zero_tokens_does_not_divide_by_zero(self):
        c = eb.Candidate("x", "f", "abc", tokens=0)
        self.assertIsNone(c.bits_per_token)

    def test_empty_text_does_not_divide_by_zero(self):
        c = eb.Candidate("x", "f", "")
        self.assertEqual(c.bits_per_char, 0.0)
        self.assertEqual(c.bits_per_byte, 0.0)


class TestMeasureWithMock(unittest.TestCase):
    def test_measure_fills_tokens_from_counter(self):
        fake = MagicMock()
        fake.get_client.return_value = MagicMock()
        fake.count_tokens.return_value = 7
        with patch.dict(sys.modules, {"token_counter": fake}):
            cands = eb.build_candidates()[:3]
            source = eb.measure(cands, "claude-opus-5")
        self.assertTrue(all(c.tokens == 7 for c in cands))
        self.assertIn("claude-opus-5", source)

    def test_validate_codebook_splits_single_vs_multi(self):
        fake = MagicMock()
        fake.get_client.return_value = MagicMock()
        # panggilan pertama = baseline "x" -> 1; lalu 1, 2, 1
        fake.count_tokens.side_effect = [1, 1, 2, 1]
        with patch.dict(sys.modules, {"token_counter": fake}):
            single, multi = eb.validate_codebook(["a", "bb", "c"], "claude-opus-5")
        self.assertEqual(len(single), 2)
        self.assertEqual(len(multi), 1)
        self.assertIn("bb", multi[0])


if __name__ == "__main__":
    unittest.main()
