"""
Unit test untuk claude_tools/token_counter.py

Menggunakan mock (unittest.mock) untuk client Anthropic -- TIDAK memerlukan
ANTHROPIC_API_KEY asli dan TIDAK memanggil API sungguhan. Ini menguji logika
wrapper (pemanggilan parameter, kalkulasi efisiensi, error handling), bukan
akurasi tokenizer resmi Anthropic itu sendiri.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "claude_tools"))

import token_counter as tc


def make_mock_client(input_tokens_sequence):
    """Buat mock client yang mengembalikan input_tokens sesuai urutan panggilan."""
    client = MagicMock()
    responses = [MagicMock(input_tokens=n) for n in input_tokens_sequence]
    client.messages.count_tokens.side_effect = responses
    return client


class TestCountTokens(unittest.TestCase):
    def test_count_tokens_returns_input_tokens(self):
        client = make_mock_client([14])
        result = tc.count_tokens("Hello, Claude", model="claude-sonnet-5", client=client)
        self.assertEqual(result, 14)

    def test_count_tokens_passes_model_and_message(self):
        client = make_mock_client([14])
        tc.count_tokens("halo", model="claude-sonnet-5", client=client)
        _, kwargs = client.messages.count_tokens.call_args
        self.assertEqual(kwargs["model"], "claude-sonnet-5")
        self.assertEqual(kwargs["messages"], [{"role": "user", "content": "halo"}])

    def test_count_tokens_includes_system_when_given(self):
        client = make_mock_client([20])
        tc.count_tokens("halo", model="claude-sonnet-5", system="You are a scientist", client=client)
        _, kwargs = client.messages.count_tokens.call_args
        self.assertEqual(kwargs["system"], "You are a scientist")

    def test_count_tokens_omits_system_when_not_given(self):
        client = make_mock_client([10])
        tc.count_tokens("halo", client=client)
        _, kwargs = client.messages.count_tokens.call_args
        self.assertNotIn("system", kwargs)


class TestCompareEfficiency(unittest.TestCase):
    def test_compare_calculates_savings_correctly(self):
        # natural = 100 token, compressed = 40 token -> hemat 60 token (60%)
        client = make_mock_client([100, 40])
        result = tc.compare_efficiency("teks natural", "{ctx:x}", client=client)
        self.assertEqual(result.natural_tokens, 100)
        self.assertEqual(result.compressed_tokens, 40)
        self.assertEqual(result.tokens_saved, 60)
        self.assertEqual(result.efficiency_pct, 60.0)

    def test_compare_handles_negative_savings(self):
        # kasus AILang justru LEBIH BANYAK token (mis. simbol Unicode langka)
        client = make_mock_client([10, 15])
        result = tc.compare_efficiency("pendek", "∧∈⤳", client=client)
        self.assertEqual(result.tokens_saved, -5)
        self.assertEqual(result.efficiency_pct, -50.0)

    def test_compare_zero_natural_tokens_no_division_error(self):
        client = make_mock_client([0, 0])
        result = tc.compare_efficiency("", "", client=client)
        self.assertEqual(result.efficiency_pct, 0.0)

    def test_compare_uses_same_model_for_both_calls(self):
        client = make_mock_client([50, 20])
        tc.compare_efficiency("a", "b", model="claude-opus-4-8", client=client)
        for call in client.messages.count_tokens.call_args_list:
            self.assertEqual(call.kwargs["model"], "claude-opus-4-8")


class TestGetClient(unittest.TestCase):
    def test_raises_when_api_key_missing(self):
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(EnvironmentError):
                tc.get_client()
        finally:
            if old_key is not None:
                os.environ["ANTHROPIC_API_KEY"] = old_key


if __name__ == "__main__":
    unittest.main()
