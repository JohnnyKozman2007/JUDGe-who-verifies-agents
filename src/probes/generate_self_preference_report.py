import json
import os
import csv
from collections import defaultdict

def generate_report():
    traces = []
    trace_file = 'reports/probes/structural_self_preference/self_preference_traces.jsonl'
    
    if not os.path.exists(trace_file):
        print(f"Error: {trace_file} not found.")
        return

    with open(trace_file, 'r') as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))

    md_output_path = 'reports/probes/structural_self_preference/self_preference_domain_breakdown.md'
    csv_output_path = 'reports/probes/structural_self_preference/self_preference_domain_breakdown.csv'
    
    md_content = "# Structural Self-Preference Metrics (Domain Breakdown)\n\n"
    csv_rows = [['Verifier', 'Domain', 'Total Cases', 'Selected OWN (%)', 'Selected OWN (Count)', 
                 'Selected OTHER (%)', 'Selected OTHER (Count)', 
                 'Both Incorrect (%)', 'Both Incorrect (Count)', 
                 'Both Correct (%)', 'Both Correct (Count)', 
                 'Position Bias (%)', 'Position Bias (Count)', 
                 'Inconsistent (%)', 'Inconsistent (Count)']]

    for verifier in ['deepseek', 'qwen']:
        v_traces = [t for t in traces if t['verifier'] == verifier]
        domains = ['ALL'] + sorted(list(set(t['domain'] for t in v_traces)))
        
        md_content += f"## VERIFIER: {verifier.upper()}\n"
        
        for d in domains:
            if d == 'ALL':
                d_traces = v_traces
            else:
                d_traces = [t for t in v_traces if t['domain'] == d]
                
            total = len(d_traces)
            if total == 0: continue
            
            pref_own_tag = f"TRUE_PREF_{verifier.upper()}"
            pref_other_tag = "TRUE_PREF_QWEN" if verifier == 'deepseek' else "TRUE_PREF_DEEPSEEK"
            
            pref_own = sum(1 for r in d_traces if r['category'] == pref_own_tag)
            pref_other = sum(1 for r in d_traces if r['category'] == pref_other_tag)
            both_inc = sum(1 for r in d_traces if r['category'] == 'CONSISTENT_BOTH_INCORRECT')
            both_cor = sum(1 for r in d_traces if r['category'] == 'CONSISTENT_BOTH_CORRECT')
            bias = sum(1 for r in d_traces if r['category'] in ['POSITION_BIAS_ALWAYS_A', 'POSITION_BIAS_ALWAYS_B'])
            inconsistent = sum(1 for r in d_traces if r['category'] == 'INCONSISTENT')
            
            # Format Markdown
            md_content += f"### Domain: {d.upper()} ({total} cases)\n"
            md_content += f"- **Selected its OWN algorithm:** {pref_own/total*100:.1f}% ({pref_own})\n"
            md_content += f"- **Selected the OTHER algorithm:** {pref_other/total*100:.1f}% ({pref_other})\n"
            md_content += f"- **Consistently voted 'Both Incorrect':** {both_inc/total*100:.1f}% ({both_inc})\n"
            md_content += f"- **Consistently voted 'Both Correct':** {both_cor/total*100:.1f}% ({both_cor})\n"
            md_content += f"- **Failed due to Position Bias (A/B):** {bias/total*100:.1f}% ({bias})\n"
            md_content += f"- **Inconsistent / Tie / Refusal:** {inconsistent/total*100:.1f}% ({inconsistent})\n\n"
            
            # Format CSV Row
            csv_rows.append([
                verifier.upper(), d.upper(), total,
                f"{pref_own/total*100:.1f}%", pref_own,
                f"{pref_other/total*100:.1f}%", pref_other,
                f"{both_inc/total*100:.1f}%", both_inc,
                f"{both_cor/total*100:.1f}%", both_cor,
                f"{bias/total*100:.1f}%", bias,
                f"{inconsistent/total*100:.1f}%", inconsistent
            ])
            
    with open(md_output_path, 'w') as f:
        f.write(md_content)
        
    with open(csv_output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
        
    print(f"[SUCCESS] Breakdown reports generated at:")
    print(f"  - {md_output_path}")
    print(f"  - {csv_output_path}")

if __name__ == '__main__':
    generate_report()
