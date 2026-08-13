import os
import sys
import json
import re
import asyncio

# Fix Unicode printing issues on Windows
sys.stdout.reconfigure(encoding='utf-8')
from models import generate_response, MODELS
from prompts import get_verification_prompt
import traceback

GEN_DATA_DIR = os.path.join("data", "generated")
VER_DATA_DIR = os.path.join("data", "verified")
os.makedirs(VER_DATA_DIR, exist_ok=True)

FRAMES = ["self", "other", "neutral"]
STRATEGIES = ["direct", "cot", "rubric"]

async def verify_candidate(item, domain, verifier_model, generator_model, candidate_answer, frame, strategy):
    # Determine the "actual source" ownership frame context
    # If verifier_model == generator_model, actual_source = "self", else "other"
    actual_source = "self" if verifier_model == generator_model else "other"
    
    question = item["question"]
    prompt = get_verification_prompt(domain, question, candidate_answer, frame, strategy)
    
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
                
    return {
        "item_id": item["item_id"],
        "generator_model": generator_model,
        "verifier_model": verifier_model,
        "frame": frame,
        "strategy": strategy,
        "actual_source": actual_source,
        "raw_response": response_text,
        "parsed_verdict": parsed.get("is_correct", None),
        "thinking_or_evaluation": parsed.get("thinking") or parsed.get("evaluation"),
        "latency": latency,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
    }

async def process_domain(domain, is_pilot=True):
    print(f"Starting verification for domain: {domain}")
    suffix = "_pilot.jsonl" if is_pilot else ".jsonl"
    in_path = os.path.join(GEN_DATA_DIR, f"{domain}{suffix}")
    out_path = os.path.join(VER_DATA_DIR, f"{domain}{suffix}")
    
    if not os.path.exists(in_path):
        print(f"File not found: {in_path}")
        return
        
    items = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
            
    processed_keys = set()
    if os.path.exists(out_path):
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
    
    print(f"Found {len(processed_keys)} already processed verifications.")
    
    # We want to run 3 x 3 x 3 x 3 = 81 calls per question
    model_names = list(MODELS.keys())
    batch_size = 10 # concurrent verification calls
    
    tasks = []
    
    # First, collect all pending tasks
    for item in items:
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
                                verify_candidate(item, domain, verifier_model, generator_model, candidate_answer, frame, strategy)
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

async def main():
    domains = ["math", "code", "science"]
    for domain in domains:
        await process_domain(domain, is_pilot=True)

if __name__ == "__main__":
    asyncio.run(main())
