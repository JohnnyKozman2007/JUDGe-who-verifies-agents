"""
fuzz_validate.py

LLM-guided differential testing engine for the code domain. 
Given a candidate function and a ground-truth reference function (both Python source), 
uses an LLM to generate targeted adversarial inputs, then runs both on those inputs 
and checks whether they produce identical outputs.

Used by validate_overrides.py (Step 4) to decide:
  - Override was a false alarm (100% agreement across trials) -> NO_DISCREPANCY
  - Override was justified (any mismatch found)                -> BUG_CONFIRMED
  - Couldn't generate valid inputs for this function           -> SKIPPED_TYPE_INFERENCE_FAILED
"""

import re
import json
import subprocess
import tempfile
import os
import sys
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional

from models import generate_response
from code_utils import CodeCleaner

# ---------------------------------------------------------------------------
# Data structures returned to validate_overrides.py
# ---------------------------------------------------------------------------

@dataclass
class TrialResult:
    inputs: list              # the generated arguments
    candidate_result: str     # repr of candidate return value (or None)
    reference_result: str     # repr of reference return value (or None)
    candidate_error: Optional[str]   # exception text if candidate crashed
    reference_error: Optional[str]   # exception text if reference crashed
    match: bool               # did both produce the same result?


@dataclass
class FuzzResult:
    verdict: str              # BUG_CONFIRMED | NO_DISCREPANCY | SKIPPED_TYPE_INFERENCE_FAILED
    num_trials: int           # how many input sets were actually run
    note: str                 # human-readable explanation
    trials: List[TrialResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt for LLM Input Generation
# ---------------------------------------------------------------------------

def _build_generation_prompt(question: str, candidate_code: str, reference_code: str) -> str:
    return f"""You are an adversarial test generator for Python code.

PROBLEM DESCRIPTION:
{question}

CANDIDATE CODE:
```python
{candidate_code}
```

REFERENCE CODE:
```python
{reference_code}
```

TASK:
The candidate code might have a subtle bug (e.g. an off-by-one error, wrong boundary check, etc) compared to the correct reference code. 
Generate 15 highly targeted test cases specifically designed to expose discrepancies between these two implementations.
Focus heavily on edge cases, boundary values, empty inputs, 0, 1, -1, and exactly hitting constraints (like x == threshold).

OUTPUT FORMAT:
Return ONLY a valid JSON array of arrays. Each inner array represents the positional arguments to pass to the function.
Example:
[
  [[1, 2, 3], 3],
  [[], 0],
  [[10, 10, 10], 10]
]
Do not output any markdown formatting, explanations, or python code. Just the JSON array.
"""

async def _ask_oracle(question: str, inputs: list, cand_result: str, ref_result: str) -> str:
    prompt = f"""You are an expert Python judge. Here is a problem description:
{question}

Two implementations were run on the following test input:
Input: {inputs}

Implementation A returned: {cand_result}
Implementation B returned: {ref_result}

According to the problem description, which implementation produced the strictly correct output?
Answer with exactly one word: 'A', 'B', or 'NEITHER'."""

    messages = [
        {"role": "system", "content": "You are a code execution oracle. Answer with exactly one word."},
        {"role": "user", "content": prompt}
    ]
    
    res = await generate_response(
        model_name="microsoft/WizardLM-2-8x22B",
        messages=messages,
        temperature=0.0,
        max_tokens=10
    )
    
    if not res or not res.get("content"):
        return "SKIPPED_PIPELINE_FAIL"
        
    content = res["content"].strip().upper()
    if "A" in content and "B" not in content and "NEITHER" not in content:
        return "A"
    if "B" in content and "A" not in content and "NEITHER" not in content:
        return "B"
    if "NEITHER" in content:
        return "NEITHER"
        
    match = re.search(r'\b(A|B|NEITHER)\b', content)
    if match:
        return match.group(1)
        
    return "SKIPPED_PIPELINE_FAIL"

# ---------------------------------------------------------------------------
# Harness script template - runs both functions, compares results
# ---------------------------------------------------------------------------

_HARNESS_TEMPLATE = '''
import json
import sys
import inspect
import multiprocessing

# --- Load candidate and reference code ---
{candidate_code}

{reference_code_renamed}

def _worker_cand(args, q):
    try:
        res = repr({entry_point}(*args))
        q.put((res, None))
    except Exception as e:
        q.put((None, type(e).__name__ + ": " + str(e)))

def _worker_ref(args, q):
    try:
        res = repr(__ref_{entry_point}(*args))
        q.put((res, None))
    except Exception as e:
        q.put((None, type(e).__name__ + ": " + str(e)))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    INPUTS = {inputs_json}
    results = []
    
    try:
        sig = inspect.signature({entry_point})
        takes_one_arg = len(sig.parameters) == 1
    except Exception:
        takes_one_arg = False

    for args in INPUTS:
        call_args = [args] if takes_one_arg and isinstance(args, list) else args
        
        cand_result, cand_error = None, None
        ref_result, ref_error = None, None
        
        q_cand = multiprocessing.Queue()
        p_cand = multiprocessing.Process(target=_worker_cand, args=(call_args, q_cand))
        p_cand.start()
        
        q_ref = multiprocessing.Queue()
        p_ref = multiprocessing.Process(target=_worker_ref, args=(call_args, q_ref))
        p_ref.start()
        
        p_cand.join(2.0)
        if p_cand.is_alive():
            p_cand.terminate()
            p_cand.join()
            cand_error = "TimeoutError: execution exceeded 2.0s"
        else:
            if not q_cand.empty():
                cand_result, cand_error = q_cand.get()
            else:
                cand_error = "ProcessCrash: candidate process died unexpectedly"
                
        p_ref.join(2.0)
        if p_ref.is_alive():
            p_ref.terminate()
            p_ref.join()
            ref_error = "TimeoutError: execution exceeded 2.0s"
        else:
            if not q_ref.empty():
                ref_result, ref_error = q_ref.get()
            else:
                ref_error = "ProcessCrash: reference process died unexpectedly"

        if cand_error and ref_error:
            if "TimeoutError" in cand_error and "TimeoutError" in ref_error:
                match = True
            else:
                match = cand_error.split(":")[0] == ref_error.split(":")[0]
        elif cand_error or ref_error:
            match = False
        else:
            match = (cand_result == ref_result)

        results.append({{
            "inputs": args,
            "candidate_result": cand_result,
            "reference_result": ref_result,
            "candidate_error": cand_error,
            "reference_error": ref_error,
            "match": match,
        }})

    print(json.dumps(results))
'''


def _rename_reference(reference_code: str, entry_point: str) -> str:
    """
    Rename the entry_point function in the reference code to __ref_<entry_point>
    so both candidate and reference can coexist in the same script without collision.
    """
    renamed = re.sub(
        rf'\bdef\s+{re.escape(entry_point)}\s*\(',
        f'def __ref_{entry_point}(',
        reference_code
    )
    renamed = re.sub(
        rf'\b{re.escape(entry_point)}\s*\(',
        f'__ref_{entry_point}(',
        renamed
    )
    return renamed


async def differential_test(
    item_id: str,
    candidate_code: str,
    reference_code: str,
    entry_point: str,
    question: str = "",
    timeout: int = 60,
) -> FuzzResult:
    """
    Run candidate_code vs reference_code on LLM-generated inputs and compare outputs.
    """
    candidate_code = CodeCleaner.extract_code(candidate_code)
    if not reference_code or not reference_code.strip():
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note="No ground-truth reference code provided.",
        )
        
    # Step 1: Use LLM to generate adversarial inputs
    prompt = _build_generation_prompt(question, candidate_code, reference_code)
    messages = [
        {"role": "system", "content": "You are a test case generator. Output strictly valid JSON arrays."},
        {"role": "user", "content": prompt}
    ]
    
    res = await generate_response(
        model_name="google/gemma-2-27b-it", # Independent model outside the 4 being evaluated
        messages=messages,
        temperature=0.2,
        max_tokens=2000
    )
    
    if not res or not res.get("content"):
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note="LLM failed to generate test inputs.",
        )
        
    # Clean up output in case it wrapped it in markdown
    content = res["content"].strip()
    match = re.search(r'\[\s*\[.*\]\s*\]', content, re.DOTALL)
    if match:
        content = match.group(0)
        
    try:
        inputs = json.loads(content)
        if not isinstance(inputs, list):
            raise ValueError("Root element is not a list")
    except (json.JSONDecodeError, ValueError) as e:
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note=f"LLM generated invalid JSON inputs: {e} -> {content[:100]}...",
        )
        
    if not inputs:
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note="LLM generated an empty list of inputs.",
        )

    # Step 2: prepare reference code (HumanEval ground truth often lacks the def header)
    full_reference = reference_code
    if not re.search(rf'\bdef\s+{re.escape(entry_point)}\s*\(', reference_code):
        full_reference = question + "\n" + reference_code
        
    reference_renamed = _rename_reference(full_reference, entry_point)

    # Step 3: assemble and run the harness
    harness = _HARNESS_TEMPLATE.format(
        inputs_json=json.dumps(inputs),
        candidate_code=candidate_code,
        reference_code_renamed=reference_renamed,
        entry_point=entry_point,
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(harness)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip()[-500:] if result.stderr else "unknown error"
            return FuzzResult(
                verdict="SKIPPED_PIPELINE_FAIL",
                num_trials=0,
                note=f"Harness crashed: {error_msg}",
            )

        raw_results = json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note=f"Differential test timed out after {timeout}s (likely infinite loop).",
        )
    except (json.JSONDecodeError, ValueError) as e:
        return FuzzResult(
            verdict="SKIPPED_PIPELINE_FAIL",
            num_trials=0,
            note=f"Could not parse harness output: {e}\nOutput was: {result.stdout[:200]}",
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Step 4: build trial results and decide verdict
    trials = []
    for r in raw_results:
        trials.append(TrialResult(
            inputs=r["inputs"],
            candidate_result=r["candidate_result"],
            reference_result=r["reference_result"],
            candidate_error=r["candidate_error"],
            reference_error=r["reference_error"],
            match=r["match"],
        ))

    mismatches = [t for t in trials if not t.match]
    # NOTE: We only check the first mismatch here, assuming it's representative
    if mismatches:
        t = mismatches[0]
        oracle_answer = await _ask_oracle(question, t.inputs, t.candidate_result, t.reference_result)
        
        if oracle_answer == "A":
            verdict = "REFERENCE_BUG"
            note = f"Oracle overrode! Candidate correct on {t.inputs}."
        elif oracle_answer == "B":
            verdict = "BUG_CONFIRMED"
            note = f"Oracle confirmed bug on {t.inputs}."
        elif oracle_answer == "NEITHER":
            verdict = "BUG_CONFIRMED"
            note = f"Oracle says both are wrong on {t.inputs}."
        else:
            verdict = "SKIPPED_PIPELINE_FAIL"
            note = f"Oracle failed to respond properly."
    else:
        verdict = "NO_DISCREPANCY"
        note = f"All {len(trials)} trials matched between candidate and reference."

    return FuzzResult(
        verdict=verdict,
        num_trials=len(trials),
        note=note,
        trials=trials,
    )
