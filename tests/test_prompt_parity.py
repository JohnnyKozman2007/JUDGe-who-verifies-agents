"""
Strategy is an independent variable in this experiment. If direct/cot/rubric differ in
WHAT they ask the verifier to check, an accuracy gap between them cannot be attributed
to reasoning style. These tests hold the criteria constant so only the communication
style varies.
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from prompts import get_generation_prompt, get_verification_prompt

STRATEGIES = ["direct", "cot", "rubric"]
QUESTION = "What is 2 + 2?"
CANDIDATE = "2 + 2 = 4. The answer is 4."

SCIENCE_QUESTION = "Which option best describes photosynthesis?\nA. Respiration\nB. Light-driven glucose production\nC. Protein folding\nD. DNA replication"
SCIENCE_CANDIDATE = "The process uses light energy to produce glucose. FINAL ANSWER: B"

def science_prompt(strategy, frame="neutral"):
    return get_verification_prompt("science", SCIENCE_QUESTION, SCIENCE_CANDIDATE, frame, strategy)

def math_prompt(strategy, frame="neutral"):
    return get_verification_prompt("math", QUESTION, CANDIDATE, frame, strategy)

def criteria_block(prompt):
    m = re.search(r'CRITICAL EVALUATION INSTRUCTIONS:\n((?:\d+\. .*\n)+)', prompt)
    return m.group(1) if m else None

class ScienceCriteriaAreIdenticalAcrossStrategies(unittest.TestCase):

    def test_criteria_block_is_byte_identical(self):
        blocks = {s: criteria_block(science_prompt(s)) for s in STRATEGIES}
        for s, b in blocks.items():
            self.assertIsNotNone(b, f"{s} has no criteria block")
        self.assertEqual(len(set(blocks.values())), 1, f"criteria differ by strategy: {blocks}")

    def test_every_strategy_binds_its_verdict_to_the_criteria(self):
        for s in STRATEGIES:
            self.assertIn("criteria 1-4", science_prompt(s),
                          f"{s} never tells the verifier the criteria are the standard")

    def test_strategies_differ_only_after_the_criteria_block(self):
        heads = {
            science_prompt(s)
            .split("Apply evaluation")[0]
            .split("Work through")[0]
            .split("Score the candidate")[0]
            for s in STRATEGIES
        }
        self.assertEqual(len(heads), 1)

class MathCriteriaAreIdenticalAcrossStrategies(unittest.TestCase):

    def test_criteria_block_is_byte_identical(self):
        blocks = {s: criteria_block(math_prompt(s)) for s in STRATEGIES}
        for s, b in blocks.items():
            self.assertIsNotNone(b, f"{s} has no criteria block")
        self.assertEqual(len(set(blocks.values())), 1, f"criteria differ by strategy: {blocks}")

    def test_every_strategy_binds_its_verdict_to_the_criteria(self):
        for s in STRATEGIES:
            self.assertIn("criteria 1-4", math_prompt(s),
                          f"{s} never tells the verifier the criteria are the standard")

    def test_strategies_differ_only_after_the_criteria_block(self):
        heads = {math_prompt(s).split("Apply evaluation")[0].split("Work through")[0].split("Score the candidate")[0]
                 for s in STRATEGIES}
        self.assertEqual(len(heads), 1, "strategies diverge before the criteria block ends")

class ScienceExamplesMustNotAnchorAVerdict(unittest.TestCase):

    def test_no_strategy_shows_only_one_label(self):
        for s in STRATEGIES:
            p = science_prompt(s)
            has_true = '"is_correct": true' in p
            has_false = '"is_correct": false' in p
            self.assertTrue(has_true and has_false)

    def test_no_example_reasoning_asserts_the_candidate_was_correct(self):
        for s in STRATEGIES:
            self.assertNotIn("The candidate correctly", science_prompt(s))

    def test_science_cot_and_rubric_warn_against_latex_json_escapes(self):
        """Only cot and rubric emit a 'thinking' string, so only they can produce an invalid
        JSON escape. Measured on 474 real failures: 70.9% carried LaTeX math delimiters and
        46.0% a backslashed Greek letter, so the instruction has to name delimiters, not just
        Greek letters."""
        for s in ["cot", "rubric"]:
            p = science_prompt(s)
            self.assertIn("use no backslashes at all", p)
            self.assertIn("LaTeX math delimiters", p)

    def test_science_direct_has_no_latex_json_escape_warning(self):
        self.assertNotIn("use no backslashes at all", science_prompt("direct"))


class ScienceFramingIsTheOnlyOwnershipDifference(unittest.TestCase):

    def test_frames_differ_only_in_the_ownership_sentence(self):
        for s in STRATEGIES:
            bodies = set()
            for frame in ["self", "other", "neutral"]:
                p = science_prompt(s, frame)
                bodies.add(p[p.index("Your task is to verify"):])
            self.assertEqual(len(bodies), 1)

class ScienceCriteriaMustNotDirectAVerdict(unittest.TestCase):
    """Criterion-level anchoring is the same failure as example-level anchoring: telling the
    verifier which way to rule biases the exact axis being measured. Science previously ended
    its criteria with "...mark it incorrect", which math has no counterpart for, so a science
    FPR/FNR gap could be read off the prompt rather than the model."""

    def test_no_criterion_instructs_a_verdict(self):
        for s in STRATEGIES:
            block = criteria_block(science_prompt(s)).lower()
            for directive in ["mark it incorrect", "mark it correct"]:
                self.assertNotIn(directive, block,
                                 f"{s} criteria tell the verifier which verdict to give")

    def test_science_has_exactly_four_criteria(self):
        """Four is a science-specific choice, not an echo of math: two shared rigour rules,
        one substantive factual check, one format/consistency check. Science's measured
        failure is approving wrong answers, not format slips, so extra numbered format
        criteria would pull verifier attention away from the check that matters. Pinned to a
        literal rather than compared against math, so the math prompt can evolve freely."""
        for s in STRATEGIES:
            n = len(re.findall(r'^\d+\. ', criteria_block(science_prompt(s)), re.M))
            self.assertEqual(n, 4, f"{s} has {n} criteria, expected 4")


class ScienceGenerationPromptForcesAFinalAnswerLine(unittest.TestCase):
    """parse_science_candidate_answer's highest-confidence tier is the strict
    'FINAL ANSWER: <letter>' line; the generator has to actually emit it."""

    def test_requires_a_final_answer_line(self):
        self.assertIn("FINAL ANSWER", get_generation_prompt("science", "Q"))

    def test_demands_exactly_one_final_line(self):
        self.assertIn("exactly one", get_generation_prompt("science", "Q"))

    def test_does_not_show_a_literal_placeholder_to_echo(self):
        """Weak models copy a shown template verbatim instead of substituting their letter,
        which silently drops the answer to a lower-confidence parser tier."""
        self.assertNotIn("<A, B, C, or D>", get_generation_prompt("science", "Q"))

    def test_verification_criteria_reference_the_same_format(self):
        for s in STRATEGIES:
            self.assertIn("FINAL ANSWER", science_prompt(s),
                          f"{s} does not check the format the generator was told to use")


class ScienceVerifierPromptHasNoInjectedParse(unittest.TestCase):
    """The parity tests above assert on get_verification_prompt output, but verify.py is what
    actually reaches the API. It used to append the grader's own parse to the science prompt.
    Since report.py scores science as (parsed letter == ground truth AND not ambiguous), that
    made verifier and grader agree by construction wherever extraction failed. The parse must
    stay on the output row for auditing and stay out of the prompt."""

    @staticmethod
    def _verify_source():
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "verify.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_parse_block_is_not_injected_into_the_prompt(self):
        src = self._verify_source()
        self.assertNotIn("[SCIENCE ANSWER PARSE]", src,
                         "verify.py is injecting the grader's parse back into the prompt")

    def test_parse_is_still_recorded_for_auditing(self):
        src = self._verify_source()
        self.assertIn("parse_science_candidate_answer", src)
        self.assertIn("candidate_answer_letter", src)


class ExamplesMustNotAnchorAVerdict(unittest.TestCase):
    """A one-shot example with a fixed label biases the verdict, and the old prompts
    anchored true for direct/cot and false for rubric, along the measured axis."""

    def test_no_strategy_shows_only_one_label(self):
        for s in STRATEGIES:
            p = math_prompt(s)
            has_true = '"is_correct": true' in p
            has_false = '"is_correct": false' in p
            self.assertTrue(has_true and has_false,
                            f"{s} anchors a single verdict (true={has_true}, false={has_false})")

    def test_no_example_reasoning_asserts_the_candidate_was_correct(self):
        for s in STRATEGIES:
            p = math_prompt(s)
            self.assertNotIn("The candidate correctly", p,
                             f"{s} example reasoning leans positive")


class FramingIsTheOnlyOwnershipDifference(unittest.TestCase):

    def test_frames_differ_only_in_the_ownership_sentence(self):
        for s in STRATEGIES:
            bodies = set()
            for frame in ["self", "other", "neutral"]:
                p = math_prompt(s, frame)
                bodies.add(p[p.index("Your task is to verify"):])
            self.assertEqual(len(bodies), 1,
                             f"{s}: frames change more than the ownership sentence")


class MathGenerationPromptForcesAnAnswerTag(unittest.TestCase):
    """grade_math's most reliable path is the <answer> tag; the generator has to produce it."""

    def test_requires_answer_tags(self):
        p = get_generation_prompt("math", "What is 2 + 2?")
        self.assertIn("<answer></answer>", p)

    def test_demands_exactly_one_tag(self):
        self.assertIn("exactly one <answer> tag", get_generation_prompt("math", "Q"))

    def test_verification_criteria_reference_the_same_tag(self):
        for s in STRATEGIES:
            self.assertIn("<answer></answer>", math_prompt(s),
                          f"{s} does not check the format the generator was told to use")


class OtherDomainsAreUntouched(unittest.TestCase):
    """This slice is math only. Changing code or science generation prompts would
    invalidate their committed data."""

    def test_code_generation_prompt_unchanged(self):
        self.assertIn("Provide ONLY the valid Python code", get_generation_prompt("code", "Q"))

    def test_science_generation_prompt_still_enforces_final_answer(self):
        # preflight_check.py asserts this exact string.
        self.assertIn("FINAL ANSWER", get_generation_prompt("science", "Q"))

    def test_science_and_code_have_no_answer_tag_requirement(self):
        for d in ["code", "science"]:
            self.assertNotIn("<answer>", get_generation_prompt(d, "Q"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
