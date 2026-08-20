import os
import json
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from execution_grounding import run_candidate_code
from science_utils import extract_option_map_from_question, parse_science_candidate_answer

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", default="data/raw", help="Directory with raw jsonl files")
    parser.add_argument("--gen_dir", default="data/generated", help="Directory with generated jsonl files")
    parser.add_argument("--ver_dir", default="data/verified", help="Directory with verified jsonl files")
    parser.add_argument("--out_dir", default="reports", help="Output directory for CSV reports")
    parser.add_argument("--plot_dir", default="plots", help="Output directory for plots")
    parser.add_argument("--mode", type=str, choices=["pilot", "actual"], default="pilot", help="Run in pilot or actual mode")
    return parser.parse_args()

def _notes_to_string(notes):
    if notes is None:
        return ""
    if isinstance(notes, list):
        return ";".join(str(note) for note in notes)
    return str(notes)

def normalize_bool_verdict(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def recover_verdict_from_raw_response(raw_response):
    """
    Recover is_correct from JSON-like verifier responses that failed strict parsing,
    commonly because LaTeX backslashes such as \\( or \\kappa are invalid JSON escapes.
    """
    if not raw_response:
        return None

    text = str(raw_response).strip()

    try:
        parsed = json.loads(text)
        return normalize_bool_verdict(parsed.get("is_correct"))
    except Exception:
        pass

    matches = re.findall(
        r'["\']?is_correct["\']?\s*[:=]\s*["\']?(true|false)["\']?',
        text,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    unique = {match.lower() for match in matches}
    if len(unique) > 1:
        return None

    return matches[-1].lower() == "true"

def parse_science_for_item(candidate_text, raw_item):
    option_map = raw_item.get("option_map")
    if not isinstance(option_map, dict):
        option_map = extract_option_map_from_question(str(raw_item.get("question", "")))
    return parse_science_candidate_answer(candidate_text, option_map)


def grade_science(candidate_text, raw_item):
    parsed = parse_science_for_item(candidate_text, raw_item)
    gt = str(raw_item.get("ground_truth", "")).upper()
    return parsed["letter"] == gt and not parsed["ambiguous"]

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
    graded_candidates = {}
    science_audit_rows = []
    mode = args.mode
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    domains = ["math", "code", "science"]
    
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
                        parsed_science = parse_science_for_item(cand_text, raw_item)
                        ground_truth_letter = str(raw_item.get("ground_truth", "")).upper()
                        is_correct = parsed_science.get("letter") == ground_truth_letter and not parsed_science.get("ambiguous")

                        science_audit_rows.append({
                            "item_id": item_id,
                            "generator": gen_model,
                            "ground_truth_letter": ground_truth_letter,
                            "ground_truth_text": raw_item.get("correct_answer_text"),
                            "extracted_letter": parsed_science.get("letter"),
                            "extracted_option_text": parsed_science.get("option_text"),
                            "extraction_mode": parsed_science.get("mode"),
                            "extraction_confidence": parsed_science.get("confidence"),
                            "ambiguous": int(bool(parsed_science.get("ambiguous"))),
                            "parsed_successfully": int(parsed_science.get("letter") is not None),
                            "parse_notes": _notes_to_string(parsed_science.get("notes")),
                            "is_correct": int(is_correct),
                        })
                    elif domain == "math":
                        is_correct = grade_math(cand_text, raw_item['ground_truth'])
                    elif domain == "code":
                        is_correct = grade_code(cand_text, raw_item['test'], entry_point=raw_item.get('entry_point'))
                    graded_candidates[(domain, item_id, gen_model)] = is_correct
    return graded_candidates, pd.DataFrame(science_audit_rows)

def load_fuzz_results(args):
    mode = args.mode
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    fuzz_dict = {}
    path = os.path.join("data", "validated", f"code_overrides{suffix}")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                key = (item['item_id'], item['generator_model'], item['verifier_model'], item['frame'], item['strategy'])
                fuzz_dict[key] = item.get('fuzz_verdict')
    return fuzz_dict

def analyze_verifications(args, graded_candidates, fuzz_dict):
    mode = args.mode
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    domains = ["math", "code", "science"]
    rows = []
    fuzz_errors_removed = 0
    
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
                adjusted_cand_is_correct = cand_is_correct
                
                fuzz_verdict = None
                if domain == "code":
                    key = (item_id, gen_model, ver_model, frame, strategy)
                    fuzz_verdict = fuzz_dict.get(key)
                
                if fuzz_verdict == "ERROR":
                    fuzz_errors_removed += 1
                    continue
                    
                if fuzz_verdict == "BUG_CONFIRMED":
                    adjusted_cand_is_correct = False
                elif fuzz_verdict in ("REFERENCE_BUG", "NO_DISCREPANCY"):
                    adjusted_cand_is_correct = True

                original_parsed_verdict = normalize_bool_verdict(v.get('parsed_verdict'))
                parsed = original_parsed_verdict
                verdict_recovered_from_raw = False

                if parsed is None:
                    recovered = recover_verdict_from_raw_response(v.get("raw_response"))
                    if recovered is not None:
                        parsed = recovered
                        verdict_recovered_from_raw = True
                thinking = v.get('thinking_or_evaluation', '')
                verbosity = len(thinking) if thinking else 0
                
                dissociated = False
                label_was_right = False
                reasoning_was_right = False
                
                if strategy != 'direct' and thinking and parsed is not None:
                    # Use word-boundary regex to avoid substring false alarms, and negative lookbehinds for "no/not"
                    has_negative = bool(re.search(r'(?<!no )(?<!not )\b(error|fail|fails|incorrect|issue|bug|wrong)\b', thinking, re.IGNORECASE))
                    has_positive = bool(re.search(r'(?<!no )(?<!not )\b(correct|valid|sound|perfect)\b', thinking, re.IGNORECASE))
                    
                    if (parsed is True and has_negative) or (parsed is False and has_positive and not has_negative):
                        dissociated = True
                        if parsed == cand_is_correct:
                            label_was_right = True
                        else:
                            reasoning_was_right = True
                
                if parsed is None:
                    # Unparseable verdict: exclude from confusion matrix entirely
                    tp = fp = tn = fn = False
                    adj_tp = adj_fp = adj_tn = adj_fn = False
                else:
                    verdict = parsed
                    tp = (cand_is_correct == True and verdict == True)
                    fp = (cand_is_correct == False and verdict == True)
                    tn = (cand_is_correct == False and verdict == False)
                    fn = (cand_is_correct == True and verdict == False)
                    
                    adj_tp = (adjusted_cand_is_correct == True and verdict == True)
                    adj_fp = (adjusted_cand_is_correct == False and verdict == True)
                    adj_tn = (adjusted_cand_is_correct == False and verdict == False)
                    adj_fn = (adjusted_cand_is_correct == True and verdict == False)
                
                # Ground-truth authorship, independent of what the verifier was TOLD (frame).
                actual_source = 'self' if gen_model == ver_model else 'other'
                # Was the told frame accurate? (only meaningful when frame in {self, other})
                frame_matches_truth = (frame == actual_source) if frame in ('self', 'other') else None

                candidate_answer_letter = v.get("candidate_answer_letter")
                candidate_answer_ambiguous = int(domain == "science" and bool(v.get("candidate_answer_ambiguous")))
                candidate_answer_parsed = int(domain == "science" and candidate_answer_letter is not None)
                
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
                    'adjusted_candidate_is_correct': adjusted_cand_is_correct,
                    'parsed_verdict': parsed,
                    'original_parsed_verdict': original_parsed_verdict,
                    'verdict_recovered_from_raw': int(verdict_recovered_from_raw),
                    'strict_json_parse_fail': int(original_parsed_verdict is None),
                    "candidate_answer_letter": candidate_answer_letter,
                    "candidate_answer_text": v.get("candidate_answer_text"),
                    "candidate_answer_extraction_mode": v.get("candidate_answer_extraction_mode"),
                    "candidate_answer_extraction_confidence": v.get("candidate_answer_extraction_confidence"),
                    "candidate_answer_ambiguous": candidate_answer_ambiguous,
                    "candidate_answer_parsed": candidate_answer_parsed,
                    "candidate_answer_parse_notes": _notes_to_string(v.get("candidate_answer_parse_notes")),
                    "prompt_tokens": v.get("prompt_tokens", 0),
                    "completion_tokens": v.get("completion_tokens", 0),
                    'formatting_fail': int(parsed is None),
                    'tp': int(tp),
                    'fp': int(fp),
                    'tn': int(tn),
                    'fn': int(fn),
                    'adj_tp': int(adj_tp),
                    'adj_fp': int(adj_fp),
                    'adj_tn': int(adj_tn),
                    'adj_fn': int(adj_fn),
                    'latency': v.get('latency', 0),
                    'verbosity': verbosity,
                    'dissociated': int(dissociated),
                    'label_was_right': int(label_was_right),
                    'reasoning_was_right': int(reasoning_was_right),
                    'overrode_passing_tests': int(v.get('overrode_passing_tests', False))
                })
    return pd.DataFrame(rows), fuzz_errors_removed

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

def generate_reports_and_plots(df, args, fuzz_errors_removed):
    # Determine prefix based on mode (pilot/actual). 
    mode = args.mode
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

    science_gen_summary = pd.DataFrame()
    if science_audit_df is not None and not science_audit_df.empty:
        science_audit_df.to_csv(os.path.join(args.out_dir, f'{prefix}science_generation_audit.csv'), index=False)
        science_gen_summary = science_audit_df.groupby('generator').agg(
            Total=('item_id', 'count'),
            Correct=('is_correct', 'sum'),
            Parsed=('parsed_successfully', 'sum'),
            Ambiguous=('ambiguous', 'sum')
        ).reset_index()
        science_gen_summary['Accuracy'] = science_gen_summary['Correct'] / science_gen_summary['Total'].clip(lower=1)
        science_gen_summary['Parse_Rate'] = science_gen_summary['Parsed'] / science_gen_summary['Total'].clip(lower=1)
        science_gen_summary['Ambiguous_Rate'] = science_gen_summary['Ambiguous'] / science_gen_summary['Total'].clip(lower=1)
        science_gen_summary.to_csv(os.path.join(args.out_dir, f'{prefix}science_generator_summary.csv'), index=False)
    
    agg = df.groupby(['domain', 'verifier', 'frame', 'strategy']).agg(
        Total=('item_id', 'count'),
        TP=('tp', 'sum'), FP=('fp', 'sum'), TN=('tn', 'sum'), FN=('fn', 'sum'),
        Adj_TP=('adj_tp', 'sum'), Adj_FP=('adj_fp', 'sum'), Adj_TN=('adj_tn', 'sum'), Adj_FN=('adj_fn', 'sum'),
        Avg_Latency=('latency', 'mean'), Avg_Verbosity=('verbosity', 'mean'),
        Dissociated=('dissociated', 'sum'),
        Formatting_Fails=('formatting_fail', 'sum'),
        Overrode_Passing_Tests=('overrode_passing_tests', 'sum')
    ).reset_index()
    
    agg['Valid_Total'] = (agg['Total'] - agg['Formatting_Fails']).clip(lower=1)
    agg['Accuracy'] = (agg['TP'] + agg['TN']) / agg['Valid_Total']
    agg['Adjusted_Accuracy'] = (agg['Adj_TP'] + agg['Adj_TN']) / agg['Valid_Total']
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

    # Domain-specific checks are kept separate from the headline metrics so the
    # cross-domain report remains balanced while each domain stays auditable.
    domain_validity_df = agg.groupby('domain').agg(
        Total=('Total', 'sum'),
        Formatting_Fails=('Formatting_Fails', 'sum'),
        Dissociated=('Dissociated', 'sum'),
        Code_Overrode_Passing_Tests=('Overrode_Passing_Tests', 'sum')
    ).reset_index()
    domain_validity_df['Formatting_Failure_Rate'] = domain_validity_df['Formatting_Fails'] / domain_validity_df['Total'].clip(lower=1)
    domain_validity_df['Dissociation_Rate'] = domain_validity_df['Dissociated'] / domain_validity_df['Total'].clip(lower=1)
    domain_validity_df['Science_Candidate_Parse_Rate'] = None
    domain_validity_df['Science_Candidate_Ambiguous_Rate'] = None

    science_df = df[df['domain'] == 'science'].copy()
    science_diag = pd.DataFrame()
    if not science_df.empty:
        science_diag = science_df.groupby(['verifier', 'frame', 'strategy']).agg(
            Total=('item_id', 'count'),
            TP=('tp', 'sum'), FP=('fp', 'sum'), TN=('tn', 'sum'), FN=('fn', 'sum'),
            Formatting_Fails=('formatting_fail', 'sum'),
            Candidate_Parsed=('candidate_answer_parsed', 'sum'),
            Candidate_Ambiguous=('candidate_answer_ambiguous', 'sum'),
            Avg_Latency=('latency', 'mean'),
            Avg_Verbosity=('verbosity', 'mean'),
            Dissociated=('dissociated', 'sum')
        ).reset_index()
        science_diag['Valid_Total'] = (science_diag['Total'] - science_diag['Formatting_Fails']).clip(lower=1)
        science_diag['Accuracy'] = (science_diag['TP'] + science_diag['TN']) / science_diag['Valid_Total']
        science_diag['FPR'] = science_diag['FP'] / (science_diag['FP'] + science_diag['TN']).replace(0, 1)
        science_diag['FNR'] = science_diag['FN'] / (science_diag['FN'] + science_diag['TP']).replace(0, 1)
        science_diag['Candidate_Parse_Rate'] = science_diag['Candidate_Parsed'] / science_diag['Total'].clip(lower=1)
        science_diag['Candidate_Ambiguous_Rate'] = science_diag['Candidate_Ambiguous'] / science_diag['Total'].clip(lower=1)
        science_diag['Dissociation_Rate'] = science_diag['Dissociated'] / science_diag['Total'].clip(lower=1)
        science_diag.to_csv(os.path.join(args.out_dir, f'{prefix}science_verifier_diagnostics.csv'), index=False)

        science_mask = domain_validity_df['domain'] == 'science'
        domain_validity_df.loc[science_mask, 'Science_Candidate_Parse_Rate'] = science_df['candidate_answer_parsed'].mean()
        domain_validity_df.loc[science_mask, 'Science_Candidate_Ambiguous_Rate'] = science_df['candidate_answer_ambiguous'].mean()

    domain_validity_df.to_csv(os.path.join(args.out_dir, f'{prefix}domain_validity_checks.csv'), index=False)
    
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
            except Exception: p_fpr = 1.0
            try: _, p_fnr, _, _ = chi2_contingency([[self_row['FN'], self_row['TP']], [other_row['FN'], other_row['TP']]])
            except Exception: p_fnr = 1.0
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
        f.write(f"**Total Verifications Processed:** {agg['Total'].sum()}\n")
        if fuzz_errors_removed > 0:
            f.write(f"**Fuzzer Errors Removed:** {fuzz_errors_removed} (These were safely dropped from all metrics)\n\n")
        else:
            f.write("\n")
        
        f.write("## Highest Accuracy by Domain\n")
        f.write(f"![Accuracy Plot](../{args.plot_dir}/{prefix}accuracy_by_domain.png)\n\n")
        for domain in sorted(df['domain'].unique()):
            dom_df = agg[agg['domain'] == domain]
            best_row = dom_df.loc[dom_df['Accuracy'].idxmax()]
            f.write(f"- **{domain.capitalize()}**: {best_row['verifier']} (Frame: {best_row['frame']}, Strategy: {best_row['strategy']}) achieved **{best_row['Accuracy']*100:.1f}%** accuracy (**{best_row['Adjusted_Accuracy']*100:.1f}% Adjusted**).\n")
            
        f.write("\n## Model Preferences by Domain (Best Configurations)\n")
        for domain in sorted(df['domain'].unique()):
            f.write(f"### {domain.capitalize()}\n")
            dom_df = agg[agg['domain'] == domain]
            for model in sorted(dom_df['verifier'].unique()):
                mod_df = dom_df[dom_df['verifier'] == model]
                best_row = mod_df.loc[mod_df['Accuracy'].idxmax()]
                f.write(f"- **{model}**: Prefers **{best_row['frame']}** frame & **{best_row['strategy']}** strategy (**{best_row['Accuracy']*100:.1f}%**)\n")

        f.write("\n## Strategy Performance per Model (Raw Accuracy)\n")
        strat_mod = agg.groupby(['verifier', 'strategy'])['Accuracy'].mean().unstack()
        f.write("| Model | " + " | ".join(strat_mod.columns) + " |\n")
        f.write("|-------|" + "|".join(["---"] * len(strat_mod.columns)) + "|\n")
        for model, row in strat_mod.iterrows():
            f.write(f"| **{model}** | " + " | ".join([f"{v*100:.1f}%" for v in row]) + " |\n")
            
        f.write("\n## Strategy Performance per Model (Adjusted Accuracy)\n")
        strat_mod_adj = agg.groupby(['verifier', 'strategy'])['Adjusted_Accuracy'].mean().unstack()
        f.write("| Model | " + " | ".join(strat_mod_adj.columns) + " |\n")
        f.write("|-------|" + "|".join(["---"] * len(strat_mod_adj.columns)) + "|\n")
        for model, row in strat_mod_adj.iterrows():
            f.write(f"| **{model}** | " + " | ".join([f"{v*100:.1f}%" for v in row]) + " |\n")

        write_breakdown_section(f, "1. Comprehensive Accuracy Breakdown (Raw)", agg, 'Accuracy', is_percent=True, invert_good=False)
        write_breakdown_section(f, "1b. Comprehensive Accuracy Breakdown (Adjusted)", agg, 'Adjusted_Accuracy', is_percent=True, invert_good=False)
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

        f.write("\n## 7. Domain-Specific Validity Checks\n")
        f.write("*These checks are diagnostic safeguards around domain-specific grading. They support the shared metrics above; they do not replace the common accuracy/FPR/FNR analysis.*\n\n")
        f.write(f"Full table: `{prefix}domain_validity_checks.csv`.\n\n")

        f.write("### Code: Execution Grounding\n")
        f.write("*Instances where the code passed the test suite, but the verifier LLM overrode that execution signal and marked it INCORRECT.*\n")
        code_agg = agg[agg['domain'] == 'code']
        if not code_agg.empty:
            override_sum = code_agg['Overrode_Passing_Tests'].sum()
            f.write(f"- **Total Overrides**: {override_sum} out of {code_agg['TP'].sum() + code_agg['FN'].sum()} passing submissions.\n\n")
            f.write("#### By Verifier Model\n")
            for verifier in sorted(code_agg['verifier'].unique()):
                v_df = code_agg[code_agg['verifier'] == verifier]
                f.write(f"- **{verifier}**: {v_df['Overrode_Passing_Tests'].sum()}\n")
        else:
            f.write("*(No code domain data present)*\n")

        f.write("\n### Science: Option Extraction Audit\n")
        f.write("*Science grading uses the shared correctness metrics above, with an additional parser audit because GPQA answers must map cleanly to one of A-D.*\n")
        if not science_df.empty:
            parse_rate = science_df['candidate_answer_parsed'].mean()
            ambiguous_rate = science_df['candidate_answer_ambiguous'].mean()
            f.write(f"- **Candidate Parse Rate**: {parse_rate*100:.1f}% of science verification rows had a detected A-D answer.\n")
            f.write(f"- **Ambiguous Candidate Rate**: {ambiguous_rate*100:.1f}% of science verification rows were marked ambiguous by the parser.\n")
            if not science_gen_summary.empty:
                best_gen = science_gen_summary.loc[science_gen_summary['Accuracy'].idxmax()]
                f.write(f"- **Best Science Generator**: {best_gen['generator']} with {best_gen['Accuracy']*100:.1f}% generation accuracy.\n")
            if not science_diag.empty:
                best_cell = science_diag.loc[science_diag['Accuracy'].idxmax()]
                worst_fp = science_diag.loc[science_diag['FPR'].idxmax()]
                f.write(f"- **Best Science Verifier Cell**: {best_cell['verifier']} / {best_cell['frame']} / {best_cell['strategy']} at {best_cell['Accuracy']*100:.1f}% accuracy.\n")
                f.write(f"- **Highest Science False-Approval Cell**: {worst_fp['verifier']} / {worst_fp['frame']} / {worst_fp['strategy']} with {worst_fp['FPR']*100:.1f}% FPR.\n")
            f.write(f"Full science audit files: `{prefix}science_generation_audit.csv`, `{prefix}science_generator_summary.csv`, `{prefix}science_verifier_diagnostics.csv`.\n")
        else:
            f.write("*(No science domain data present)*\n")

        f.write("\n### Math: Answer Matching\n")
        math_agg = agg[agg['domain'] == 'math']
        if not math_agg.empty:
            f.write("- Math candidates are graded by boxed-answer extraction first, then numeric/exact matching. Symbolically equivalent but differently formatted answers remain a limitation to mention in the paper.\n")
            f.write(f"- **Math Verification Rows**: {int(math_agg['Total'].sum())}\n")
        else:
            f.write("*(No math domain data present)*\n")

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
                f"(same label, different truth) isolates the pure *reality* effect. Full data: `{prefix}belief_vs_reality.csv`.\n")

        f.write("\n## 9. Confusion Matrices (Visuals & Raw Data)\n")
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
        
    print("Grading generated candidates against ground truth...")
    graded, science_audit_df = load_and_grade(args)
    
    print("Loading fuzzer override results...")
    fuzz_dict = load_fuzz_results(args)
    
    print("Analyzing verifications...")
    df, fuzz_errors_removed = analyze_verifications(args, graded, fuzz_dict)
    
    if not df.empty:
        print("Generating reports and plots...")
        generate_reports_and_plots(df, args, fuzz_errors_removed, science_audit_df)
    else:
        print("No verified data found to report on.")

if __name__ == "__main__":
    main()
