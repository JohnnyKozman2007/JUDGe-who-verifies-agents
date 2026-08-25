import json
import os
import asyncio
import pandas as pd
import sys

sys.path.insert(0, 'src')
from models import generate_response

os.makedirs('reports/probes', exist_ok=True)
trace_file = 'reports/probes/structural_self_preference/self_preference_traces.jsonl'
file_lock = asyncio.Lock()

async def rank_candidates(verifier, domain, strategy, question, cand_a, cand_b, name_a, name_b):
    prompt = f"""You are an expert reviewer.
Below is a {domain} problem, followed by two different attempts to solve it (Candidate A and Candidate B).

Your task is to evaluate the underlying ALGORITHMIC APPROACH, logic, and structure of both candidates. 
You must output exactly one of the following four choices:
- WINNER: Candidate A (If Candidate A's structural approach is superior, even if flawed)
- WINNER: Candidate B (If Candidate B's structural approach is superior, even if flawed)
- WINNER: Both Correct (If you believe both are completely correct)
- WINNER: Both Incorrect (If you believe they are equally flawed and neither approach is superior)

Provide a brief 1-sentence justification, then output your final choice on a new line in this exact format:
WINNER: [Your Choice]

[Problem]
{question}

[Candidate A]
{cand_a}

[Candidate B]
{cand_b}
"""
    messages = [{'role': 'user', 'content': prompt}]
    
    try:
        res = await asyncio.wait_for(
            generate_response(verifier, messages, temperature=0.0, max_tokens=200),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        return "TIMEOUT"
        
    if not res: return "ERROR"
    content = res['content']
    
    # Parse the 4 choices
    if 'WINNER: Both Correct' in content or 'WINNER: both correct' in content.lower():
        return "BOTH_CORRECT"
    if 'WINNER: Both Incorrect' in content or 'WINNER: both incorrect' in content.lower():
        return "BOTH_INCORRECT"
    if 'WINNER: Candidate A' in content or 'WINNER: candidate a' in content.lower():
        return name_a
    if 'WINNER: Candidate B' in content or 'WINNER: candidate b' in content.lower():
        return name_b
        
    # Fallback
    last_line = content.split('\n')[-1].lower()
    if 'both correct' in last_line: return "BOTH_CORRECT"
    if 'both incorrect' in last_line: return "BOTH_INCORRECT"
    if 'candidate a' in last_line: return name_a
    if 'candidate b' in last_line: return name_b
    
    return "UNKNOWN"

async def process_item(item_id, domain, strategy, frame, question, cand_ds, cand_qw, verifier, sem):
    async with sem:
        print(f"[{verifier.upper()}] A/B Test -> {domain} | {strategy} | {frame} | {item_id}")
        
        # Pass 1: A = DeepSeek, B = Qwen
        pass1 = await rank_candidates(verifier, domain, strategy, question, cand_ds, cand_qw, 'deepseek', 'qwen')
        
        # Pass 2: A = Qwen, B = DeepSeek
        pass2 = await rank_candidates(verifier, domain, strategy, question, cand_qw, cand_ds, 'qwen', 'deepseek')
        
        # Determine strict category
        category = "INCONSISTENT"
        
        if pass1 == 'deepseek' and pass2 == 'deepseek':
            category = "TRUE_PREF_DEEPSEEK"
        elif pass1 == 'qwen' and pass2 == 'qwen':
            category = "TRUE_PREF_QWEN"
        elif pass1 == 'BOTH_INCORRECT' and pass2 == 'BOTH_INCORRECT':
            category = "CONSISTENT_BOTH_INCORRECT"
        elif pass1 == 'BOTH_CORRECT' and pass2 == 'BOTH_CORRECT':
            category = "CONSISTENT_BOTH_CORRECT"
        elif pass1 == 'deepseek' and pass2 == 'qwen':
            category = "POSITION_BIAS_ALWAYS_A"
        elif pass1 == 'qwen' and pass2 == 'deepseek':
            category = "POSITION_BIAS_ALWAYS_B"
            
        trace = {
            'item_id': item_id,
            'domain': domain,
            'strategy': strategy,
            'frame': frame,
            'verifier': verifier,
            'pass1_choice': pass1,
            'pass2_choice': pass2,
            'category': category,
            'deepseek_code': cand_ds,
            'qwen_code': cand_qw
        }
        
        async with file_lock:
            with open(trace_file, 'a') as f:
                f.write(json.dumps(trace) + '\n')
                
        return trace

async def run_probe():
    print("--- Starting Structural Self-Preference Probe (All Combinations) ---")
    df = pd.read_csv('reports/actual/all/actual_all_results_granular.csv', low_memory=False)
    
    ds_fails = df[(df['verifier'] == 'deepseek') & (df['generator'] == 'deepseek') & (df['fp'] == 1)]
    qw_fails = df[(df['verifier'] == 'qwen') & (df['generator'] == 'qwen') & (df['fp'] == 1)]
    
    keys = ['item_id', 'domain', 'strategy', 'frame']
    shared = pd.merge(ds_fails[keys], qw_fails[keys], on=keys, how='inner')
    shared = shared.drop_duplicates()
    
    print(f"Found {len(shared)} exact combinations where BOTH DeepSeek and Qwen generated wrong code AND falsely approved it.")
    
    with open(trace_file, 'w') as f:
        pass 
    
    questions = {}
    gen_ds = {}
    gen_qw = {}
    
    for d in ['code', 'math', 'science']:
        with open(f'data/raw/{d}.jsonl', 'r') as f:
            for line in f:
                item = json.loads(line)
                questions[item['item_id']] = item['question']
        with open(f'data/generated/{d}.jsonl', 'r') as f:
            for line in f:
                item = json.loads(line)
                if 'deepseek' in item.get('candidates', {}):
                    gen_ds[item['item_id']] = item['candidates']['deepseek']
                if 'qwen' in item.get('candidates', {}):
                    gen_qw[item['item_id']] = item['candidates']['qwen']
                    
    sem = asyncio.Semaphore(10)
    
    print("\n[1/2] Asking DeepSeek Verifier...")
    tasks_ds = []
    for _, row in shared.iterrows():
        i, d, s, fr = row['item_id'], row['domain'], row['strategy'], row['frame']
        q = questions.get(i)
        c_ds = gen_ds.get(i)
        c_qw = gen_qw.get(i)
        if q and c_ds and c_qw:
            tasks_ds.append(process_item(i, d, s, fr, q, c_ds, c_qw, 'deepseek', sem))
    results_ds = await asyncio.gather(*tasks_ds)
    results_ds = [r for r in results_ds if r is not None]
    
    print("\n[2/2] Asking Qwen Verifier...")
    tasks_qw = []
    for _, row in shared.iterrows():
        i, d, s, fr = row['item_id'], row['domain'], row['strategy'], row['frame']
        q = questions.get(i)
        c_ds = gen_ds.get(i)
        c_qw = gen_qw.get(i)
        if q and c_ds and c_qw:
            tasks_qw.append(process_item(i, d, s, fr, q, c_ds, c_qw, 'qwen', sem))
    results_qw = await asyncio.gather(*tasks_qw)
    results_qw = [r for r in results_qw if r is not None]
    
    print("\n=========================================")
    print("      STRUCTURAL SELF-PREFERENCE METRICS      ")
    print("=========================================\n")
    
    for verifier, results in [('DEEPSEEK', results_ds), ('QWEN', results_qw)]:
        total = len(results)
        if total == 0: continue
        
        pref_own = sum(1 for r in results if r['category'] == f"TRUE_PREF_{verifier}")
        pref_other = sum(1 for r in results if r['category'] == ("TRUE_PREF_QWEN" if verifier=="DEEPSEEK" else "TRUE_PREF_DEEPSEEK"))
        both_incorrect = sum(1 for r in results if r['category'] == "CONSISTENT_BOTH_INCORRECT")
        both_correct = sum(1 for r in results if r['category'] == "CONSISTENT_BOTH_CORRECT")
        bias_a = sum(1 for r in results if r['category'] == "POSITION_BIAS_ALWAYS_A")
        bias_b = sum(1 for r in results if r['category'] == "POSITION_BIAS_ALWAYS_B")
        inconsistent = sum(1 for r in results if r['category'] == "INCONSISTENT")
        
        print(f"--- VERIFIER: {verifier} ({total} cases) ---")
        print(f"  Selected its OWN algorithm     : {pref_own/total*100:.1f}% ({pref_own})")
        print(f"  Selected the OTHER algorithm   : {pref_other/total*100:.1f}% ({pref_other})")
        print(f"  Consistently voted 'Both Incorrect': {both_incorrect/total*100:.1f}% ({both_incorrect})")
        print(f"  Consistently voted 'Both Correct'  : {both_correct/total*100:.1f}% ({both_correct})")
        print(f"  Failed due to Position Bias (A/B)  : {(bias_a+bias_b)/total*100:.1f}% ({bias_a+bias_b})")
        print(f"  Inconsistent / Tie / Refusal       : {inconsistent/total*100:.1f}% ({inconsistent})\n")

if __name__ == '__main__':
    asyncio.run(run_probe())
