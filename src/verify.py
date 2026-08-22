import os
import sys
import json
import re
import asyncio

# Fix Unicode printing issues on Windows
sys.stdout.reconfigure(encoding='utf-8')
from models import generate_response, MODELS
from prompts import get_verification_prompt
from execution_grounding import run_candidate_code
from science_utils import (
    extract_option_map_from_question,
    parse_science_candidate_answer,
    sanitize_json_escapes,
)
from code_utils import CodeCleaner

RAW_DATA_DIR = os.path.join("data", "raw")
GEN_DATA_DIR = os.path.join("data", "generated")
VER_DATA_DIR = os.path.join("data", "verified")
os.makedirs(VER_DATA_DIR, exist_ok=True)

FRAMES = ["self", "other", "neutral"]
STRATEGIES = ["direct", "cot", "rubric"]

async def verify_candidate(item, domain, verifier_model, generator_model, candidate_answer, frame, strategy, test_code=None, entry_point=None):
    # Determine the "actual source" ownership frame context
    # If verifier_model == generator_model, actual_source = "self", else "other"
    actual_source = "self" if verifier_model == generator_model else "other"
    
    if domain == "code":
        candidate_answer = CodeCleaner.extract_code(candidate_answer)
        
    question = item["question"]
    prompt = get_verification_prompt(domain, question, candidate_answer, frame, strategy)

    candidate_answer_parse = None

    if domain == "science":
        # The parse is recorded on the output row for auditing, but deliberately NOT injected
        # into the verifier prompt. report.py grades science as
        # (parsed letter == ground truth AND not ambiguous), so showing the verifier the same
        # parse made verifier and grader agree by construction on exactly the rows where
        # extraction failed - inflating measured accuracy where the data is weakest. It also
        # carried a "mark it incorrect" directive that math's prompt has no counterpart for.
        # Math receives no such hint either, which keeps the two read-and-judge domains
        # symmetric; code's execution block differs in kind because it is real external
        # ground truth, not a regex over the candidate's own text.
        option_map = item.get("option_map") or extract_option_map_from_question(question)
        candidate_answer_parse = parse_science_candidate_answer(candidate_answer, option_map)

    execution_result = None
    if domain == "code":
        if test_code:
            # Ground the verifier in what ACTUALLY happens when the code runs, instead of
            # letting it judge correctness from a text read (which is where the ~70-90%
            # false-positive rate on wrong code was coming from - fluent-looking broken
            # code reads fine but fails immediately on execution).
            # entry_point is required: this test format defines check(candidate) but never
            # calls it - without passing entry_point, ALL code "passes" regardless of
            # correctness, since no assertion ever actually runs.
            execution_result = run_candidate_code(candidate_answer, test_code, entry_point=entry_point)

            logic_core_rule = (
                "\n\nIMPORTANT: The execution result above shows whether the code passed the given test cases. "
                "Treat this as a SIGNAL, not the final word. Passing tests does NOT guarantee the code is "
                "logically correct - the tests may not cover every edge case, and the candidate could hardcode "
                "outputs, exploit a shortcut, or use an approach that happens to satisfy these specific tests "
                "without correctly solving the general problem stated in the task. You must judge the code's "
                "LOGIC, not just whether execution passed. You have the authority to mark the candidate as "
                "incorrect even when all tests passed and no assertion failed, if you believe the underlying "
                "logic is flawed or would fail on other valid inputs not covered by these tests."
            )
            if strategy == "direct":
                # No reasoning field exists for direct - the rule still applies, it's just
                # applied silently. This is intentional, not an oversight (see note below).
                logic_override_instruction = logic_core_rule
            else:
                logic_override_instruction = logic_core_rule + " If you do this, explain why in your response's reasoning field."
            prompt = prompt + "\n\n" + execution_result.to_prompt_block() + logic_override_instruction
        else:
            print(f"WARNING: no test code found for item {item.get('item_id')} - verifying code domain WITHOUT execution grounding.")
    
    messages = [
        {"role": "system", "content": "You are an expert verifier. Always respond in valid JSON format as requested."},
        {"role": "user", "content": prompt}
    ]
    
    # We remove response_format="json_object" because some models on DeepInfra
    # inject syntax errors when forced into JSON mode. We will parse it robustly.
    res = await generate_response(
        verifier_model, 
        messages, 
        temperature=0.0, 
        max_tokens=2000, 
        retries=2
    )
    
    response_text = ""
    prompt_tokens = None
    completion_tokens = None
    latency = None
    
    if res:
        response_text = res["content"]
        prompt_tokens = res["prompt_tokens"]
        completion_tokens = res["completion_tokens"]
        latency = res["latency"]
    
    parsed = {}
    json_sanitized = False
    if response_text:
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Robust fallback parsing
            try:
                # 1. Try to extract from ```json ... ``` markdown block
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(1))
                else:
                    # 2. Try to find the first { and last }
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        clean_text = response_text[start:end+1]
                        # Fix weird edge case where model prepends {{"is_correct"
                        if clean_text.startswith("{{") and not clean_text.startswith("{\""):
                            clean_text = clean_text[1:]
                        parsed = json.loads(clean_text)
                    else:
                        print(f"Failed to parse JSON for {item['item_id']}, Model: {verifier_model}. Response: {response_text}")
            except Exception as e:
                print(f"Failed to parse JSON for {item['item_id']}, Model: {verifier_model}. Response: {response_text}")

        # 3. Science-only final tier: repair LaTeX backslashes and re-parse. GPQA answers are
        # notation-dense, so verifiers emit \( \) and \kappa inside JSON strings, which are
        # invalid escapes. Repairing recovers the whole object rather than just the verdict,
        # which keeps 'thinking' alive for the verbosity and dissociation metrics.
        # Scoped to science so math and code parsing behaviour is unchanged.
        if not parsed and domain == "science":
            try:
                parsed = json.loads(sanitize_json_escapes(response_text))
                json_sanitized = True
            except Exception:
                pass

    if not isinstance(parsed, dict):
        parsed = {}

    parsed_verdict = parsed.get("is_correct", None)

    # Did the verifier override a clean test pass on logic grounds? This is the specific
    # behavior we're now explicitly inviting - worth tracking as its own signal, separate
    # from ordinary false positives/negatives, since it shows the verifier actually reasoning
    # about logic rather than just reading the execution result off.
    overrode_passing_tests = (
        execution_result is not None
        and execution_result.ran_successfully
        and parsed_verdict is False
    )

    return {
        "item_id": item["item_id"],
        "generator_model": generator_model,
        "verifier_model": verifier_model,
        "frame": frame,
        "strategy": strategy,
        "actual_source": actual_source,
        "raw_response": response_text,
        "parsed_verdict": parsed_verdict,
        # True when strict JSON parsing failed and the escape-repair tier rescued the object.
        # Keeps the real format-compliance rate visible even though the verdict was recovered.
        "json_sanitized": json_sanitized,
        "thinking_or_evaluation": parsed.get("thinking") or parsed.get("evaluation") or parsed.get("reason"),
        "candidate_answer_letter": candidate_answer_parse.get("letter") if candidate_answer_parse else None,
        "candidate_answer_text": candidate_answer_parse.get("option_text") if candidate_answer_parse else None,
        "candidate_answer_extraction_mode": candidate_answer_parse.get("mode") if candidate_answer_parse else None,
        "candidate_answer_extraction_confidence": candidate_answer_parse.get("confidence") if candidate_answer_parse else None,
        "candidate_answer_ambiguous": candidate_answer_parse.get("ambiguous") if candidate_answer_parse else None,
        "candidate_answer_parse_notes": candidate_answer_parse.get("notes") if candidate_answer_parse else None,
        "latency": latency,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "execution_grounded": execution_result is not None,
        "execution_ran_successfully": execution_result.ran_successfully if execution_result else None,
        "execution_timed_out": execution_result.timed_out if execution_result else None,
        "overrode_passing_tests": overrode_passing_tests,
    }

async def process_domain(domain, is_pilot=True, overwrite=False):
    print(f"Starting verification for domain: {domain}")
    suffix = "_pilot.jsonl" if is_pilot else ".jsonl"
    raw_path = os.path.join(RAW_DATA_DIR, f"{domain}{suffix}")
    in_path = os.path.join(GEN_DATA_DIR, f"{domain}{suffix}")
    out_path = os.path.join(VER_DATA_DIR, f"{domain}{suffix}")
    
    if not os.path.exists(in_path):
        print(f"File not found: {in_path}")
        return

    # Raw items carry the ground-truth test harness (item['test']) needed for
    # execution-grounded code verification. Missing raw file degrades gracefully
    # to ungrounded verification (with a warning per item) rather than crashing.
    raw_dict = {}
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            for line in f:
                raw_item = json.loads(line)
                raw_dict[raw_item["item_id"]] = raw_item
    elif domain == "code":
        print(f"WARNING: raw file not found at {raw_path} - code verification will run WITHOUT execution grounding.")
        
    items = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
            
    processed_keys = set()
    if os.path.exists(out_path):
        if overwrite:
            os.remove(out_path)
            print(f"Deleted {out_path} and starting fresh.")
        else:
            with open(out_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        k = (
                            data["item_id"],
                            data["generator_model"],
                            data["verifier_model"],
                            data["frame"],
                            data["strategy"]
                        )
                        processed_keys.add(k)
                    except Exception:
                        pass
    
    if processed_keys:
        print(f"Found {len(processed_keys)} already processed verifications.")
    
    # We want to run 3 x 3 x 3 x 3 = 81 calls per question
    model_names = list(MODELS.keys())
    batch_size = 10 # concurrent verification calls
    
    tasks = []
    
    # First, collect all pending tasks
    for item in items:
        raw_item = raw_dict.get(item["item_id"])
        test_code = raw_item.get("test") if (raw_item and domain == "code") else None
        entry_point = raw_item.get("entry_point") if (raw_item and domain == "code") else None
        for verifier_model in model_names:
            for generator_model, candidate_answer in item["candidates"].items():
                if not candidate_answer:
                    # Skip if generator failed
                    continue
                for frame in FRAMES:
                    for strategy in STRATEGIES:
                        k = (item["item_id"], generator_model, verifier_model, frame, strategy)
                        if k not in processed_keys:
                            tasks.append(
                                verify_candidate(item, domain, verifier_model, generator_model, candidate_answer, frame, strategy, test_code=test_code, entry_point=entry_point)
                            )
                            
    print(f"Total pending verifications to run: {len(tasks)}")
    
    if not tasks:
        print(f"Finished {domain}. All verifications already complete.")
        return
        
    # Run tasks in batches and save incrementally
    with open(out_path, "a", encoding="utf-8") as f:
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            batch_results = await asyncio.gather(*batch)
            
            for v in batch_results:
                f.write(json.dumps(v) + "\n")
            f.flush()
            
            print(f"Processed {min(i+batch_size, len(tasks))} / {len(tasks)} verifications...")

    print(f"Finished {domain}.")

async def main(is_pilot=True, domains=None, overwrite=False):
    if domains is None:
        domains = ["math", "code", "science"]
    for domain in domains:
        await process_domain(domain, is_pilot=is_pilot, overwrite=overwrite)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot")
    parser.add_argument("--domain", type=str, choices=["all", "math", "code", "science"], default="all")
    parser.add_argument("--overwrite", action="store_true", help="Delete existing output and start fresh")
    args = parser.parse_args()

    is_pilot = args.mode == "pilot"
    domains = ["math", "code", "science"] if args.domain == "all" else [args.domain]
    
    asyncio.run(main(is_pilot=is_pilot, domains=domains, overwrite=args.overwrite))
