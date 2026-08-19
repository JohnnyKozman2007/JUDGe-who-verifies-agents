"""
validate_overrides.py

Runs automatically as Step 4 of the pipeline (added to run.py). No LLM calls, no cost -
pure local Python. It looks at what verify.py already produced and checks two things:

1. Cases where the code passed the real test, but the verifier said "incorrect" anyway.
   -> Runs the fuzz test (candidate vs ground_truth reference, random inputs) to check
      if that was a real catch or a false alarm.

2. Cases where the code failed the real test, but the verifier said "correct" anyway.
   -> No fuzzing needed, the test already proved it's broken. Just save the case so you
      can read why the verifier missed it.

Resumable, like verify.py: if you run this again, it only processes new cases it hasn't
seen before. Safe to run even if you skipped re-generating or re-verifying.
"""

import os
import json
from execution_grounding import run_candidate_code
from fuzz_validate import differential_test

RAW_DATA_DIR = os.path.join("data", "raw")
GEN_DATA_DIR = os.path.join("data", "generated")
VER_DATA_DIR = os.path.join("data", "verified")
OUT_DIR = os.path.join("data", "validated")
os.makedirs(OUT_DIR, exist_ok=True)


def _load_jsonl(path):
    rows = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def _already_done(path):
    """Same resume pattern as verify.py - key on the same 5-tuple that identifies a unique case."""
    done = set()
    if os.path.exists(path):
        for row in _load_jsonl(path):
            done.add((row["item_id"], row["generator_model"], row["verifier_model"], row["frame"], row["strategy"]))
    return done


async def process_domain(domain="code", is_pilot=True):
    if domain != "code":
        return  # only code has execution-checkable ground truth to compare against

    suffix = "_pilot.jsonl" if is_pilot else ".jsonl"
    raw_items = {r["item_id"]: r for r in _load_jsonl(os.path.join(RAW_DATA_DIR, f"{domain}{suffix}"))}
    gen_items = {r["item_id"]: r for r in _load_jsonl(os.path.join(GEN_DATA_DIR, f"{domain}{suffix}"))}
    verified_rows = _load_jsonl(os.path.join(VER_DATA_DIR, f"{domain}{suffix}"))

    if not verified_rows:
        print(f"No verified data found for {domain} yet - nothing to validate.")
        return

    overrides_path = os.path.join(OUT_DIR, f"{domain}_overrides{suffix}")
    missed_path = os.path.join(OUT_DIR, f"{domain}_missed_failures{suffix}")

    done_overrides = _already_done(overrides_path)
    done_missed = _already_done(missed_path)
    had_prior_data = bool(done_overrides or done_missed)

    new_overrides = 0
    new_missed = 0

    with open(overrides_path, "a", encoding="utf-8") as f_over, \
         open(missed_path, "a", encoding="utf-8") as f_missed:

        for row in verified_rows:
            key = (row["item_id"], row["generator_model"], row["verifier_model"], row["frame"], row["strategy"])
            raw_item = raw_items.get(row["item_id"])
            gen_item = gen_items.get(row["item_id"])
            if raw_item is None or gen_item is None:
                continue

            candidate_code = gen_item.get("candidates", {}).get(row["generator_model"])
            test_code = raw_item.get("test")
            entry_point = raw_item.get("entry_point")
            ground_truth = raw_item.get("ground_truth")
            question = raw_item.get("question", "")
            if not (candidate_code and test_code and entry_point):
                continue

            execution_passed = row.get("execution_ran_successfully")
            verifier_said_correct = row.get("parsed_verdict")
            if execution_passed is None or verifier_said_correct is None:
                continue  # ungrounded or unparsed row, nothing to compare

            # --- Case 1: test passed, verifier said incorrect (override) ---
            if execution_passed is True and verifier_said_correct is False:
                if key in done_overrides:
                    continue
                fuzz_result = await differential_test(
                    item_id=row["item_id"], candidate_code=candidate_code,
                    reference_code=ground_truth, entry_point=entry_point, question=question,
                )
                record = {
                    "item_id": row["item_id"],
                    "generator_model": row["generator_model"],
                    "verifier_model": row["verifier_model"],
                    "frame": row["frame"],
                    "strategy": row["strategy"],
                    "candidate_code": candidate_code,
                    "verifier_reasoning": row.get("thinking_or_evaluation"),
                    "fuzz_verdict": fuzz_result.verdict,
                    "fuzz_num_trials": fuzz_result.num_trials,
                    "fuzz_note": fuzz_result.note,
                    "fuzz_mismatches": [
                        {"inputs": t.inputs, "candidate_result": t.candidate_result,
                         "reference_result": t.reference_result,
                         "candidate_error": t.candidate_error, "reference_error": t.reference_error}
                        for t in fuzz_result.trials if not t.match
                    ],
                }
                f_over.write(json.dumps(record) + "\n")
                new_overrides += 1

            # --- Case 2: test failed, verifier said correct (missed failure) ---
            elif execution_passed is False and verifier_said_correct is True:
                if key in done_missed:
                    continue
                exec_result = run_candidate_code(candidate_code, test_code, entry_point=entry_point)
                record = {
                    "item_id": row["item_id"],
                    "generator_model": row["generator_model"],
                    "verifier_model": row["verifier_model"],
                    "frame": row["frame"],
                    "strategy": row["strategy"],
                    "candidate_code": candidate_code,
                    "verifier_reasoning": row.get("thinking_or_evaluation"),
                    "actual_execution_error": exec_result.traceback_summary or exec_result.stderr,
                }
                f_missed.write(json.dumps(record) + "\n")
                new_missed += 1

    if new_overrides == 0 and new_missed == 0 and not had_prior_data:
        print(f"[{domain}] No disagreement cases found - nothing to validate.")
    else:
        if not had_prior_data:
            print(f"[{domain}] First run - this hadn't been validated before. Processing now.")
        print(f"[{domain}] Validated {new_overrides} new override case(s) -> {overrides_path}")
        print(f"[{domain}] Logged {new_missed} new missed-failure case(s) -> {missed_path}")
        if new_overrides == 0 and new_missed == 0:
            print(f"[{domain}] Already up to date - nothing new since last run.")


async def main(is_pilot=True, domains=None):
    if domains is None:
        domains = ["math", "code", "science"]
    for domain in domains:
        await process_domain(domain, is_pilot=is_pilot)


if __name__ == "__main__":
    import argparse
    import asyncio
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot")
    parser.add_argument("--domain", type=str, choices=["all", "math", "code", "science"], default="all")
    args = parser.parse_args()

    is_pilot = args.mode == "pilot"
    domains = ["math", "code", "science"] if args.domain == "all" else [args.domain]
    asyncio.run(main(is_pilot=is_pilot, domains=domains))
