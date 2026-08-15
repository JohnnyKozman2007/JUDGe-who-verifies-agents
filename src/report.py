import os
import json
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from execution_grounding import run_candidate_code

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", default="data/raw", help="Directory with raw jsonl files")
    parser.add_argument("--gen_dir", default="data/generated", help="Directory with generated jsonl files")
    parser.add_argument("--ver_dir", default="data/verified", help="Directory with verified jsonl files")
    parser.add_argument("--out_dir", default="reports", help="Output directory for CSV reports")
    parser.add_argument("--plot_dir", default="plots", help="Output directory for plots")
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot", help="Run in pilot or actual mode")
    parser.add_argument("--is_pilot", action="store_true", help="Legacy flag: use pilot mode")
    return parser.parse_args()

def grade_science(candidate_text, ground_truth):
    if not candidate_text: return False
    match = re.search(r'(?i)(?:answer|option)\s*(?:is)?\s*[\:\*\_]*\s*\(?([A-D])\)?', candidate_text)
    if match:
        return match.group(1).upper() == ground_truth.upper()
    matches = re.findall(r'\b([A-D])\b', candidate_text.upper())
    if matches:
        return matches[-1] == ground_truth.upper()
    return False

def _math_values_equal(a, b, tol=1e-6):
    """Compare two math answer strings, numerically if possible, else exact (stripped) string match."""
    a, b = a.strip(), b.strip()
    try:
        return abs(float(a.replace(',', '')) - float(b.replace(',', ''))) < tol
    except ValueError:
        return a == b

def grade_math(candidate_text, ground_truth):
    if not candidate_text: return False
    gt_match = re.search(r'\\boxed\{(.*?)\}', ground_truth)
    gt_val = gt_match.group(1).strip() if gt_match else ground_truth.strip()

    # Prefer the candidate's own boxed answer if present (most reliable signal)
    cand_box = re.search(r'\\boxed\{(.*?)\}', candidate_text)
    if cand_box:
        return _math_values_equal(cand_box.group(1), gt_val)

    # Try numeric comparison using standalone numbers only (word/number-boundary aware,
    # so ground truth "5" does NOT match inside "15", "-5", "1.5", "25", etc.)
    try:
        gt_num = float(gt_val.replace(',', ''))
        for tok in re.findall(r'(?<![\d.])-?\d+\.?\d*(?![\d.])', candidate_text):
            try:
                if abs(float(tok) - gt_num) < 1e-6:
                    return True
            except ValueError:
                continue
        return False
    except ValueError:
        # Non-numeric ground truth (e.g. "3/4", "x=5") - use word-boundary match,
        # not raw substring, to avoid partial-token false positives
        pattern = re.escape(gt_val)
        return re.search(rf'(?<!\w){pattern}(?!\w)', candidate_text) is not None

def grade_code(candidate_text, test_code, entry_point=None):
    """Reuses run_candidate_code from execution_grounding.py — single source of truth."""
    if not candidate_text: return False
    result = run_candidate_code(candidate_text, test_code, entry_point=entry_point)
    return result.ran_successfully

def load_and_grade(args):
    mode = "pilot" if args.is_pilot else args.mode
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    domains = ["math", "code", "science"]
    graded_candidates = {}
    
    for domain in domains:
        raw_path = os.path.join(args.raw_dir, f"{domain}{suffix}")
        gen_path = os.path.join(args.gen_dir, f"{domain}{suffix}")
        
        if not os.path.exists(raw_path) or not os.path.exists(gen_path):
            continue
            
        raw_dict = {}
        with open(raw_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                raw_dict[item['item_id']] = item
                
        with open(gen_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                item_id = item['item_id']
                raw_item = raw_dict.get(item_id)
                if not raw_item: continue
                
                for gen_model, cand_text in item.get('candidates', {}).items():
                    if domain == "science":
                        is_correct = grade_science(cand_text, raw_item['ground_truth'])
                    elif domain == "math":
                        is_correct = grade_math(cand_text, raw_item['ground_truth'])
                    elif domain == "code":
                        is_correct = grade_code(cand_text, raw_item['test'], entry_point=raw_item.get('entry_point'))
                    graded_candidates[(domain, item_id, gen_model)] = is_correct
    return graded_candidates

def analyze_verifications(args, graded_candidates):
    mode = "pilot" if args.is_pilot else args.mode
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    domains = ["math", "code", "science"]
    rows = []
    
    for domain in domains:
        ver_path = os.path.join(args.ver_dir, f"{domain}{suffix}")
        if not os.path.exists(ver_path): continue
        
        with open(ver_path, 'r', encoding='utf-8') as f:
            for line in f:
                v = json.loads(line)
                item_id = v['item_id']
                gen_model = v['generator_model']
                ver_model = v['verifier_model']
                frame = v['frame']
                strategy = v['strategy']
                
                cand_is_correct = graded_candidates.get((domain, item_id, gen_model), False)
                parsed = v.get('parsed_verdict')
                thinking = v.get('thinking_or_evaluation', '')
                verbosity = len(thinking) if thinking else 0
                
                dissociated = False
                label_was_right = False
                reasoning_was_right = False
                
                if strategy != 'direct' and thinking and parsed is not None:
                    thinking_lower = thinking.lower()
                    negative_keywords = ['error', 'fail', 'incorrect', 'issue', 'bug', 'wrong']
                    has_negative = any(kw in thinking_lower for kw in negative_keywords)
                    if parsed == True and has_negative:
                        dissociated = True
                        if parsed == cand_is_correct:
                            label_was_right = True
                        else:
                            reasoning_was_right = True
                
                if parsed is None:
                    # Unparseable verdict: exclude from confusion matrix entirely rather
                    # than silently forcing it to count as "wrong" (which fabricates signal
                    # and biases accuracy/FPR/FNR downward without disclosure).
                    tp = fp = tn = fn = False
                else:
                    verdict = parsed
                    tp = (cand_is_correct == True and verdict == True)
                    fp = (cand_is_correct == False and verdict == True)
                    tn = (cand_is_correct == False and verdict == False)
                    fn = (cand_is_correct == True and verdict == False)
                
                # Ground-truth authorship, independent of what the verifier was TOLD (frame).
                actual_source = 'self' if gen_model == ver_model else 'other'
                # Was the told frame accurate? (only meaningful when frame in {self, other})
                frame_matches_truth = (frame == actual_source) if frame in ('self', 'other') else None

                rows.append({
                    'domain': domain,
                    'item_id': item_id,
                    'generator': gen_model,
                    'verifier': ver_model,
                    'frame': frame,
                    'actual_source': actual_source,
                    'frame_matches_truth': frame_matches_truth,
                    'strategy': strategy,
                    'candidate_is_correct': cand_is_correct,
                    'parsed_verdict': parsed,
                    'formatting_fail': int(parsed is None),
                    'tp': int(tp),
                    'fp': int(fp),
                    'tn': int(tn),
                    'fn': int(fn),
                    'latency': v.get('latency', 0),
                    'verbosity': verbosity,
                    'dissociated': int(dissociated),
                    'label_was_right': int(label_was_right),
                    'reasoning_was_right': int(reasoning_was_right),
                    'overrode_passing_tests': int(v.get('overrode_passing_tests', False))
                })
    return pd.DataFrame(rows)

def write_breakdown_section(f, title, df, value_col, is_percent=True, invert_good=False):
    f.write(f"\n## {title}\n")
    overall = df[value_col].mean()
    f.write("### Overall Average Across Everything\n")
    if is_percent:
        f.write(f"- **Overall**: {overall*100:.1f}%\n")
    else:
        f.write(f"- **Overall**: {overall:.1f}\n")
    
    f.write(f"### By Domain\n")
    for domain in sorted(df['domain'].unique()):
        val = df[df['domain'] == domain][value_col].mean()
        f.write(f"- **{domain.capitalize()}**: {val*100:.1f}%\n" if is_percent else f"- **{domain.capitalize()}**: {val:.1f}\n")
        
    f.write(f"### By Strategy\n")
    for strat in sorted(df['strategy'].unique()):
        val = df[df['strategy'] == strat][value_col].mean()
        f.write(f"- **{strat}**: {val*100:.1f}%\n" if is_percent else f"- **{strat}**: {val:.1f}\n")
        
    f.write(f"### By Ownership Frame\n")
    for frame in sorted(df['frame'].unique()):
        val = df[df['frame'] == frame][value_col].mean()
        f.write(f"- **{frame}**: {val*100:.1f}%\n" if is_percent else f"- **{frame}**: {val:.1f}\n")
        
    f.write(f"### By Model\n")
    for model in sorted(df['verifier'].unique()):
        val = df[df['verifier'] == model][value_col].mean()
        f.write(f"- **{model}**: {val*100:.1f}%\n" if is_percent else f"- **{model}**: {val:.1f}\n")
        
    f.write(f"### Top 3 Best Ownership + Strategy Combos\n")
    combo_grp = df.groupby(['frame', 'strategy'])[value_col].mean().reset_index()
    if invert_good:
        top_combos = combo_grp.sort_values(by=value_col, ascending=True).head(3)
    else:
        top_combos = combo_grp.sort_values(by=value_col, ascending=False).head(3)
    for _, row in top_combos.iterrows():
        f.write(f"- **{row['frame']} + {row['strategy']}**: {row[value_col]*100:.1f}%\n" if is_percent else f"- **{row['frame']} + {row['strategy']}**: {row[value_col]:.1f}\n")

def write_behavior_breakdown(f, title, df, group_col=None):
    if group_col is None:
        agg_b = df.agg({'tp': 'sum', 'fp': 'sum', 'tn': 'sum', 'fn': 'sum'})
        caught = agg_b['tn'] / max(1, agg_b['tn'] + agg_b['fp'])
        passed = agg_b['fp'] / max(1, agg_b['tn'] + agg_b['fp'])
        intro = agg_b['fn'] / max(1, agg_b['fn'] + agg_b['tp'])
        conf = agg_b['tp'] / max(1, agg_b['fn'] + agg_b['tp'])
        f.write(f"### {title}\n")
        f.write(f"- **Overall** -> Caught: {caught*100:.1f}% | Passed: {passed*100:.1f}% | Introduced: {intro*100:.1f}% | Confirmed: {conf*100:.1f}%\n")
    else:
        f.write(f"### By {title}\n")
        for g in sorted(df[group_col].unique()):
            g_df = df[df[group_col] == g]
            agg_b = g_df.agg({'tp': 'sum', 'fp': 'sum', 'tn': 'sum', 'fn': 'sum'})
            caught = agg_b['tn'] / max(1, agg_b['tn'] + agg_b['fp'])
            passed = agg_b['fp'] / max(1, agg_b['tn'] + agg_b['fp'])
            intro = agg_b['fn'] / max(1, agg_b['fn'] + agg_b['tp'])
            conf = agg_b['tp'] / max(1, agg_b['fn'] + agg_b['tp'])
            f.write(f"- **{g}** -> Caught: {caught*100:.1f}% | Passed: {passed*100:.1f}% | Introduced: {intro*100:.1f}% | Confirmed: {conf*100:.1f}%\n")

def generate_reports_and_plots(df, args):
    # Determine prefix based on mode (pilot/actual). Legacy is_pilot flag overrides if set.
    mode = "pilot" if args.is_pilot else args.mode
    prefix = "pilot_" if mode == "pilot" else ""
    
    csv_path = os.path.join(args.out_dir, f'{prefix}results_granular.csv')
    # If CSV already exists or plot directory has files, ask once
    need_prompt = os.path.exists(csv_path) or (os.path.isdir(args.plot_dir) and any(os.scandir(args.plot_dir)))
    if need_prompt:
        ans = input(f"Report output (CSV and/or plots) already exists. Overwrite all? (y/n): ")
        if ans.lower().strip() != 'y':
            print("Skipping report generation.")
            return
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(args.plot_dir, exist_ok=True)
    
    df.to_csv(csv_path, index=False)
    
    agg = df.groupby(['domain', 'verifier', 'frame', 'strategy']).agg(
        Total=('item_id', 'count'),
        TP=('tp', 'sum'), FP=('fp', 'sum'), TN=('tn', 'sum'), FN=('fn', 'sum'),
        Avg_Latency=('latency', 'mean'), Avg_Verbosity=('verbosity', 'mean'),
        Dissociated=('dissociated', 'sum'),
        Formatting_Fails=('formatting_fail', 'sum'),
        Overrode_Passing_Tests=('overrode_passing_tests', 'sum')
    ).reset_index()
    
    agg['Valid_Total'] = (agg['Total'] - agg['Formatting_Fails']).clip(lower=1)
    agg['Accuracy'] = (agg['TP'] + agg['TN']) / agg['Valid_Total']
    agg['FPR'] = agg['FP'] / (agg['FP'] + agg['TN']).replace(0, 1)
    agg['FNR'] = agg['FN'] / (agg['FN'] + agg['TP']).replace(0, 1)
    agg['Dissociation_Rate'] = agg['Dissociated'] / agg['Total']
    agg['Formatting_Failure_Rate'] = agg['Formatting_Fails'] / agg['Total']
    
    # Behavior Rates Export
    behavior_df = agg[['domain', 'verifier', 'frame', 'strategy']].copy()
    behavior_df['Errors_Caught_Rate'] = agg['TN'] / (agg['TN'] + agg['FP']).replace(0, 1)
    behavior_df['Errors_Passed_Rate'] = agg['FP'] / (agg['TN'] + agg['FP']).replace(0, 1)
    behavior_df['Errors_Introduced_Rate'] = agg['FN'] / (agg['FN'] + agg['TP']).replace(0, 1)
    behavior_df['Correct_Confirmed_Rate'] = agg['TP'] / (agg['FN'] + agg['TP']).replace(0, 1)
    behavior_df.to_csv(os.path.join(args.out_dir, f'{prefix}verifier_behavior_rates.csv'), index=False)
    
    # Bias and P-Values
    bias_df = agg[agg['frame'].isin(['self', 'other'])]
    pivot_fpr = bias_df.pivot_table(index=['domain', 'verifier', 'strategy'], columns='frame', values='FPR').reset_index()
    if 'other' in pivot_fpr.columns and 'self' in pivot_fpr.columns:
        pivot_fpr['FPR_Self_Bias'] = pivot_fpr['self'] - pivot_fpr['other']
    pivot_fnr = bias_df.pivot_table(index=['domain', 'verifier', 'strategy'], columns='frame', values='FNR').reset_index()
    if 'other' in pivot_fnr.columns and 'self' in pivot_fnr.columns:
        pivot_fnr['FNR_Self_Bias'] = pivot_fnr['self'] - pivot_fnr['other']
    bias_merged = pd.merge(pivot_fpr, pivot_fnr, on=['domain', 'verifier', 'strategy'], suffixes=('_FPR', '_FNR'))
    bias_merged.to_csv(os.path.join(args.out_dir, f'{prefix}bias_metrics.csv'), index=False)
    
    # P-values computed PER (verifier, domain, strategy) cell so they actually test the same
    # slice of data as the bias number they're reported next to (previously this was collapsed
    # across all domains/strategies, which tested a different, blended dataset than the rows
    # it appeared under). Expect many "not significant" results at pilot N (~20/cell) - that's
    # honest, not a flaw; it'll sharpen once cell sizes grow in the full run.
    cell_p_values = {}
    overall_bias = df[df['frame'].isin(['self', 'other'])].groupby(['verifier', 'domain', 'strategy', 'frame']).agg(
        TP=('tp', 'sum'), FP=('fp', 'sum'), TN=('tn', 'sum'), FN=('fn', 'sum')
    ).reset_index()
    for (verifier, domain, strategy), cell_df in overall_bias.groupby(['verifier', 'domain', 'strategy']):
        if 'self' in cell_df['frame'].values and 'other' in cell_df['frame'].values:
            self_row = cell_df[cell_df['frame'] == 'self'].iloc[0]
            other_row = cell_df[cell_df['frame'] == 'other'].iloc[0]
            try: _, p_fpr, _, _ = chi2_contingency([[self_row['FP'], self_row['TN']], [other_row['FP'], other_row['TN']]])
            except: p_fpr = 1.0
            try: _, p_fnr, _, _ = chi2_contingency([[self_row['FN'], self_row['TP']], [other_row['FN'], other_row['TP']]])
            except: p_fnr = 1.0
            cell_p_values[(verifier, domain, strategy)] = {'fpr_p': p_fpr, 'fnr_p': p_fnr}

    # --- Belief-vs-Reality analysis (answers Primary Question #1) ---
    # Crosses the TOLD frame against the ACTUAL (ground-truth) source, so we can separate
    # "does being told you wrote it change behavior" from "does actually having written it
    # change behavior" - these were previously conflated because ~75% of "self"-labeled rows
    # were not actually self-authored, and the report never surfaced the actual_source field.
    belief_reality = df[df['frame'].isin(['self', 'other'])].groupby(
        ['verifier', 'frame', 'actual_source']
    ).agg(
        Total=('item_id', 'count'), TP=('tp', 'sum'), FP=('fp', 'sum'), TN=('tn', 'sum'), FN=('fn', 'sum'),
        Valid=('formatting_fail', lambda s: (1 - s).sum())
    ).reset_index()
    belief_reality['Accuracy'] = (belief_reality['TP'] + belief_reality['TN']) / belief_reality['Valid'].clip(lower=1)
    belief_reality['FPR'] = belief_reality['FP'] / (belief_reality['FP'] + belief_reality['TN']).replace(0, 1)
    belief_reality.to_csv(os.path.join(args.out_dir, f'{prefix}belief_vs_reality.csv'), index=False)

    sns.set_theme(style="whitegrid")
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=agg, x='domain', y='Accuracy', hue='verifier', errorbar=None)
    plt.title('Verifier Accuracy by Domain')
    plt.ylim(0, 1.1)
    plt.savefig(os.path.join(args.plot_dir, f'{prefix}accuracy_by_domain.png'))
    plt.close()
    
    if 'FPR_Self_Bias' in bias_merged.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=bias_merged, x='domain', y='FPR_Self_Bias', hue='verifier', errorbar=None)
        plt.title('Self-Preservation Bias (FPR Gap: Self - Other)')
        plt.ylabel('FPR Difference')
        plt.axhline(0, color='black', linestyle='--')
        plt.savefig(os.path.join(args.plot_dir, f'{prefix}fpr_self_bias.png'))
        plt.close()

    if 'FNR_Self_Bias' in bias_merged.columns:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=bias_merged, x='domain', y='FNR_Self_Bias', hue='verifier', errorbar=None)
        plt.title('Self-Doubt Bias (FNR Gap: Self - Other)')
        plt.ylabel('FNR Difference')
        plt.axhline(0, color='black', linestyle='--')
        plt.savefig(os.path.join(args.plot_dir, f'{prefix}fnr_self_bias.png'))
        plt.close()

    for verifier in df['verifier'].unique():
        mod_df = df[df['verifier'] == verifier]
        matrix = [[mod_df['tn'].sum(), mod_df['fp'].sum()], [mod_df['fn'].sum(), mod_df['tp'].sum()]]
        plt.figure(figsize=(6, 5))
        sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Predicted False', 'Predicted True'], yticklabels=['Actual False', 'Actual True'])
        plt.title(f'Confusion Matrix - {verifier}')
        plt.savefig(os.path.join(args.plot_dir, f'{prefix}confusion_matrix_{verifier}.png'))
        plt.close()

    summary_path = os.path.join(args.out_dir, f'{prefix}executive_summary.md')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# Dynamic Executive Summary\n\n")
        f.write(f"**Total Verifications Processed:** {agg['Total'].sum()}\n\n")
        
        f.write("## Highest Accuracy by Domain\n")
        f.write(f"![Accuracy Plot](../{args.plot_dir}/{prefix}accuracy_by_domain.png)\n\n")
        for domain in sorted(df['domain'].unique()):
            dom_df = agg[agg['domain'] == domain]
            best_row = dom_df.loc[dom_df['Accuracy'].idxmax()]
            f.write(f"- **{domain.capitalize()}**: {best_row['verifier']} (Frame: {best_row['frame']}, Strategy: {best_row['strategy']}) achieved **{best_row['Accuracy']*100:.1f}%** accuracy.\n")
            
        f.write("\n## Model Preferences by Domain (Best Configurations)\n")
        for domain in sorted(df['domain'].unique()):
            f.write(f"### {domain.capitalize()}\n")
            dom_df = agg[agg['domain'] == domain]
            for model in sorted(dom_df['verifier'].unique()):
                mod_df = dom_df[dom_df['verifier'] == model]
                best_row = mod_df.loc[mod_df['Accuracy'].idxmax()]
                f.write(f"- **{model}**: Prefers **{best_row['frame']}** frame & **{best_row['strategy']}** strategy (**{best_row['Accuracy']*100:.1f}%**)\n")

        f.write("\n## Strategy Performance per Model\n")
        strat_mod = agg.groupby(['verifier', 'strategy'])['Accuracy'].mean().unstack()
        f.write("| Model | " + " | ".join(strat_mod.columns) + " |\n")
        f.write("|-------|" + "|".join(["---"] * len(strat_mod.columns)) + "|\n")
        for model, row in strat_mod.iterrows():
            f.write(f"| **{model}** | " + " | ".join([f"{v*100:.1f}%" for v in row]) + " |\n")

        write_breakdown_section(f, "1. Comprehensive Accuracy Breakdown", agg, 'Accuracy', is_percent=True, invert_good=False)
        write_breakdown_section(f, "2. Formatting Failure Rates (NaN / Instructions Missed)", agg, 'Formatting_Failure_Rate', is_percent=True, invert_good=True)
        write_breakdown_section(f, "3. Verbosity Analysis (Average Characters)", agg, 'Avg_Verbosity', is_percent=False, invert_good=False)
        
        non_direct = agg[agg['strategy'] != 'direct']
        if not non_direct.empty:
            write_breakdown_section(f, "4. Dissociation Rates (Hallucinated Verdicts)", non_direct, 'Dissociation_Rate', is_percent=True, invert_good=True)
            f.write("\n### Dissociation Deep Dive (Reasoning vs Label)\n")
            diss_df = df[df['dissociated'] == 1]
            if not diss_df.empty:
                total_diss = len(diss_df)
                label_right = diss_df['label_was_right'].sum()
                reasoning_right = diss_df['reasoning_was_right'].sum()
                f.write(f"Out of {total_diss} hallucinated verifications:\n")
                f.write(f"- **Label was Right / Reasoning was Wrong**: {label_right/total_diss*100:.1f}% of the time.\n")
                f.write(f"- **Reasoning was Right / Label was Wrong**: {reasoning_right/total_diss*100:.1f}% of the time.\n")

        f.write("\n## 5. Verifier Behavior Rates\n")
        write_behavior_breakdown(f, "Overall Averages", df)
        write_behavior_breakdown(f, "Domain", df, 'domain')
        write_behavior_breakdown(f, "Strategy", df, 'strategy')
        write_behavior_breakdown(f, "Ownership Frame", df, 'frame')
        write_behavior_breakdown(f, "Model", df, 'verifier')

        f.write("\n## 6. Statistical Bias (Self vs Other)\n")
        f.write("### Top 3 Highest Self-Preservation Biases (FPR Gap)\n")
        f.write("*These models were most likely to falsely approve their own mistakes.*\n")
        f.write(f"![FPR Bias Plot](../{args.plot_dir}/{prefix}fpr_self_bias.png)\n\n")
        if 'FPR_Self_Bias' in bias_merged.columns:
            top_fpr = bias_merged.sort_values(by='FPR_Self_Bias', ascending=False).head(3)
            for _, row in top_fpr.iterrows():
                f.write(f"- **{row['verifier']}** ({row['domain']}, {row['strategy']}): **+{row['FPR_Self_Bias']*100:.1f}%** bias\n")
                
        f.write("\n### Top 3 Highest Self-Doubt Biases (FNR Gap)\n")
        f.write("*These models were most likely to falsely reject their own correct answers.*\n")
        f.write(f"![FNR Bias Plot](../{args.plot_dir}/{prefix}fnr_self_bias.png)\n\n")
        if 'FNR_Self_Bias' in bias_merged.columns:
            top_fnr = bias_merged.sort_values(by='FNR_Self_Bias', ascending=False).head(3)
            for _, row in top_fnr.iterrows():
                f.write(f"- **{row['verifier']}** ({row['domain']}, {row['strategy']}): **+{row['FNR_Self_Bias']*100:.1f}%** bias\n")
                
        f.write("\n### Statistical Significance (P-Values for Bias)\n")
        f.write("*Chi-Square tests on raw False Positives/Negatives between Self and Other frames, computed PER (verifier, domain, strategy) cell "
                "- i.e. each p-value tests the exact same slice of data as the bias row above it. Small pilot sample sizes (~20/cell) mean most "
                "will read as not significant; that's expected at this scale, not a null result.*\n")
        for _, row in top_fpr.iterrows() if 'FPR_Self_Bias' in bias_merged.columns else []:
            key = (row['verifier'], row['domain'], row['strategy'])
            pv = cell_p_values.get(key)
            if pv:
                f.write(f"- **{row['verifier']}** ({row['domain']}, {row['strategy']}): FPR Bias p={pv['fpr_p']:.4f} | FNR Bias p={pv['fnr_p']:.4f}\n")

        f.write("\n## 7. Test Suite Overrides (Code Domain)\n")
        f.write("*Instances where the code passed the test suite (ground truth correct), but the verifier LLM overrode that signal and marked it INCORRECT.*\n")
        code_agg = agg[agg['domain'] == 'code']
        if not code_agg.empty:
            override_sum = code_agg['Overrode_Passing_Tests'].sum()
            f.write(f"- **Total Overrides**: {override_sum} out of {code_agg['TP'].sum() + code_agg['FN'].sum()} passing submissions.\n\n")
            f.write("### By Verifier Model\n")
            for verifier in sorted(code_agg['verifier'].unique()):
                v_df = code_agg[code_agg['verifier'] == verifier]
                f.write(f"- **{verifier}**: {v_df['Overrode_Passing_Tests'].sum()}\n")
        else:
            f.write("*(No code domain data present)*\n")

        f.write("\n## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)\n")
        f.write("*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? "
                "Rows below cross the told frame against ground-truth authorship (actual_source).*\n\n")
        f.write("| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |\n")
        f.write("|---|---|---|---|---|\n")
        for _, row in belief_reality.sort_values(['verifier', 'frame', 'actual_source']).iterrows():
            actually = "Yes" if row['actual_source'] == 'self' else "No"
            f.write(f"| {row['verifier']} | {row['frame']} | {actually} | {row['Accuracy']*100:.1f}% | {row['FPR']*100:.1f}% |\n")
        f.write("\nRead this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs "
                "(told other / actually self) vs (told other / actually other). A gap between the first two rows "
                "(same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 "
                "(same label, different truth) isolates the pure *reality* effect. Full data: `belief_vs_reality.csv`.\n")

        f.write("\n## 7. Confusion Matrices (Visuals & Raw Data)\n")
        for verifier in sorted(df['verifier'].unique()):
            mod_df = df[df['verifier'] == verifier]
            tp = mod_df['tp'].sum()
            fp = mod_df['fp'].sum()
            tn = mod_df['tn'].sum()
            fn = mod_df['fn'].sum()
            f.write(f"### {verifier}\n")
            f.write(f"**True Positives:** {tp} | **False Positives:** {fp} | **True Negatives:** {tn} | **False Negatives:** {fn}\n\n")
            f.write(f"![Confusion Matrix {verifier}](../{args.plot_dir}/{prefix}confusion_matrix_{verifier}.png)\n")
            
    print(f"Reports successfully generated in {args.out_dir}/ and {args.plot_dir}/")

def main():
    args = parse_args()
    # Resolve mode: legacy --is_pilot overrides --mode if present
    if getattr(args, "is_pilot", False):
        args.mode = "pilot"
    print("Grading generated candidates against ground truth...")
    graded = load_and_grade(args)
    print("Analyzing verifications...")
    df = analyze_verifications(args, graded)
    if not df.empty:
        print("Generating reports and plots...")
        generate_reports_and_plots(df, args)
    else:
        print("No verified data found to report on.")

if __name__ == "__main__":
    main()
