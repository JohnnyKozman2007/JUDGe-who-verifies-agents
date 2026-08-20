"""
Spec for grade_math (issue #3).

grade_math produces the ground-truth label that every math verifier verdict is
scored against, so a false positive here silently converts a verifier's false
positive into a true positive and corrupts the bias metrics downstream.

The rule these tests encode: grade only the candidate's FINAL answer. A number
that merely appears somewhere in the working is not an answer.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from report import grade_math


class CorrectAnswersMustPass(unittest.TestCase):
    """Backward compatibility: the fix must not over-correct into false negatives."""

    def test_boxed_match(self):
        self.assertTrue(grade_math(r"Working... \boxed{5}", r"So the answer is \boxed{5}"))

    def test_answer_is_phrase(self):
        self.assertTrue(grade_math("Adding 3 and 4 we get 7. The answer is 7.", r"\boxed{7}"))

    def test_final_answer_phrase(self):
        self.assertTrue(grade_math("Some working here. Final answer: 42", r"\boxed{42}"))

    def test_therefore_phrase(self):
        self.assertTrue(grade_math("We simplify the expression. Therefore, x = 3.", r"\boxed{3}"))

    def test_trailing_number_without_marker(self):
        self.assertTrue(grade_math("Multiply 6 by 7 to get 42.", r"\boxed{42}"))

    def test_numeric_equivalence_decimal(self):
        self.assertTrue(grade_math("The answer is 0.50", r"\boxed{0.5}"))

    def test_numeric_equivalence_comma(self):
        self.assertTrue(grade_math("The answer is 1000", r"\boxed{1,000}"))

    def test_prose_final_answer_with_multiple_numbers(self):
        # Real pilot case math_2/mistral: the stated answer is 6, but the sentence
        # also contains 50. Every value in the final-answer region must count.
        text = "= 300 / 50\n= 6\n\nFinal Answer: It would take 50 workers 6 days to build the embankment."
        self.assertTrue(grade_math(text, r"\boxed{6}"))

    def test_answer_stated_as_a_word(self):
        # Real pilot case math_6/mistral: question asks how many solutions, gt is 3,
        # candidate answers "three solutions".
        text = "For k = 2: x = 76. So, there are three solutions to the congruence: 8, 42, and 76."
        self.assertTrue(grade_math(text, r"\boxed{3}"))

    def test_non_numeric_ground_truth_match(self):
        self.assertTrue(grade_math("After simplifying, the answer is 3/4.", r"\boxed{3/4}"))


class AnswerTagIsTheStrongestSignal(unittest.TestCase):
    """The math generation prompt now requires <answer></answer>. The tag outranks
    every other extraction path."""

    def test_tag_is_used(self):
        self.assertTrue(grade_math("Working: 2x = 8, x = 4.\n<answer>4</answer>", r"\boxed{4}"))

    def test_tag_beats_a_matching_intermediate_value(self):
        self.assertFalse(grade_math("We had 5 apples, then 8.\n<answer>8</answer>", r"\boxed{5}"))

    def test_tag_outranks_boxed(self):
        self.assertFalse(grade_math(r"\boxed{5} but actually <answer>8</answer>", r"\boxed{5}"))

    def test_last_tag_wins_when_the_example_is_echoed(self):
        # A model may repeat the prompt's own example before giving its real answer.
        text = "Format reminder: <answer>3/4</answer>. My solution gives 12.\n<answer>12</answer>"
        self.assertTrue(grade_math(text, r"\boxed{12}"))
        self.assertFalse(grade_math(text, r"\boxed{3/4}"))

    def test_fraction_inside_tag(self):
        self.assertTrue(grade_math("Simplifying gives\n<answer>3/4</answer>", r"\boxed{3/4}"))


class IntermediateValuesMustNotCount(unittest.TestCase):
    """Issue #3: the ground truth appearing in the working must not grade as correct."""

    def test_issue_example_ground_truth_in_first_sentence(self):
        # gt 5 appears in the working, candidate's actual answer is 8
        text = "We start with 5 apples, then add 3 more, giving us 8 apples total. The answer is 8."
        self.assertFalse(grade_math(text, r"\boxed{5}"))

    def test_ground_truth_as_a_rate_in_working(self):
        text = "The rate is 12 per hour. Over 2.5 hours that gives 30. Final answer: 30."
        self.assertFalse(grade_math(text, r"\boxed{12}"))

    def test_ground_truth_appearing_as_an_exponent(self):
        text = "We square it: x^2 = 100, so the answer is 100."
        self.assertFalse(grade_math(text, r"\boxed{2}"))

    def test_non_numeric_ground_truth_in_working(self):
        text = "First we get 3/4 of the way, then halve it: 1/2."
        self.assertFalse(grade_math(text, r"\boxed{3/4}"))

    def test_candidate_boxes_a_wrong_answer(self):
        self.assertFalse(grade_math(r"Working: 5 apples... \boxed{8}", r"\boxed{5}"))

    def test_boxed_answer_wins_over_matching_intermediate_value(self):
        # 5 appears in the working AND the candidate boxed 8: the box is the answer
        self.assertFalse(grade_math(r"We had 5, then doubled to get \boxed{8}", r"\boxed{5}"))


class DegenerateInputs(unittest.TestCase):

    def test_empty_string(self):
        self.assertFalse(grade_math("", r"\boxed{5}"))

    def test_none(self):
        self.assertFalse(grade_math(None, r"\boxed{5}"))

    def test_no_number_anywhere(self):
        self.assertFalse(grade_math("I am not sure how to solve this.", r"\boxed{5}"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
