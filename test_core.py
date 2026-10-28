"""Small tests. Run with: python -m unittest -v  (no real API key needed)."""

import os
import tempfile
import unittest
from unittest import mock

import optimizer
import storage
from optimizer import OptimizerError
from prompts import EXPLANATION_MARKER, OPTIMIZED_MARKER

FAKE_REPLY = f"{OPTIMIZED_MARKER}\nRole: coder\nTask: todo app\n\n{EXPLANATION_MARKER}\n- added role"


class OptimizerTests(unittest.TestCase):
    def test_empty_input(self):
        with self.assertRaises(OptimizerError):
            optimizer.optimize_prompt("   ", "General")

    def test_missing_api_key(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaises(OptimizerError) as ctx:
                optimizer.optimize_prompt("hello", "General")
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    def test_success_with_mocked_llm(self):
        with mock.patch.object(optimizer, "call_llm", return_value=FAKE_REPLY) as m:
            optimized, why = optimizer.optimize_prompt("todo app", "Coding")
        self.assertIn("Role: coder", optimized)
        self.assertIn("added role", why)
        self.assertIn("Coding", m.call_args[0][0])  # mode reached the meta-prompt

    def test_api_failure_is_friendly(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}):
            with mock.patch("google.genai.Client", side_effect=RuntimeError("boom")):
                with self.assertRaises(OptimizerError):
                    optimizer.optimize_prompt("hello", "General")

    def test_reply_without_markers(self):
        optimized, _ = optimizer.parse_reply("just text")
        self.assertEqual(optimized, "just text")


class StorageTests(unittest.TestCase):
    def test_save_and_load_limit_and_order(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "t.db")
            self.assertEqual(storage.load_history(20, db), [])
            for i in range(25):
                storage.save_entry("General", f"o{i}", f"p{i}", "e", db)
            rows = storage.load_history(20, db)
            self.assertEqual(len(rows), 20)
            self.assertEqual(rows[0]["original"], "o24")  # newest first


if __name__ == "__main__":
    unittest.main()
