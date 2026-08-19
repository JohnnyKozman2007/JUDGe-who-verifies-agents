import os
import json
import asyncio
from models import generate_response, MODELS
from prompts import get_generation_prompt

RAW_DATA_DIR = os.path.join("data", "raw")
GEN_DATA_DIR = os.path.join("data", "generated")
os.makedirs(GEN_DATA_DIR, exist_ok=True)

async def generate_for_item(item, domain):
    question = item["question"]
    prompt = get_generation_prompt(domain, question)
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    tasks = []
    # Qwen, DeepSeek, Llama, Mistral
    model_names = list(MODELS.keys())
    for model in model_names:
        # temperature=0.0 for deterministic, reproducible generation.
        tasks.append(generate_response(model, messages, temperature=0.0, max_tokens=2000))
        
    results = await asyncio.gather(*tasks)
    
    item["candidates"] = {}
    item["generation_meta"] = {}
    for model, res in zip(model_names, results):
        if res is not None:
            item["candidates"][model] = res["content"]
            item["generation_meta"][model] = {
                "latency": res["latency"],
                "prompt_tokens": res["prompt_tokens"],
                "completion_tokens": res["completion_tokens"]
            }
        else:
            item["candidates"][model] = None
            item["generation_meta"][model] = None
        
    return item

async def process_domain(domain, is_pilot=True, overwrite=False):
    print(f"Starting generation for domain: {domain}")
    suffix = "_pilot.jsonl" if is_pilot else ".jsonl"
    in_path = os.path.join(RAW_DATA_DIR, f"{domain}{suffix}")
    out_path = os.path.join(GEN_DATA_DIR, f"{domain}{suffix}")
    
    if not os.path.exists(in_path):
        print(f"File not found: {in_path}")
        return
        
    items = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
            
    processed_ids = set()
    if os.path.exists(out_path):
        if overwrite:
            os.remove(out_path)
            print(f"Deleted {out_path} and starting fresh.")
        else:
            with open(out_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        processed_ids.add(json.loads(line)["item_id"])
                    except Exception:
                        pass
                    
    items_to_process = [item for item in items if item["item_id"] not in processed_ids]
    if processed_ids:
        print(f"Found {len(processed_ids)} already processed items. {len(items_to_process)} left to process.")
    
    if not items_to_process:
        print(f"Finished {domain}. All items already generated.")
        return
            
    # Process concurrently in batches to avoid overwhelming the API
    batch_size = 5
    
    with open(out_path, "a", encoding="utf-8") as f:
        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            tasks = [generate_for_item(item, domain) for item in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for item_res in batch_results:
                f.write(json.dumps(item_res) + "\n")
            f.flush()
            print(f"Processed {min(i+batch_size, len(items_to_process))} / {len(items_to_process)} remaining items...")
            
    print(f"Finished {domain}. Saved to {out_path}")

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
