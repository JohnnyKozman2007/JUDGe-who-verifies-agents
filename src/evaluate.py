import os
import json
import ast
import pandas as pd
from collections import defaultdict
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

VER_DATA_DIR = os.path.join("data", "verified")

# We will need a way to determine the objective correctness of the candidate answer.
# For GPQA (science), we can just check if the model selected the correct option letter.
# For Code, we would theoretically run the evalplus test suite against the code.
# For Math, we check if the ground truth is in the response.

# For now, this is a placeholder evaluation script that calculates metrics assuming
# we have a `candidate_correct` boolean.

def compute_metrics(y_true, y_pred):
    if len(y_true) == 0:
        return {}
    
    acc = accuracy_score(y_true, y_pred)
    # Handle single class scenarios
    if len(set(y_true)) == 1:
        p = accuracy_score(y_true, y_pred) # Simplified
        r = p
        f1 = p
        tn, fp, fn, tp = 0, 0, 0, 0
        if y_true[0]:
            tp = sum(y_pred)
            fn = len(y_true) - tp
        else:
            tn = len(y_true) - sum(y_pred)
            fp = sum(y_pred)
    else:
        p = precision_score(y_true, y_pred, zero_division=0)
        r = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    return {
        "accuracy": acc,
        "precision": p,
        "recall": r,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr
    }

def process_results(domain, is_pilot=True):
    suffix = "_pilot.jsonl" if is_pilot else ".jsonl"
    in_path = os.path.join(VER_DATA_DIR, f"{domain}{suffix}")
    
    if not os.path.exists(in_path):
        return
        
    results = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
            
    df = pd.DataFrame(results)
    if df.empty:
        return
        
    print(f"\n--- Metrics for {domain} ---")
    
    # We don't have true 'candidate_correct' yet without executing tests/evaluators.
    # So we'll skip actual metric computation for now until ground truth grading is implemented.
    print(f"Total verifications run: {len(df)}")
    
    # Group by frame, strategy, verifier_model
    summary = df.groupby(["verifier_model", "frame", "strategy"])["parsed_verdict"].value_counts(dropna=False).unstack().fillna(0)
    print(summary)
    
if __name__ == "__main__":
    for domain in ["math", "code", "science"]:
        process_results(domain, is_pilot=True)
