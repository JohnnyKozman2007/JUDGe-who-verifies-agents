import json
import os
import asyncio
import pandas as pd
import sys

sys.path.insert(0, 'src')
from models import generate_response
from prompts import get_verification_prompt

# Ensure directory exists immediately
os.makedirs('reports/probes', exist_ok=True)
trace_file = 'reports/probes/style_transfer/style_transfer_traces.jsonl'
file_lock = asyncio.Lock()

async def rewrite_text(original_text, prompt_file):
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'Here is the candidate answer to rewrite:\n\n{original_text}'}
    ]
    
    try:
        res = await asyncio.wait_for(
            generate_response('mistralai/Mixtral-8x7B-Instruct-v0.1', messages, temperature=0.3, max_tokens=2500),
            timeout=60.0
        )
        if res: return res['content']
    except asyncio.TimeoutError:
        pass
    return original_text

async def verify_candidate(verifier, domain, question, candidate, strategy, frame):
    prompt = get_verification_prompt(domain, question, candidate, frame, strategy)
    messages = [{'role': 'user', 'content': prompt}]
    
    resp_format = 'json_object' if strategy == 'direct' else None
    
    try:
        res = await asyncio.wait_for(
            generate_response(verifier, messages, temperature=0.0, max_tokens=1000, response_format=resp_format),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        return None
        
    if not res: return None
    content = res['content']
    
    if strategy == 'direct':
        try:
            parsed = json.loads(content)
            for k, v in parsed.items():
                if isinstance(v, bool): return v
                if str(v).lower() in ['true', 'yes', 'correct']: return True
                if str(v).lower() in ['false', 'no', 'incorrect']: return False
        except: pass
            
    lower_content = content.lower()
    if '\"is_correct\": true' in lower_content or '\"is_correct\":true' in lower_content: return True
    if '\"is_correct\": false' in lower_content or '\"is_correct\":false' in lower_content: return False
    return None

async def process_item(item_id, question, candidate, verifier, domain, strategy, frame, sem):
    async with sem:
        print(f'Processing {verifier} -> {domain} -> {frame} -> {item_id}...')
        mistral_style = await rewrite_text(candidate, 'prompts/rewrite_mistral.txt')
        control_style = await rewrite_text(candidate, 'prompts/rewrite_control.txt')
        
        v_mistral = await verify_candidate(verifier, domain, question, mistral_style, strategy, frame)
        v_control = await verify_candidate(verifier, domain, question, control_style, strategy, frame)
        
        trace = {
            'item_id': item_id,
            'domain': domain,
            'strategy': strategy,
            'frame': frame,
            'verifier': verifier,
            'original_verdict': True,
            'control_verdict': v_control,
            'mistral_style_verdict': v_mistral,
            'original_text': candidate,
            'mistral_text': mistral_style,
            'control_text': control_style
        }
        
        # REAL-TIME LOGGING: Save the trace immediately after it finishes
        async with file_lock:
            with open(trace_file, 'a') as f:
                f.write(json.dumps(trace) + '\n')
                
        return trace

async def process_target(target_name, verifier, generator):
    print(f'\n--- Starting {target_name} ---')
    df = pd.read_csv('reports/actual/all/actual_all_results_granular.csv', low_memory=False)
    
    mask = (df['verifier'] == verifier) & (df['generator'] == generator) & \
           (df['candidate_is_correct'] == False) & (df['fp'] == 1)
    
    fps = df[mask]
    print(f'Found {len(fps)} absolute False Positive cases for {target_name}.')
    if len(fps) == 0: return []
        
    raw_dicts = {'code': {}, 'math': {}, 'science': {}}
    gen_dicts = {'code': {}, 'math': {}, 'science': {}}
    for d in ['code', 'math', 'science']:
        with open(f'data/raw/{d}.jsonl', 'r') as f:
            for line in f:
                item = json.loads(line)
                raw_dicts[d][item['item_id']] = item['question']
        with open(f'data/generated/{d}.jsonl', 'r') as f:
            for line in f:
                item = json.loads(line)
                if generator in item.get('candidates', {}):
                    gen_dicts[d][item['item_id']] = item['candidates'][generator]

    sem = asyncio.Semaphore(5)
    tasks = []
    
    for _, row in fps.iterrows():
        item_id = row['item_id']
        domain = row['domain']
        strategy = row['strategy']
        frame = row['frame']
        
        q = raw_dicts[domain].get(item_id)
        c = gen_dicts[domain].get(item_id)
        if q and c:
            tasks.append(process_item(item_id, q, c, verifier, domain, strategy, frame, sem))
            
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

async def main():
    # Clear the trace file at the start of a fresh run
    with open(trace_file, 'w') as f:
        pass 

    all_traces = []
    
    results_ds = await process_target('DeepSeek (All)', 'deepseek', 'deepseek')
    all_traces.extend(results_ds)
    
    results_qw = await process_target('Qwen (All)', 'qwen', 'qwen')
    all_traces.extend(results_qw)
    
    print(f'\n[SUCCESS] Fully complete. Traces saved to {trace_file}')
    
    print('\n--- FINAL SUMMARY ---')
    for verifier in ['deepseek', 'qwen']:
        subset = [r for r in all_traces if r['verifier'] == verifier]
        if not subset: continue
        
        total = len(subset)
        control_fps = sum(1 for r in subset if r['control_verdict'] == True)
        mistral_fps = sum(1 for r in subset if r['mistral_style_verdict'] == True)
        
        print(f'{verifier.upper()}:')
        print(f'  Original FPR: 100% ({total}/{total})')
        print(f'  Control FPR : {control_fps/total*100:.1f}% ({control_fps}/{total})')
        print(f'  Mistral FPR : {mistral_fps/total*100:.1f}% ({mistral_fps}/{total})')
        print(f'  -> FPR Drop : -{(control_fps - mistral_fps)/total*100:.1f}%\n')

if __name__ == '__main__':
    asyncio.run(main())
