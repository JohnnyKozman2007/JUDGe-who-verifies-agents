import os
import json
from datasets import load_dataset
import pandas as pd
from dotenv import load_dotenv
from science_utils import build_option_map, render_science_question, validate_science_options

load_dotenv()

RAW_DATA_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def load_math(mode):
    print("Loading MATH dataset...")
    # MATH dataset 'dim/competition_math' only has a train split.
    ds = load_dataset('dim/competition_math', split='train')
    
    num_samples = 10 if mode == "pilot" else 150
    sampled = ds.shuffle(seed=42).select(range(num_samples))
    
    # Convert to standard format
    standardized = []
    for i, item in enumerate(sampled):
        standardized.append({
            "item_id": f"math_{i}",
            "domain": "math",
            "question": item["problem"],
            "ground_truth": item["solution"]
        })
    return standardized

def load_code(mode):
    print("Loading HumanEval+ dataset...")
    # HumanEval+ 
    ds = load_dataset('evalplus/humanevalplus', split='test')
    
    num_samples = 10 if mode == "pilot" else 150
    sampled = ds.shuffle(seed=42).select(range(num_samples))
    
    standardized = []
    for i, item in enumerate(sampled):
        standardized.append({
            "item_id": f"code_{item['task_id'].replace('/', '_')}",
            "domain": "code",
            "question": item["prompt"],
            "entry_point": item["entry_point"],
            "test": item["test"],
            "ground_truth": item["canonical_solution"]
        })
    return standardized

def load_science(mode):
    print("Loading GPQA-Diamond dataset...")
    # GPQA Diamond requires HF Token
    token = os.environ.get("HF_TOKEN")
    ds = load_dataset('Idavidrein/gpqa', 'gpqa_diamond', split='train', token=token)
    
    num_samples = 10 if mode == "pilot" else 150
    sampled = ds.shuffle(seed=42)
    
    standardized = []
    skipped = []
    for item in sampled:
        if len(standardized) >= num_samples:
            break

        import random
        random.seed(42 + len(standardized))
        
        options = [
            item["Correct Answer"],
            item["Incorrect Answer 1"],
            item["Incorrect Answer 2"],
            item["Incorrect Answer 3"]
        ]
        random.shuffle(options)

        issues = validate_science_options(options)
        if issues:
            skipped.append({"question": item["Question"][:80], "issues": issues})
            continue

        question_text = render_science_question(item["Question"], options)
        correct_letter = chr(65 + options.index(item["Correct Answer"]))
        option_map = build_option_map(options)
        
        standardized.append({
            "item_id": f"science_{len(standardized)}",
            "domain": "science",
            "question_stem": item["Question"],
            "question": question_text,
            "ground_truth": correct_letter,
            "correct_answer_text": item["Correct Answer"],
            "option_map": option_map,
            "options": [option_map[chr(65 + idx)] for idx in range(4)],
            "source_dataset": "Idavidrein/gpqa:gpqa_diamond",
        })

    if len(standardized) < num_samples:
        raise RuntimeError(
            f"Could only prepare {len(standardized)} valid science items out of requested {num_samples}. "
            f"Skipped {len(skipped)} malformed items."
        )

    if skipped:
        print(f"Skipped {len(skipped)} malformed GPQA items while building the science split.")
    return standardized

def save_data(data, domain, mode):
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    out_path = os.path.join(RAW_DATA_DIR, f"{domain}{suffix}")
    
    # Check existing items for resume support
    existing_ids = set()
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    existing_ids.add(json.loads(line)["item_id"])
                except Exception:
                    pass
    
    new_items = [item for item in data if item["item_id"] not in existing_ids]
    
    if not new_items:
        print(f"Already have {len(existing_ids)} items for {domain} in {out_path}. Nothing to add.")
        return
    
    with open(out_path, "a", encoding="utf-8") as f:
        for item in new_items:
            f.write(json.dumps(item) + "\n")
    print(f"Added {len(new_items)} new items to {out_path} (total: {len(existing_ids) + len(new_items)})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot")
    parser.add_argument("--domain", type=str, choices=["all", "math", "code", "science"], default="all")
    args = parser.parse_args()

    domains = ["math", "code", "science"] if args.domain == "all" else [args.domain]
    
    for domain in domains:
        if domain == "math":
            data = load_math(args.mode)
        elif domain == "code":
            data = load_code(args.mode)
        elif domain == "science":
            data = load_science(args.mode)
        save_data(data, domain, args.mode)
    
    print("Data loading complete.")
