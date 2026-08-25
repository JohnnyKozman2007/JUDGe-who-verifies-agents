"""
Does verification ability follow from generation ability?

ORIGINAL HYPOTHESIS (not supported): "oversight flows downward in capability" --
stronger models make better judges, so a weak model cannot police a strong one.

WHAT THE DATA SHOWS: the raw oversight asymmetry is largely a confound. The cell
(verifier=mistral, generator=deepseek) contains DEEPSEEK'S errors, which the
detectability analysis independently proved are intrinsically hard to catch. So the
raw matrix conflates "weak verifier" with "hard-to-detect error".

Holding the SPECIFIC ERROR constant (strata = item x generator), every judge sees the
identical wrong answer to the identical question. Detectability and item difficulty
are then fixed by construction, and what remains is verifier capability. Doing that
reverses the conclusion:

    science (no grounding)        r = +0.47   capability helps
    math    (no runtime oracle)   r = -0.01   capability irrelevant
    code    (execution grounded)  r = -0.35   capability HURTS

The weakest model (Mistral-12B) is the best code judge. The likely mechanism is that
the code verifier prompt explicitly invites overriding the execution signal, and more
capable models take that invitation while weaker ones read the result off. That is
testable here via `overrode_passing_tests` (see override_analysis).

STATISTICS. Row-level p-values are pseudo-replication: thousands of rows but only four
models. Inference is therefore done at the model-pair level (sign test) and by
permuting verifier identity within error strata. Row-level p-values are never reported.

Reads committed data only. Reuses the grade cache from analysis_detectability.
Writes nothing.
"""
import os, sys, json, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_detectability import build_frame, load_or_build_grades

DOMAINS = ["science", "math", "code"]
FRONTIER = ["qwen", "deepseek", "llama"]        # 70B-class; mistral is 12B
GROUNDING = {"science": "none", "math": "none (answer match only)", "code": "execution"}


# ── frame ─────────────────────────────────────────────────────────────
def build_oversight_frame(domain, mode="actual"):
    """
    Reuses the detectability frame: wrong candidates only, self-verification already
    excluded. Adds verifier accuracy and the error stratum (item x generator).
    """
    df = build_frame(domain, mode)
    acc = df.attrs["acc"]
    df["ver_acc"] = df.verifier.map(acc)
    df["stratum"] = df.item_id + "||" + df.generator
    df.attrs["acc"] = acc
    return df


def _stratum_adjusted(df, min_verifiers=2):
    """
    Per (error, verifier) catch rate, demeaned within error. Shared by every check
    below so they all measure the same quantity on the same footing.
    """
    keep = df.groupby("stratum")["verifier"].nunique()
    d = df[df.stratum.isin(keep[keep >= min_verifiers].index)]
    if len(d) == 0:
        return None
    per = d.groupby(["stratum", "verifier"]).agg(
        caught=("rejected", "mean"), ver_acc=("ver_acc", "first")).reset_index()
    if per.ver_acc.nunique() < 2 or len(per) < 20:
        return None
    per["adj"] = per.caught - per.groupby("stratum").caught.transform("mean")
    return per


# ── 1. descriptive ────────────────────────────────────────────────────
def oversight_matrix(df, domain):
    """The raw 4x4. Diagonal is self-verification and is excluded upstream, so it
    prints as '--': it is contaminated by self-preference and is not comparable."""
    print(f"\n{'='*76}\n1. OVERSIGHT MATRIX (error-catch rate) [{domain}]\n{'='*76}")
    acc = df.attrs["acc"]
    order = sorted(acc, key=lambda m: -acc[m])
    print("  rows = verifier, cols = generator; models ordered strongest -> weakest")
    print(f"  {'verifier':16s}" + "".join(f"{g:>11s}" for g in order))
    for v in order:
        line = f"  {v:9s}({acc[v]*100:4.1f}%) "
        for g in order:
            cell = df[(df.verifier == v) & (df.generator == g)]
            line += f"{cell.rejected.mean()*100:10.1f}%" if len(cell) else f"{'--':>11s}"
        print(line)

    up = [df[(df.verifier == v) & (df.generator == g)].rejected.mean()
          for v in acc for g in acc if v != g and acc[v] < acc[g]]
    down = [df[(df.verifier == v) & (df.generator == g)].rejected.mean()
            for v in acc for g in acc if v != g and acc[v] > acc[g]]
    up = [x for x in up if not np.isnan(x)]
    down = [x for x in down if not np.isnan(x)]
    print(f"\n  RAW asymmetry: weaker->stronger {np.mean(up)*100:.1f}%  |  "
          f"stronger->weaker {np.mean(down)*100:.1f}%  |  gap {(np.mean(down)-np.mean(up))*100:+.1f}pp")
    print("  NOTE: this raw gap confounds verifier capability with error detectability.")
    print("        Section 2 separates them; do not quote this number on its own.")


# ── 2. PRIMARY: error-stratified ──────────────────────────────────────
def critical_test(df, domain):
    """Does verifier capability predict catching an error, holding the error fixed?"""
    print(f"\n{'='*76}\n2. PRIMARY — error-stratified [{domain}]  (grounding: {GROUNDING[domain]})\n{'='*76}")
    per = _stratum_adjusted(df)
    if per is None:
        print("  too few strata; skipping"); return None, None
    r = np.corrcoef(per.ver_acc, per.adj)[0, 1]
    print(f"  r(verifier_accuracy, stratum-adjusted catch) = {r:+.4f}")
    print(f"  ({per.stratum.nunique()} distinct errors, {len(per)} error-verifier pairs)")
    print(f"  POSITIVE = stronger verifiers catch more, holding the error constant\n")
    print(f"  {'verifier':10s} {'ver acc':>8s} {'raw catch':>10s} {'stratum-adj':>12s}")
    for m in sorted(df.attrs["acc"], key=lambda x: -df.attrs["acc"][x]):
        s = per[per.verifier == m]
        if len(s) == 0: continue
        raw = df[df.verifier == m].rejected.mean()
        print(f"  {m:10s} {df.attrs['acc'][m]*100:7.1f}% {raw*100:9.1f}% {s.adj.mean()*100:+11.1f}pp")
    return r, per


# ── 3. inference at the model-pair level ──────────────────────────────
def sign_test_pairs(df, domain):
    """
    Each model PAIR is one independent observation of the directional claim.
    Returns (wins, n) so the caller can pool across domains.
    """
    from scipy.stats import binomtest
    acc = df.attrs["acc"]
    models = sorted(acc, key=lambda m: -acc[m])
    print(f"\n{'='*76}\n3. PAIRED SIGN TEST — raw asymmetry, model pairs [{domain}]\n{'='*76}")
    print(f"  {'stronger':10s} {'weaker':10s} {'S->W':>8s} {'W->S':>8s} {'gap':>9s}  dir")
    wins = n = 0
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            s, w = models[i], models[j]
            sw = df[(df.verifier == s) & (df.generator == w)].rejected.mean()
            ws = df[(df.verifier == w) & (df.generator == s)].rejected.mean()
            if np.isnan(sw) or np.isnan(ws): continue
            n += 1; ok = sw > ws; wins += ok
            print(f"  {s:10s} {w:10s} {sw*100:7.1f}% {ws*100:7.1f}% "
                  f"{(sw-ws)*100:+8.1f}pp  {'OK' if ok else 'XX'}")
    if n:
        p = binomtest(wins, n, 0.5).pvalue
        print(f"\n  {wins}/{n} pairs in predicted direction   sign-test p = {p:.4f}")
        print("  Measures the RAW asymmetry (capability + detectability combined).")
    return wins, n


def permutation_test(df, domain, n_perm=2000, seed=0):
    """Shuffle verifier identity WITHIN error stratum: preserves how hard each error
    is, breaks the verifier-capability link. Honest p for the stratified effect."""
    per = _stratum_adjusted(df)
    if per is None:
        print(f"\n4. PERMUTATION [{domain}] skipped"); return None, None
    rng = np.random.default_rng(seed)
    obs = np.corrcoef(per.ver_acc, per.adj)[0, 1]
    null = np.empty(n_perm)
    for i in range(n_perm):
        sh = per.groupby("stratum")["ver_acc"].transform(lambda s: rng.permutation(s.values))
        null[i] = np.corrcoef(sh, per.adj)[0, 1]
    p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (n_perm + 1)
    print(f"\n{'='*76}\n4. PERMUTATION TEST [{domain}]\n{'='*76}")
    print(f"  observed r = {obs:+.4f}   null: mean={null.mean():+.4f} sd={null.std():.4f}")
    print(f"  95% null range [{np.percentile(null,2.5):+.4f}, {np.percentile(null,97.5):+.4f}]")
    print(f"  p = {p:.4f}  -> {'SIGNIFICANT' if p < 0.05 else 'NOT significant'}")
    return obs, p


# ── 5-8. robustness ───────────────────────────────────────────────────
def capacity_control(df, domain):
    """
    Mistral is 12B; the others are 70B-class. If the effect needs the small model,
    the claim is about SCALE, not capability. Re-estimate on frontier models only.
    """
    print(f"\n{'='*76}\n5. CAPACITY CONTROL — 70B-class only [{domain}]\n{'='*76}")
    d = df[df.verifier.isin(FRONTIER) & df.generator.isin(FRONTIER)]
    per = _stratum_adjusted(d)
    if per is None:
        print("  too few strata; skipping"); return None
    r = np.corrcoef(per.ver_acc, per.adj)[0, 1]
    full = _stratum_adjusted(df)
    r_full = np.corrcoef(full.ver_acc, full.adj)[0, 1] if full is not None else np.nan
    print(f"  r (frontier only) = {r:+.4f}   vs full-pool r = {r_full:+.4f}")
    print(f"  ({per.stratum.nunique()} errors, {len(per)} pairs)")
    print("  Sign flip or collapse here => the effect was driven by the 12B model.")
    return r


def leave_one_generator_out(df, domain):
    """Is the effect an artifact of whose errors are in the pool?"""
    print(f"\n{'='*76}\n6. LEAVE-ONE-GENERATOR-OUT [{domain}]\n{'='*76}")
    base = _stratum_adjusted(df)
    if base is None:
        print("  skipping"); return
    r_all = np.corrcoef(base.ver_acc, base.adj)[0, 1]
    print(f"  {'held-out generator':20s} {'r':>10s} {'change':>9s}")
    print(f"  {'(none - full)':20s} {r_all:+10.4f}")
    for g in sorted(df.generator.unique()):
        sub = _stratum_adjusted(df[df.generator != g])
        if sub is None:
            print(f"  {'drop ' + g:20s} {'n/a':>10s}"); continue
        r = np.corrcoef(sub.ver_acc, sub.adj)[0, 1]
        print(f"  {'drop ' + g:20s} {r:+10.4f} {r - r_all:+9.4f}")


def by_strategy(df, domain):
    """Does the verification strategy change how much capability matters?"""
    print(f"\n{'='*76}\n7. BY VERIFICATION STRATEGY [{domain}]\n{'='*76}")
    print(f"  {'strategy':10s} {'r':>10s} {'n pairs':>9s}")
    for s in ["direct", "cot", "rubric"]:
        sub = _stratum_adjusted(df[df.strategy == s])
        if sub is None:
            print(f"  {s:10s} {'n/a':>10s}"); continue
        r = np.corrcoef(sub.ver_acc, sub.adj)[0, 1]
        print(f"  {s:10s} {r:+10.4f} {len(sub):9d}")


def bootstrap_ci(df, domain, n_boot=2000, seed=0):
    """95% CI per verifier, resampling ERRORS (the independent unit), not rows."""
    print(f"\n{'='*76}\n8. BOOTSTRAP 95% CI — stratum-adjusted catch [{domain}]\n{'='*76}")
    per = _stratum_adjusted(df)
    if per is None:
        print("  skipping"); return
    strata = per.stratum.unique()
    rng = np.random.default_rng(seed)
    print(f"  {'verifier':10s} {'ver acc':>8s} {'adj catch':>11s} {'95% CI':>22s}")
    for m in sorted(df.attrs["acc"], key=lambda x: -df.attrs["acc"][x]):
        sub = per[per.verifier == m]
        if len(sub) == 0: continue
        boots = []
        for _ in range(n_boot):
            samp = rng.choice(strata, len(strata), replace=True)
            vals = per[per.stratum.isin(samp) & (per.verifier == m)].adj
            if len(vals): boots.append(vals.mean())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        star = "" if (lo < 0 < hi) else " *"
        print(f"  {m:10s} {df.attrs['acc'][m]*100:7.1f}% {sub.adj.mean()*100:+10.1f}pp "
              f"[{lo*100:+7.1f}, {hi*100:+7.1f}]{star}")
    print("  * = CI excludes zero.")


# ── 9. independent evidence (not confounded by detectability) ─────────
def difficulty_stratification(df, domain, mode="actual"):
    """
    About ITEMS, not model pairs, so detectability cannot confound it. Reports catch
    rate on wrong candidates only -- NOT overall accuracy, which mixes in true
    positives and is undefined where every generator succeeded.
    """
    print(f"\n{'='*76}\n9. DIFFICULTY STRATIFICATION [{domain}]\n{'='*76}")
    grades = load_or_build_grades(domain, mode)
    solved = {}
    for (item, m), ok in grades.items():
        solved[item] = solved.get(item, 0) + ok
    d = df.copy()
    d["n_solvers"] = d.item_id.map(solved)
    print(f"  {'generators solving item':26s} {'errors':>8s} {'catch rate':>12s}")
    for k in sorted(d.n_solvers.dropna().unique()):
        s = d[d.n_solvers == k]
        print(f"  {int(k)}/4 {'':22s} {s.groupby('stratum').ngroups:8d} {s.rejected.mean()*100:11.1f}%")
    print("  Rising catch rate with solvability = verification tracks the competence frontier.")


# ── 10. mechanism: do capable judges override the oracle? ─────────────
def override_analysis(domain, mode="actual"):
    """
    Code only. The code verifier prompt explicitly invites overriding execution
    ("you have the authority to mark the candidate as incorrect even when all tests
    passed"). If override rate rises with capability, that is the mechanism behind
    capability HURTING in the grounded domain.
    """
    if domain != "code":
        return
    print(f"\n{'='*76}\n10. MECHANISM — do capable judges override the oracle? [{domain}]\n{'='*76}")
    grades = load_or_build_grades(domain, mode)
    acc = {}
    for m in ["qwen", "deepseek", "llama", "mistral"]:
        t = [v for (i, g), v in grades.items() if g == m]
        acc[m] = sum(t) / len(t) if t else np.nan
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    rows = []
    for l in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        r = json.loads(l)
        if r["verifier_model"] == r["generator_model"]: continue
        if r.get("parsed_verdict") is None: continue
        rows.append({"verifier": r["verifier_model"],
                     "override": int(bool(r.get("overrode_passing_tests"))),
                     "exec_ok": r.get("execution_ran_successfully"),
                     "verdict": r["parsed_verdict"]})
    d = pd.DataFrame(rows)
    if d.empty:
        print("  no rows"); return
    print(f"  {'verifier':10s} {'gen acc':>8s} {'override rate':>14s} {'approved-despite-fail':>23s}")
    for m in sorted(acc, key=lambda x: -acc[x]):
        s = d[d.verifier == m]
        if len(s) == 0: continue
        failed = s[s.exec_ok == False]
        adf = failed.verdict.mean() * 100 if len(failed) else float("nan")
        print(f"  {m:10s} {acc[m]*100:7.1f}% {s.override.mean()*100:13.1f}% {adf:22.1f}%")
    print("  'override rate'          = execution PASSED but judge said incorrect")
    print("  'approved-despite-fail'  = execution FAILED but judge said correct")
    print("  If either rises with capability, capable judges are reasoning past the oracle.")


# ── 11. metric validity: is catch rate measuring judgment or just rejection? ──
def full_confusion_by_verifier(domain, mode="actual"):
    """
    Everything above is computed over WRONG candidates only, so it reports catch rate
    = TN/(TN+FP). That metric is maximised by rejecting everything: a judge that never
    approves scores 100% while being useless. Mistral posts the highest code catch rate
    (94.2%) while rejecting 22.5% of code that passed its own tests, which suggests the
    ranking is an artifact rather than a finding.

    This rebuilds over ALL candidates (correct and wrong) so both error directions are
    visible, and reports balanced accuracy -- the mean of the two directional rates --
    which a pure rejector cannot game.
    """
    print(f"\n{'='*76}\n11. METRIC VALIDITY — full confusion matrix [{domain}]\n{'='*76}")
    grades = load_or_build_grades(domain, mode)
    acc = {}
    for m in ["qwen", "deepseek", "llama", "mistral"]:
        t = [v for (i, g), v in grades.items() if g == m]
        acc[m] = sum(t) / len(t) if t else float("nan")

    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    cell = {}
    for l in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        r = json.loads(l)
        v = r.get("parsed_verdict")
        if v is None or r["verifier_model"] == r["generator_model"]:
            continue
        correct = grades.get((r["item_id"], r["generator_model"]), False)
        c = cell.setdefault(r["verifier_model"], {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
        if correct and v: c["tp"] += 1
        elif (not correct) and v: c["fp"] += 1
        elif (not correct) and (not v): c["tn"] += 1
        else: c["fn"] += 1

    rows = []
    for m, c in cell.items():
        tnr = c["tn"] / (c["tn"] + c["fp"]) if (c["tn"] + c["fp"]) else float("nan")
        tpr = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else float("nan")
        n = sum(c.values())
        rows.append({"verifier": m, "gen_acc": acc.get(m, float("nan")),
                     "catch_rate": tnr, "confirm_rate": tpr,
                     "balanced_acc": (tnr + tpr) / 2,
                     "overall_acc": (c["tp"] + c["tn"]) / n if n else float("nan")})
    d = pd.DataFrame(rows)

    print(f"  {'verifier':10s} {'gen acc':>8s} {'catch rate':>11s} {'confirm rate':>13s} "
          f"{'balanced acc':>13s} {'overall acc':>12s}")
    for _, r in d.sort_values("catch_rate", ascending=False).iterrows():
        print(f"  {r.verifier:10s} {r.gen_acc*100:7.1f}% {r.catch_rate*100:10.1f}% "
              f"{r.confirm_rate*100:12.1f}% {r.balanced_acc*100:12.1f}% {r.overall_acc*100:11.1f}%")
    print("  catch rate   = TN/(TN+FP), over WRONG candidates  (gameable by rejecting all)")
    print("  confirm rate = TP/(TP+FN), over CORRECT candidates (gameable by approving all)")
    print("  balanced acc = mean of the two; cannot be gamed by a constant response")

    by_catch = list(d.sort_values("catch_rate", ascending=False).verifier)
    by_bal = list(d.sort_values("balanced_acc", ascending=False).verifier)
    print(f"\n  ranking by catch rate   : {' > '.join(by_catch)}")
    print(f"  ranking by balanced acc : {' > '.join(by_bal)}")
    if by_catch != by_bal:
        print("  -> RANKINGS DISAGREE: catch rate is not a valid judge-quality metric here.")
    else:
        print("  -> rankings agree; catch rate is not misleading in this domain.")
    return d


# ── main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="actual", choices=["pilot", "actual"])
    ap.add_argument("--domains", nargs="+", default=DOMAINS)
    ap.add_argument("--n-perm", type=int, default=2000)
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()

    summary, pooled_w, pooled_n = [], 0, 0
    for dom in a.domains:
        suffix = ".jsonl" if a.mode == "actual" else "_pilot.jsonl"
        if not os.path.exists(os.path.join("data", "verified", f"{dom}{suffix}")):
            print(f"\n[{dom}] no verified data, skipping"); continue
        print(f"\n\n{'#'*76}\n#  {dom.upper()}   (grounding: {GROUNDING[dom]})\n{'#'*76}")
        df = build_oversight_frame(dom, a.mode)
        print(f"  rows: {len(df)} (wrong candidates, self-verification excluded)")

        oversight_matrix(df, dom)
        r, _ = critical_test(df, dom)
        w, n = sign_test_pairs(df, dom)
        pooled_w += w; pooled_n += n
        _, p = permutation_test(df, dom, a.n_perm)
        rc = capacity_control(df, dom)
        leave_one_generator_out(df, dom)
        by_strategy(df, dom)
        bootstrap_ci(df, dom, a.n_boot)
        difficulty_stratification(df, dom, a.mode)
        override_analysis(dom, a.mode)
        full_confusion_by_verifier(dom, a.mode)
        summary.append({"domain": dom, "grounding": GROUNDING[dom],
                        "r_stratified": r, "perm_p": p, "r_frontier": rc,
                        "sign_wins": w, "sign_n": n})

    print(f"\n\n{'#'*76}\n#  CROSS-DOMAIN SUMMARY\n{'#'*76}")
    print(f"  {'domain':9s} {'grounding':24s} {'r (strat)':>10s} {'perm p':>9s} "
          f"{'r (70B)':>9s} {'sign':>7s}")
    for s in summary:
        rs = f"{s['r_stratified']:+.4f}" if s["r_stratified"] is not None else "n/a"
        ps = f"{s['perm_p']:.4f}" if s["perm_p"] is not None else "n/a"
        rf = f"{s['r_frontier']:+.4f}" if s["r_frontier"] is not None else "n/a"
        print(f"  {s['domain']:9s} {s['grounding']:24s} {rs:>10s} {ps:>9s} {rf:>9s} "
              f"{s['sign_wins']}/{s['sign_n']:>5}")
    if pooled_n:
        from scipy.stats import binomtest
        print(f"\n  POOLED raw asymmetry: {pooled_w}/{pooled_n} pairs, "
              f"sign-test p = {binomtest(pooled_w, pooled_n, 0.5).pvalue:.2e}")
    print("\n  Read the r column against the grounding column: that interaction is the finding.")
