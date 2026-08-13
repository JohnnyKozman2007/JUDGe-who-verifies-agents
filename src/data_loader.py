import os
import json
from datasets import load_dataset
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

RAW_DATA_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def load_math():
    print("Loading MATH dataset...")
    # MATH dataset 'dim/competition_math' only has a train split.
    ds = load_dataset('dim/competition_math', split='train')
    
    # Take a random sample of 120 with fixed seed
    sampled = ds.shuffle(seed=42).select(range(120))
    
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

def load_code():
    print("Loading HumanEval+ dataset...")
    # HumanEval+ 
    ds = load_dataset('evalplus/humanevalplus', split='test')
    
    # We only have 164 total. Sample 120.
    sampled = ds.shuffle(seed=42).select(range(120))
    
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

def load_science():
    print("Loading GPQA-Diamond dataset...")
    # GPQA Diamond requires HF Token
    token = os.environ.get("HF_TOKEN")
    ds = load_dataset('Idavidrein/gpqa', 'gpqa_diamond', split='train', token=token)
    
    # GPQA Diamond has around 198 questions. Sample 120.
    sampled = ds.shuffle(seed=42).select(range(120))
    
    standardized = []
    for i, item in enumerate(sampled):
        # Format the question as multiple choice
        question_text = item["Question"] + "\nOptions:\n"
        
        # We need to present the options randomly, but GPQA already has Incorrect Answer 1, etc.
        # So let's just present them and the correct answer. 
        # For simplicity, we just provide the question and ask for the correct answer, or present options.
        import random
        random.seed(42 + i)
        
        options = [
            item["Correct Answer"],
            item["Incorrect Answer 1"],
            item["Incorrect Answer 2"],
            item["Incorrect Answer 3"]
        ]
        random.shuffle(options)
        
        for j, opt in enumerate(options):
            question_text += f"{chr(65+j)}. {opt}\n"
            
        correct_letter = chr(65 + options.index(item["Correct Answer"]))
        
        standardized.append({
            "item_id": f"science_{i}",
            "domain": "science",
            "question": question_text,
            "ground_truth": correct_letter,
            "correct_answer_text": item["Correct Answer"]
        })
    return standardized

def save_data(data, domain):
    # Full 120
    out_path = os.path.join(RAW_DATA_DIR, f"{domain}.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    print(f"Saved {len(data)} items to {out_path}")
    
    # Pilot 10
    pilot_path = os.path.join(RAW_DATA_DIR, f"{domain}_pilot.jsonl")
    with open(pilot_path, "w", encoding="utf-8") as f:
        for item in data[:10]:
            f.write(json.dumps(item) + "\n")
    print(f"Saved 10 pilot items to {pilot_path}")

if __name__ == "__main__":
    math_data = load_math()
    save_data(math_data, "math")
    
    code_data = load_code()
    save_data(code_data, "code")
    
    science_data = load_science()
    save_data(science_data, "science")
    
    print("Data loading complete.")
