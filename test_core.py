"""Small tests. Run with: python -m unittest -v  (no real API key needed)."""

import csv
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import config
import optimizer
import prompts
import storage
from google.genai import errors as genai_errors
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


def api_error(code, status="ERR"):
    """Build a real Gemini SDK error with the given HTTP code (no network used)."""
    cls = genai_errors.ServerError if code >= 500 else genai_errors.ClientError
    return cls(code, {"error": {"message": "test", "status": status}})


@mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"})
@mock.patch("optimizer.time.sleep")  # do not really wait in tests
class RetryAndErrorTests(unittest.TestCase):
    def test_retries_temporary_error_then_succeeds(self, _sleep):
        side = [api_error(503), api_error(503), FAKE_REPLY]
        with mock.patch.object(optimizer, "_gemini_request", side_effect=side) as m:
            optimized, _ = optimizer.optimize_prompt("hello")
        self.assertEqual(m.call_count, 3)  # 1 try + 2 retries
        self.assertIn("Role: coder", optimized)

    def test_gives_up_after_max_retries(self, _sleep):
        with mock.patch.object(optimizer, "_gemini_request", side_effect=api_error(503)) as m:
            with self.assertRaises(OptimizerError) as ctx:
                optimizer.optimize_prompt("hello")
        self.assertEqual(m.call_count, 1 + config.MAX_RETRIES)
        self.assertIn("busy", str(ctx.exception))

    def test_timeout_is_retried(self, _sleep):
        side = [TimeoutError("timed out"), FAKE_REPLY]
        with mock.patch.object(optimizer, "_gemini_request", side_effect=side) as m:
            optimizer.optimize_prompt("hello")
        self.assertEqual(m.call_count, 2)

    def test_permanent_errors_not_retried_and_have_own_messages(self, _sleep):
        cases = {404: "not found", 429: "quota", 403: "key"}
        for code, word in cases.items():
            with mock.patch.object(optimizer, "_gemini_request", side_effect=api_error(code)) as m:
                with self.assertRaises(OptimizerError) as ctx:
                    optimizer.optimize_prompt("hello")
            self.assertEqual(m.call_count, 1, code)
            self.assertIn(word, str(ctx.exception).lower(), code)

    def test_invalid_key_reported_as_400(self, _sleep):
        err = genai_errors.ClientError(400, {"error": {"message": "API key not valid", "status": "INVALID_ARGUMENT"}})
        with mock.patch.object(optimizer, "_gemini_request", side_effect=err):
            with self.assertRaises(OptimizerError) as ctx:
                optimizer.optimize_prompt("hello")
        self.assertIn("API key", str(ctx.exception))

    def test_empty_model_reply(self, _sleep):
        with mock.patch.object(optimizer, "_gemini_request", return_value="  "):
            with self.assertRaises(OptimizerError):
                optimizer.optimize_prompt("hello")


class InputValidationTests(unittest.TestCase):
    def test_too_long_input_rejected(self):
        with self.assertRaises(OptimizerError) as ctx:
            optimizer.optimize_prompt("x" * (config.MAX_INPUT_CHARS + 1))
        self.assertIn(str(config.MAX_INPUT_CHARS), str(ctx.exception))

    def test_too_long_custom_instruction_rejected(self):
        with self.assertRaises(OptimizerError):
            optimizer.optimize_prompt("hi", custom_instruction="x" * (config.MAX_CUSTOM_CHARS + 1))

    def test_count_words(self):
        self.assertEqual(optimizer.count_words("one two  three\nfour"), 4)
        self.assertEqual(optimizer.count_words(""), 0)


class MetaPromptTests(unittest.TestCase):
    def test_custom_instruction_added(self):
        text = prompts.build_meta_prompt("General", "Balanced", "Hinglish mein output")
        self.assertIn("Hinglish mein output", text)

    def test_no_custom_instruction_by_default(self):
        self.assertNotIn("Extra requirement", prompts.build_meta_prompt("General"))

    def test_each_length_changes_prompt(self):
        texts = {length: prompts.build_meta_prompt("General", length) for length in prompts.LENGTHS}
        self.assertEqual(len(set(texts.values())), 3)
        self.assertIn("80 words", texts["Short"])

    def test_options_reach_llm_call(self):
        with mock.patch.object(optimizer, "call_llm", return_value=FAKE_REPLY) as m:
            optimizer.optimize_prompt("todo app", "Study", "Detailed", "keep it simple")
        system = m.call_args[0][0]
        self.assertIn("Study", system)
        self.assertIn("250 words", system)
        self.assertIn("keep it simple", system)

    def test_every_mode_has_description(self):
        for mode in prompts.MODES:
            self.assertTrue(prompts.MODE_DESCRIPTIONS[mode])


class ParsingTests(unittest.TestCase):
    def test_only_optimized_marker(self):
        optimized, why = optimizer.parse_reply(f"{OPTIMIZED_MARKER}\nDo X")
        self.assertEqual(optimized, "Do X")
        self.assertEqual(why, optimizer.NO_EXPLANATION_TEXT)

    def test_only_explanation_marker(self):
        optimized, why = optimizer.parse_reply(f"Do X\n{EXPLANATION_MARKER}\n- reason")
        self.assertEqual(optimized, "Do X")
        self.assertEqual(why, "- reason")

    def test_loose_marker_formatting(self):
        reply = "**Optimized Prompt:**\nDo X\n\n## What improved\nnot a marker"
        optimized, _ = optimizer.parse_reply(reply)
        self.assertIn("Do X", optimized)

    def test_code_fence_removed(self):
        reply = f"{OPTIMIZED_MARKER}\n```\nDo X\n```\n{EXPLANATION_MARKER}\n- ok"
        self.assertEqual(optimizer.parse_reply(reply)[0], "Do X")

    def test_empty_reply_does_not_crash(self):
        optimized, why = optimizer.parse_reply("")
        self.assertEqual(optimized, "")
        self.assertEqual(why, optimizer.NO_EXPLANATION_TEXT)


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

    def test_delete_one_entry(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "t.db")
            first = storage.save_entry("General", "a", "A", "e", db)
            storage.save_entry("Coding", "b", "B", "e", db)
            storage.delete_entry(first, db)
            rows = storage.load_history(20, db)
            self.assertEqual([r["original"] for r in rows], ["b"])
            storage.delete_entry(9999, db)  # missing id: no crash

    def test_clear_all(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "t.db")
            storage.save_entry("General", "a", "A", "e", db)
            storage.clear_history(db)
            self.assertEqual(storage.load_history(20, db), [])

    def test_export_json_and_csv_contain_all_entries(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "t.db")
            for i in range(25):  # more than the 20 shown in the sidebar
                storage.save_entry("General", f"orig {i}, with comma", "opt", "why", db)
            data = json.loads(storage.export_json(db))
            self.assertEqual(len(data), 25)
            self.assertEqual(set(data[0]), set(storage.COLUMNS))
            rows = list(csv.DictReader(io.StringIO(storage.export_csv(db))))
            self.assertEqual(len(rows), 25)
            self.assertEqual(rows[0]["original"], "orig 24, with comma")  # CSV quoting works

    def test_db_path_from_env(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "custom.db")
            with mock.patch.dict(os.environ, {"DB_PATH": path}):
                storage.save_entry("General", "a", "A", "e")
            self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
