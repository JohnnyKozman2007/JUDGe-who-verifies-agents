"""
Science-domain grading depends on extracting exactly one A-D option from GPQA-style
answers. These tests protect the parser/grader contract before expensive verification
runs, similar to how prompt parity tests protect the prompt contract.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from science_utils import (
    build_option_map,
    extract_option_map_from_question,
    grade_science_candidate,
    normalize_option_text,
    parse_science_candidate_answer,
    render_science_question,
    sanitize_json_escapes,
    validate_option_map,
    validate_science_options,
)


OPTIONS = [
    "Respiration",
    "Light-driven glucose production",
    "Protein folding",
    "DNA replication",
]

OPTION_MAP = {
    "A": "Respiration",
    "B": "Light-driven glucose production",
    "C": "Protein folding",
    "D": "DNA replication",
}

RAW_ITEM = {
    "item_id": "science_test",
    "question": render_science_question("Which option best describes photosynthesis?", OPTIONS),
    "ground_truth": "B",
    "correct_answer_text": "Light-driven glucose production",
    "option_map": OPTION_MAP,
}


class ScienceOptionValidationTests(unittest.TestCase):

    def test_valid_options_pass(self):
        self.assertEqual(validate_science_options(OPTIONS), [])

    def test_duplicate_options_are_rejected_after_normalization(self):
        options = ["Alpha", "Beta", "beta ", "Delta"]
        issues = validate_science_options(options)
        self.assertTrue(any("duplicates" in issue for issue in issues), issues)

    def test_empty_options_are_rejected(self):
        options = ["Alpha", "", "Gamma", "Delta"]
        issues = validate_science_options(options)
        self.assertTrue(any("empty" in issue for issue in issues), issues)

    def test_wrong_option_count_is_rejected(self):
        issues = validate_science_options(["Alpha", "Beta", "Gamma"])
        self.assertTrue(any("expected 4 options" in issue for issue in issues), issues)

    def test_option_map_must_have_exact_labels_a_to_d(self):
        bad_map = {"A": "Alpha", "B": "Beta", "C": "Gamma", "E": "Delta"}
        issues = validate_option_map(bad_map)
        self.assertTrue(any("option_map labels" in issue for issue in issues), issues)

    def test_build_option_map_uses_stable_a_to_d_labels(self):
        self.assertEqual(build_option_map(OPTIONS), OPTION_MAP)


class ScienceQuestionRenderingTests(unittest.TestCase):

    def test_render_science_question_uses_stable_option_format(self):
        rendered = render_science_question("Question stem", OPTIONS)
        self.assertIn("Question stem", rendered)
        self.assertIn("Options:", rendered)
        self.assertIn("A. Respiration", rendered)
        self.assertIn("D. DNA replication", rendered)

    def test_extract_option_map_from_rendered_question(self):
        rendered = render_science_question("Question stem", OPTIONS)
        self.assertEqual(extract_option_map_from_question(rendered), OPTION_MAP)

    def test_extract_multiline_option_map(self):
        question = (
            "Which reagent sequence is correct?\n"
            "Options:\n"
            "A. 1. Zn, ether\n"
            "   2. HCl\n"
            "B. 1. NaBH4\n"
            "   2. H2O\n"
            "C. Heat only\n"
            "D. No reaction\n"
        )
        option_map = extract_option_map_from_question(question)
        self.assertEqual(set(option_map.keys()), {"A", "B", "C", "D"})
        self.assertIn("Zn, ether", option_map["A"])
        self.assertIn("HCl", option_map["A"])
        self.assertIn("NaBH4", option_map["B"])


class ScienceAnswerParsingTests(unittest.TestCase):

    def test_strict_final_answer_line_is_high_confidence(self):
        parsed = parse_science_candidate_answer("Reasoning here.\nFINAL ANSWER: B", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertEqual(parsed["option_text"], OPTION_MAP["B"])
        self.assertEqual(parsed["mode"], "strict_final_answer")
        self.assertEqual(parsed["confidence"], "high")
        self.assertFalse(parsed["ambiguous"])

    def test_final_answer_accepts_parenthesized_letter(self):
        parsed = parse_science_candidate_answer("Reasoning here.\nFINAL ANSWER: (B)", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertFalse(parsed["ambiguous"])

    def test_multiple_strict_final_answers_are_ambiguous(self):
        parsed = parse_science_candidate_answer("FINAL ANSWER: A\nFINAL ANSWER: B", OPTION_MAP)
        self.assertIsNone(parsed["letter"])
        self.assertTrue(parsed["ambiguous"])
        self.assertTrue(any("multiple_strict_final_answers" in note for note in parsed["notes"]))

    def test_explicit_answer_statement_is_parsed(self):
        parsed = parse_science_candidate_answer("After checking the options, the correct answer is B.", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertEqual(parsed["mode"], "explicit_answer_statement")
        self.assertEqual(parsed["confidence"], "high")

    def test_conflicting_explicit_answers_are_marked_ambiguous(self):
        parsed = parse_science_candidate_answer("The answer is A. Therefore, the answer is B.", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertTrue(parsed["ambiguous"])
        self.assertEqual(parsed["mode"], "explicit_answer_statement_conflicting")

    def test_last_line_letter_fallback(self):
        parsed = parse_science_candidate_answer("The explanation points to glucose production.\nB", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertEqual(parsed["mode"], "last_line_letter")
        self.assertEqual(parsed["confidence"], "medium")

    def test_unique_option_text_match_without_letter(self):
        parsed = parse_science_candidate_answer(
            "The best description is light-driven glucose production.",
            OPTION_MAP,
        )
        self.assertEqual(parsed["letter"], "B")
        self.assertEqual(parsed["option_text"], OPTION_MAP["B"])
        self.assertEqual(parsed["mode"], "unique_option_text_match")

    def test_multiple_option_text_matches_are_ambiguous(self):
        parsed = parse_science_candidate_answer(
            "This discusses respiration and DNA replication.",
            OPTION_MAP,
        )
        self.assertIsNone(parsed["letter"])
        self.assertTrue(parsed["ambiguous"])
        self.assertTrue(any("multiple_option_text_matches" in note for note in parsed["notes"]))

    def test_choose_statement_is_high_confidence_explicit_answer(self):
        parsed = parse_science_candidate_answer("Long reasoning without final tag. I choose B.", OPTION_MAP)
        self.assertEqual(parsed["letter"], "B")
        self.assertEqual(parsed["mode"], "explicit_answer_statement")
        self.assertEqual(parsed["confidence"], "high")

    def test_no_answer_returns_no_letter(self):
        parsed = parse_science_candidate_answer("This response never selects an option.", OPTION_MAP)
        self.assertIsNone(parsed["letter"])
        self.assertEqual(parsed["confidence"], "none")

    def test_empty_answer_returns_note(self):
        parsed = parse_science_candidate_answer("", OPTION_MAP)
        self.assertIsNone(parsed["letter"])
        self.assertIn("empty_candidate_text", parsed["notes"])


class ScienceGradingTests(unittest.TestCase):

    def test_correct_final_answer_grades_true(self):
        self.assertTrue(grade_science_candidate("Reasoning.\nFINAL ANSWER: B", RAW_ITEM))

    def test_wrong_final_answer_grades_false(self):
        self.assertFalse(grade_science_candidate("Reasoning.\nFINAL ANSWER: C", RAW_ITEM))

    def test_unique_option_text_match_grades_true(self):
        self.assertTrue(
            grade_science_candidate("The best answer is light-driven glucose production.", RAW_ITEM)
        )

    def test_ambiguous_answer_grades_false_even_if_ground_truth_appears(self):
        self.assertFalse(grade_science_candidate("FINAL ANSWER: A\nFINAL ANSWER: B", RAW_ITEM))

    def test_missing_option_map_falls_back_to_question_extraction(self):
        raw_item_without_map = {
            "item_id": "science_test",
            "question": RAW_ITEM["question"],
            "ground_truth": "B",
        }
        self.assertTrue(
            grade_science_candidate("Reasoning.\nFINAL ANSWER: B", raw_item_without_map)
        )


class ScienceNormalizationTests(unittest.TestCase):

    def test_normalization_handles_case_spacing_and_quotes(self):
        self.assertEqual(
            normalize_option_text('  "Light-driven   glucose production."  '),
            "light-driven glucose production",
        )

    def test_normalization_preserves_scientific_content(self):
        normalized = normalize_option_text("α + β → γ")
        self.assertIn("α", normalized)
        self.assertIn("β", normalized)
        self.assertIn("γ", normalized)


class JsonEscapeRepairTests(unittest.TestCase):
    """GPQA verifier responses are notation-dense, so cot/rubric emit LaTeX inside JSON
    strings and produce invalid escapes. Measured on 474 real failures: 70.9% carried
    LaTeX math delimiters, 46.0% a backslashed Greek letter. Repairing and re-parsing
    recovers 'thinking' too, which a regex for is_correct alone cannot."""

    def _roundtrip(self, raw):
        return json.loads(sanitize_json_escapes(raw))

    def test_latex_math_delimiters_are_repaired(self):
        raw = r'{"thinking": "the value is \(a \approx 0.85\)", "is_correct": true}'
        obj = self._roundtrip(raw)
        self.assertIs(obj["is_correct"], True)
        self.assertIn("0.85", obj["thinking"])

    def test_backslashed_greek_letters_are_repaired(self):
        raw = r'{"thinking": "mass dimension of \kappa is -1", "is_correct": false}'
        obj = self._roundtrip(raw)
        self.assertIs(obj["is_correct"], False)
        self.assertIn("kappa", obj["thinking"])

    def test_mixed_single_and_double_backslashes(self):
        """Regression: models mix conventions inside one response. A naive per-backslash
        pass re-examines the trailing backslash of a valid '\\\\' pair and corrupts it,
        which left 21 of 474 real failures unparseable."""
        raw = r'{"thinking": "which is \( \\gamma B \\)", "is_correct": true}'
        obj = self._roundtrip(raw)
        self.assertIs(obj["is_correct"], True)
        self.assertIn("gamma", obj["thinking"])

    def test_thinking_is_recovered_not_just_the_verdict(self):
        """The whole point of repairing over regexing: 'thinking' drives the verbosity and
        dissociation metrics, and the regex path drops it."""
        raw = r'{"thinking": "candidate used \(E = mc^2\) correctly", "is_correct": true}'
        obj = self._roundtrip(raw)
        self.assertTrue(obj["thinking"].strip())
        self.assertIn("correctly", obj["thinking"])

    def test_already_valid_json_is_left_alone(self):
        raw = '{"thinking": "no backslashes here", "is_correct": true}'
        self.assertEqual(json.loads(raw), self._roundtrip(raw))

    def test_legitimate_escapes_survive(self):
        raw = r'{"thinking": "line one\nline two, quote: \"x\"", "is_correct": false}'
        obj = self._roundtrip(raw)
        self.assertIn("\n", obj["thinking"])
        self.assertIn('"x"', obj["thinking"])

    def test_unicode_escape_is_not_broken(self):
        raw = r'{"thinking": "alpha is α", "is_correct": true}'
        self.assertIn("α", self._roundtrip(raw)["thinking"])

    def test_empty_and_none_are_passed_through(self):
        self.assertEqual(sanitize_json_escapes(""), "")
        self.assertIsNone(sanitize_json_escapes(None))

    def test_structurally_broken_json_is_not_rescued(self):
        """A missing comma is not an escape problem. The repairer must not guess at
        structure; those rows fall through to the verdict-only recovery path."""
        raw = '{"thinking": "text" "is_correct": true}'
        with self.assertRaises(json.JSONDecodeError):
            self._roundtrip(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)