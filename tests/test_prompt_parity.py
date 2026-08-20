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
from prompts import get_verification_prompt

STRATEGIES = ["direct", "cot", "rubric"]
QUESTION = "What is 2 + 2?"
CANDIDATE = "2 + 2 = 4. The answer is 4."

def math_prompt(strategy, frame="neutral"):
    return get_verification_prompt("math", QUESTION, CANDIDATE, frame, strategy)

def criteria_block(prompt):
    m = re.search(r'CRITICAL EVALUATION INSTRUCTIONS:\n((?:\d+\. .*\n)+)', prompt)
    return m.group(1) if m else None


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
