"""
execution_grounding.py

Fixes the code-domain verifier problem: verifiers were judging code by reading it
("does this look right?") instead of by running it. Reading is where the ~70-90%
false-positive rate on wrong code comes from - fluent-looking broken code passes a
text read easily but fails execution immediately.

This module runs the candidate code for real and packages the actual output/error/
traceback into a block you inject into the verifier prompt, turning the task into
"here's what happened when we ran it, does that match the spec" - a much more
grounded, mechanical judgment than eyeballing code for plausibility.

Drop this into your verification pipeline (the script that builds prompts and calls
the verifier LLM - not report.py, which only analyzes results after the fact).
"""

import subprocess
import tempfile
import os
import sys
import re
from dataclasses import dataclass, asdict
from typing import Optional


def _strip_markdown_fences(code: str) -> str:
    """Remove ```python ... ``` wrapping if present."""
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # drop closing fence
        return "\n".join(lines)
    return code


@dataclass
class ExecutionResult:
    ran_successfully: bool          # did the process exit 0 with no crash?
    stdout: str                     # captured stdout, truncated
    stderr: str                     # captured stderr, truncated
    traceback_summary: Optional[str]  # last traceback frame + exception line, if any
    timed_out: bool
    tests_passed: Optional[int] = None   # if test_code uses plain `assert`, count passed
    tests_total: Optional[int] = None    # count of assert statements found in test_code

    def to_prompt_block(self) -> str:
        """Render as a clean block to inject directly into a verifier prompt."""
        if self.timed_out:
            return "[EXECUTION RESULT]\nThe code timed out and did not complete. This usually means an infinite loop, unbounded recursion, or a hang."

        lines = ["[EXECUTION RESULT]"]
        lines.append(f"Exit status: {'SUCCESS (exit code 0)' if self.ran_successfully else 'FAILED (non-zero exit / exception)'}")

        if self.tests_total is not None:
            passed = self.tests_passed if self.tests_passed is not None else 0
            lines.append(f"Assertions: {passed}/{self.tests_total} passed")

        if self.stdout.strip():
            lines.append(f"STDOUT:\n{self.stdout.strip()[:1500]}")
        else:
            lines.append("STDOUT: (empty)")

        if not self.ran_successfully:
            if self.traceback_summary:
                lines.append(f"ERROR (actual exception raised):\n{self.traceback_summary}")
            elif self.stderr.strip():
                lines.append(f"STDERR:\n{self.stderr.strip()[:1500]}")

        return "\n".join(lines)


def _extract_traceback_summary(stderr: str, max_chars: int = 800) -> Optional[str]:
    """
    Pull the most useful part of a Python traceback: the final 'File ... line ...' frame
    plus the exception type/message line. Full tracebacks are noisy for a judge prompt;
    the last frame + exception line is almost always what actually matters.
    """
    if not stderr.strip():
        return None
    lines = stderr.strip().splitlines()
    # Exception line is virtually always the last non-empty line of a Python traceback
    exception_line = lines[-1] if lines else ""
    # Find the last "File ..., line ..." frame for location context
    file_frames = [l for l in lines if l.strip().startswith("File ")]
    last_frame = file_frames[-1].strip() if file_frames else ""
    summary = "\n".join(x for x in [last_frame, exception_line] if x)
    return summary[:max_chars] if summary else stderr[:max_chars]


def _count_assertions(test_code: str) -> int:
    """Rough count of top-level assert statements in the test harness, for pass/fail tallying."""
    return len(re.findall(r'^\s*assert\b', test_code, flags=re.MULTILINE))


def run_candidate_code(candidate_text: str, test_code: str, entry_point: Optional[str] = None, timeout: int = 5) -> ExecutionResult:
    """
    Actually executes candidate_text + test_code (same sandboxing approach as
    report.py's grade_code) and returns a full ExecutionResult instead of a bare bool.

    entry_point: REQUIRED for HumanEval+-style harnesses, where test_code defines a
    `check(candidate)` function but never calls it - candidate_text's function name
    (item['entry_point']). Without this, the script just defines functions and exits
    0 regardless of correctness, since no assertion ever actually runs. If your
    test_code format already calls its own assertions directly (plain `assert` style),
    leave entry_point=None.

    NOTE on sandboxing: this runs via subprocess with a timeout, same as the existing
    grading harness - fine for known benchmark code (HumanEval+ etc). If candidate
    code source expands beyond curated benchmarks, consider adding resource limits
    (e.g. via `resource` module or a container) since this executes arbitrary LLM output.
    """
    if not candidate_text:
        return ExecutionResult(False, "", "", None, False, None, None)

    candidate_text = _strip_markdown_fences(candidate_text)

    full_source = candidate_text + "\n\n" + test_code
    if entry_point:
        full_source += f"\ncheck({entry_point})\n"
    tests_total = _count_assertions(test_code)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(full_source)
        tmp_name = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_name],
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding='utf-8'
        )
        ran_successfully = (result.returncode == 0)
        traceback_summary = None if ran_successfully else _extract_traceback_summary(result.stderr)

        # If the harness uses plain asserts, an AssertionError tells us at least one failed;
        # exact pass count isn't recoverable from a single crashing process, so report
        # "at least one failed" rather than fabricating a precise count.
        tests_passed = tests_total if ran_successfully else None

        return ExecutionResult(
            ran_successfully=ran_successfully,
            stdout=result.stdout,
            stderr=result.stderr,
            traceback_summary=traceback_summary,
            timed_out=False,
            tests_passed=tests_passed,
            tests_total=tests_total if tests_total > 0 else None,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(False, "", "", None, True, None, tests_total if tests_total > 0 else None)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


if __name__ == "__main__":
    # Quick demo
    candidate = "def add(a, b):\n    return a - b  # bug: should be +"
    tests = "assert add(2, 3) == 5\nassert add(-1, 1) == 0"
    result = run_candidate_code(candidate, tests)
    print(result.to_prompt_block())

