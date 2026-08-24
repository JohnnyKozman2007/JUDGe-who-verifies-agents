"""
Can ensembling repair an unreliable judge?

DESIGN NOTE 1 -- there is no single "ensemble". An ensemble of n judges has n decision
rules (approve if >= k of n approve). Comparing "majority of 4" (needs 3/4 = 75%) with
"majority of 3" (needs 2/3 = 67%) compares thresholds, not ensembles. Everything here
sweeps k explicitly.

DESIGN NOTE 2 -- primary metric is BALANCED ACCURACY. The oversight analysis showed
error-catch rate is maximised by rejecting everything, so it cannot rank judges or
ensembles. Catch/FPR are still printed for continuity with earlier numbers.

DESIGN NOTE 3 -- two judge pools are reported:
  * LOO pool  (deployment-realistic): for each candidate, the judges are the three
    models that did NOT write it. Always exactly 3, never self-verifying.
  * FULL pool (composition study): all four judges including self-verification, which
    is the only way to evaluate 4-member subsets at all.

Reads committed data + the grade cache. Writes nothing.
"""
import os, sys, json, argparse, itertools
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_detectability import load_or_build_grades

DOMAINS = ["science", "math", "code"]
MODELS = ["qwen", "deepseek", "llama", "mistral"]
VCOLS = [f"v_{m}" for m in MODELS]


# ── Step 1: vote frame ────────────────────────────────────────────────
def build_vote_frame(domain, mode="actual", frame="neutral"):
    """
    One row per (item, generator, strategy); each judge's verdict as a column.
    Neutral frame only: self/other framing is an experimental manipulation, not a
    deployment condition, so it would confound an ensembling study.
    """
    grades = load_or_build_grades(domain, mode)
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    votes = {}
    for l in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        r = json.loads(l)
        v = r.get("parsed_verdict")
        if v is None or r["frame"] != frame:
            continue
        votes.setdefault((r["item_id"], r["generator_model"], r["strategy"]), {})[
            r["verifier_model"]] = bool(v)
    rows = []
    for (item, gen, strat), d in votes.items():
        row = {"item_id": item, "generator": gen, "strategy": strat,
               "truth": bool(grades.get((item, gen), False))}
        row.update({f"v_{m}": d.get(m) for m in MODELS})
        rows.append(row)
    df = pd.DataFrame(rows)
    # LOO pool: how many of the three non-authors approved
    df["n_loo"] = sum(
        ((df.generator != m) & (df[f"v_{m}"] == True)).astype(int) for m in MODELS)
    df["n_loo_valid"] = sum(
        ((df.generator != m) & (df[f"v_{m}"].notna())).astype(int) for m in MODELS)
    return df


def evaluate(truth, pred):
    truth = np.asarray(truth, dtype=bool); pred = np.asarray(pred, dtype=bool)
    tp = int((truth & pred).sum());   fp = int((~truth & pred).sum())
    tn = int((~truth & ~pred).sum()); fn = int((truth & ~pred).sum())
    tnr = tn / (tn + fp) if (tn + fp) else np.nan
    tpr = tp / (tp + fn) if (tp + fn) else np.nan
    return {"n": len(truth), "acc": (tp + tn) / len(truth) if len(truth) else np.nan,
            "catch": tnr, "confirm": tpr, "bal_acc": (tnr + tpr) / 2,
            "fpr": fp / (fp + tn) if (fp + tn) else np.nan}


# ── Step 2a: the k-of-3 sweep on the deployment-realistic pool ────────
def loo_sweep(df, domain, strategy):
    """Judges = the three models that did not write the candidate. No self-verification."""
    d = df[(df.strategy == strategy) & (df.n_loo_valid == 3)]
    print(f"\n{'='*78}\n2a. k-of-3 SWEEP — leave-one-out pool [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 50:
        print("  too few rows"); return None
    print(f"  n = {len(d)} candidates, judges = 3 non-authors\n")
    print(f"  {'rule':10s} {'bal acc':>9s} {'acc':>8s} {'catch':>8s} {'confirm':>9s} {'FPR':>8s}")
    out = []
    for k in (1, 2, 3):
        r = evaluate(d.truth.values, (d.n_loo >= k).values)
        r.update({"rule": f"{k}-of-3", "k": k})
        out.append(r)
        print(f"  {r['rule']:10s} {r['bal_acc']*100:8.1f}% {r['acc']*100:7.1f}% "
              f"{r['catch']*100:7.1f}% {r['confirm']*100:8.1f}% {r['fpr']*100:7.1f}%")
    # every single judge, on the same rows, when it is not the author
    print(f"\n  {'single':10s} {'bal acc':>9s} {'acc':>8s} {'catch':>8s} {'confirm':>9s} {'n':>7s}")
    singles = []
    for m in MODELS:
        s = d[(d.generator != m) & (d[f"v_{m}"].notna())]
        if len(s) < 30: continue
        r = evaluate(s.truth.values, s[f"v_{m}"].values)
        r["model"] = m; singles.append(r)
        print(f"  {m:10s} {r['bal_acc']*100:8.1f}% {r['acc']*100:7.1f}% "
              f"{r['catch']*100:7.1f}% {r['confirm']*100:8.1f}% {r['n']:7d}")
    best_e = max(out, key=lambda r: r["bal_acc"])
    best_s = max(singles, key=lambda r: r["bal_acc"])
    print(f"\n  best ensemble rule : {best_e['rule']:8s} bal acc {best_e['bal_acc']*100:.1f}%")
    print(f"  best single judge  : {best_s['model']:8s} bal acc {best_s['bal_acc']*100:.1f}%")
    print(f"  ensemble advantage : {(best_e['bal_acc']-best_s['bal_acc'])*100:+.1f}pp "
          f"(NOTE: both selected in-sample; see Step 3)")
    return pd.DataFrame(out)


# ── Step 2b-clean: subsets WITHOUT self-verification (primary) ────────
def subset_sweep_noself(df, domain, strategy):
    """
    PRIMARY composition study. Subsets of size 2-3 drawn only from judges that did NOT
    write the candidate, so no model ever grades its own work. Size 4 is impossible
    here by construction -- with four models, one is always the author.

    subset_sweep() below keeps the full pool for continuity, but its counts are
    contaminated by self-preference and should not be quoted.
    """
    d = df[df.strategy == strategy]
    print(f"\n{'='*78}\n2b. SUBSETS WITHOUT SELF-VERIFICATION [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 50:
        print("  too few rows"); return None

    out = []
    for size in (1, 2, 3):
        for combo in itertools.combinations(MODELS, size):
            cols = [f"v_{m}" for m in combo]
            # keep only candidates none of these judges wrote
            sub = d[~d.generator.isin(combo)].dropna(subset=cols)
            if len(sub) < 50:
                continue
            ap = sub[cols].sum(axis=1)
            for k in range(1, size + 1):
                r = evaluate(sub.truth.values, (ap >= k).values)
                r.update({"members": "+".join(combo), "size": size, "k": k,
                          "rule": f"{k}-of-{size}", "n_rows": len(sub)})
                out.append(r)
    if not out:
        print("  no eligible subsets"); return None
    res = pd.DataFrame(out)

    print(f"  best rule at each size (judges never grade their own work):")
    print(f"  {'size':>5s} {'members':28s} {'rule':9s} {'bal acc':>9s} {'n':>7s}")
    for size in (1, 2, 3):
        s = res[res["size"] == size]
        if s.empty: continue
        b = s.nlargest(1, "bal_acc").iloc[0]
        print(f"  {size:5d} {b.members:28s} {b['rule']:9s} {b.bal_acc*100:8.1f}% {b.n_rows:7d}")

    best_single = res[res["size"] == 1].bal_acc.max()
    multi = res[res["size"] > 1]
    better = multi[multi.bal_acc > best_single]
    print(f"\n  best single judge: {best_single*100:.1f}% balanced accuracy")
    print(f"  multi-judge rules that beat it: {len(better)} / {len(multi)}")
    if len(better):
        b = better.nlargest(1, "bal_acc").iloc[0]
        print(f"    best: {b.members} [{b['rule']}] {b.bal_acc*100:.1f}% "
              f"({(b.bal_acc-best_single)*100:+.1f}pp)")
    print("  NOTE: single-judge and multi-judge rows are evaluated on different candidate")
    print("        subsets (each excludes its own members' authorship), so treat the")
    print("        comparison as indicative; Step 3's cross-validation is the formal test.")
    return res


# ── Step 2c: all subsets x all thresholds (full pool, CONTAMINATED) ───
def subset_sweep(df, domain, strategy):
    """
    Retained for continuity only. Uses the FULL pool, which INCLUDES models grading
    their own output, so self-preference inflates both baselines and ensembles.
    Quote subset_sweep_noself() instead.
    """
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n2c. ALL SUBSETS — full pool  [CONTAMINATED: includes self-verification]\n"
          f"    [{domain} / {strategy}]  -- see 2b for the clean version\n{'='*78}")
    if len(d) < 50:
        print("  too few complete rows"); return None
    print(f"  n = {len(d)} candidates with all 4 verdicts (self-verification INCLUDED)\n")
    out = []
    for size in range(1, 5):
        for combo in itertools.combinations(MODELS, size):
            cols = [f"v_{m}" for m in combo]
            ap = d[cols].sum(axis=1)
            for k in range(1, size + 1):
                r = evaluate(d.truth.values, (ap >= k).values)
                r.update({"members": "+".join(combo), "size": size, "k": k,
                          "rule": f"{k}-of-{size}"})
                out.append(r)
    res = pd.DataFrame(out)
    print(f"  best rule at each ensemble size (by balanced accuracy):")
    print(f"  {'size':>5s} {'members':34s} {'rule':9s} {'bal acc':>9s}")
    for size in range(1, 5):
        b = res[res["size"] == size].nlargest(1, "bal_acc").iloc[0]
        print(f"  {size:5d} {b.members:34s} {b['rule']:9s} {b.bal_acc*100:8.1f}%")
    best_single = res[res["size"] == 1].bal_acc.max()
    better = res[(res["size"] > 1) & (res.bal_acc > best_single)]
    print(f"\n  best single judge: {best_single*100:.1f}% balanced accuracy")
    print(f"  multi-judge rules that beat it: {len(better)} / {len(res[res['size']>1])}")
    if len(better):
        b = better.nlargest(1, "bal_acc").iloc[0]
        print(f"    best: {b.members} [{b['rule']}] {b.bal_acc*100:.1f}% "
              f"({(b.bal_acc-best_single)*100:+.1f}pp)")
    return res


# ── Step 3: cross-validated comparison ────────────────────────────────
def cv_comparison(df, domain, strategy, n_splits=50, seed=0):
    """
    Selecting the best judge (or rule) after seeing all results is selection on the
    test set. Here both are chosen on half the ITEMS and scored on the other half, so
    ensemble and single get the same handicap.
    """
    from scipy.stats import wilcoxon
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n3. CROSS-VALIDATED COMPARISON [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 100:
        print("  too few rows"); return
    items = d.item_id.unique(); rng = np.random.default_rng(seed)
    singles, ensembles = [], []
    for _ in range(n_splits):
        perm = rng.permutation(items)
        tr = d[d.item_id.isin(set(perm[:len(perm) // 2]))]
        te = d[d.item_id.isin(set(perm[len(perm) // 2:]))]
        if len(tr) < 20 or len(te) < 20: continue
        bm = max(MODELS, key=lambda m: evaluate(tr.truth.values, tr[f"v_{m}"].values)["bal_acc"])
        singles.append(evaluate(te.truth.values, te[f"v_{bm}"].values)["bal_acc"])
        best, bs = None, -np.inf
        for size in range(2, 5):
            for combo in itertools.combinations(MODELS, size):
                cols = [f"v_{m}" for m in combo]
                for k in range(1, size + 1):
                    s = evaluate(tr.truth.values, (tr[cols].sum(axis=1) >= k).values)["bal_acc"]
                    if s > bs: bs, best = s, (cols, k)
        cols, k = best
        ensembles.append(evaluate(te.truth.values, (te[cols].sum(axis=1) >= k).values)["bal_acc"])
    singles, ensembles = np.array(singles), np.array(ensembles)
    print(f"  {n_splits} random item splits, selection on train half, scored on test half")
    print(f"  best single   : {singles.mean()*100:6.2f}%  (sd {singles.std()*100:.2f})")
    print(f"  best ensemble : {ensembles.mean()*100:6.2f}%  (sd {ensembles.std()*100:.2f})")
    diff = ensembles - singles
    try: p = wilcoxon(ensembles, singles).pvalue
    except Exception: p = np.nan
    print(f"  ensemble - single: {diff.mean()*100:+.2f}pp   paired Wilcoxon p = {p:.4f}")
    print(f"  ensemble wins in {(diff > 0).mean()*100:.0f}% of splits")


# ── Step 4: why not? independence + agreement ─────────────────────────
def independence_test(df, domain, strategy, n_perm=2000, seed=0):
    """
    Permutation null: shuffle each judge's verdicts across candidates INDEPENDENTLY.
    Preserves each judge's marginal approval rate, destroys cross-judge correlation.
    Observed unanimity above the null => correlated errors => voting cannot help.
    """
    d = df[(df.strategy == strategy) & (~df.truth)].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n4. INDEPENDENCE TEST — wrong answers only [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 50:
        print("  too few wrong candidates"); return
    obs = float((d[VCOLS].sum(axis=1) == 4).mean())
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    arrs = [d[c].values.astype(bool) for c in VCOLS]
    for i in range(n_perm):
        sh = np.column_stack([rng.permutation(a) for a in arrs])
        null[i] = (sh.sum(axis=1) == 4).mean()
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    print(f"  n = {len(d)} wrong candidates")
    print(f"  ALL FOUR judges approved: observed {obs*100:.1f}%")
    print(f"    independence null     : {null.mean()*100:.1f}%  (sd {null.std()*100:.2f})")
    print(f"    excess {(obs-null.mean())*100:+.1f}pp = {obs/max(null.mean(),1e-9):.1f}x   p = {p:.4f}")
    print(f"  -> {'CORRELATED errors: voting cannot repair them' if p < .05 else 'no excess correlation detected'}")

    from sklearn.metrics import cohen_kappa_score
    print(f"\n  pairwise agreement beyond chance (Cohen's kappa), wrong answers:")
    ks = []
    for a, b in itertools.combinations(MODELS, 2):
        k = cohen_kappa_score(d[f"v_{a}"].astype(int), d[f"v_{b}"].astype(int))
        ks.append(k)
        print(f"    {a:9s} vs {b:9s}  kappa = {k:+.3f}")
    print(f"    mean kappa = {np.mean(ks):+.3f}   (0 = independent, 1 = identical)")


# ── Step 5: the ceiling ───────────────────────────────────────────────
def oracle_ceiling(df, domain, strategy):
    """Upper bound for ANY aggregation scheme: an oracle picking the right judge per item."""
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n5. ORACLE CEILING [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 50:
        print("  too few rows"); return
    corr = d[VCOLS].eq(d.truth, axis=0)
    print(f"  at least one judge correct (oracle) : {corr.any(axis=1).mean()*100:5.1f}%")
    print(f"  all four judges correct             : {corr.all(axis=1).mean()*100:5.1f}%")
    print(f"  no judge correct                    : {(~corr.any(axis=1)).mean()*100:5.1f}%")
    print("  Large gap between oracle and best ensemble => aggregation is the bottleneck.")
    print("  Small gap => the judges simply lack the information; no scheme can help.")


# ── Step 6: mechanism — does decorrelation buy anything? ──────────────
def cv_gain_ci(df, domain, strategy, n_splits=200, seed=0):
    """
    Per-split cross-validated ensemble gain with a percentile CI over item splits.

    This replaces a between-domain significance test. Comparing splits across domains
    with a rank test would treat 200 resamples of the same ~150 items as independent
    observations -- the same pseudo-replication trap flagged elsewhere in this project,
    and it produced absurd p-values (1e-66). The CI is the honest summary: read whether
    it excludes zero, and compare CIs across domains by eye.
    """
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n6. CROSS-VALIDATED GAIN + CI [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 100:
        print("  too few rows"); return None
    items = d.item_id.unique(); rng = np.random.default_rng(seed)
    gains = []
    for _ in range(n_splits):
        perm = rng.permutation(items)
        tr = d[d.item_id.isin(set(perm[:len(perm) // 2]))]
        te = d[d.item_id.isin(set(perm[len(perm) // 2:]))]
        if len(tr) < 20 or len(te) < 20: continue
        bm = max(MODELS, key=lambda m: evaluate(tr.truth.values, tr[f"v_{m}"].values)["bal_acc"])
        s = evaluate(te.truth.values, te[f"v_{bm}"].values)["bal_acc"]
        best, bs = None, -np.inf
        for size in range(2, 5):
            for combo in itertools.combinations(MODELS, size):
                cols = [f"v_{m}" for m in combo]
                for k in range(1, size + 1):
                    v = evaluate(tr.truth.values, (tr[cols].sum(axis=1) >= k).values)["bal_acc"]
                    if v > bs: bs, best = v, (cols, k)
        cols, k = best
        gains.append((evaluate(te.truth.values, (te[cols].sum(axis=1) >= k).values)["bal_acc"] - s) * 100)
    g = np.array(gains)
    lo, hi = np.percentile(g, [2.5, 97.5])
    excl = "EXCLUDES zero -> reliable effect" if (lo > 0 or hi < 0) else "includes zero -> no reliable effect"
    print(f"  ensemble - best single = {g.mean():+.2f}pp   95% CI [{lo:+.2f}, {hi:+.2f}]")
    print(f"  {len(g)} item splits;  CI {excl}")
    return g


def diversity_gain(df, domain, strategy):
    """
    CONFOUNDED -- reported for transparency, not as evidence.

    Intended test: do subsets whose members agree less (low kappa) gain more from
    ensembling? In this judge pool the low-kappa subsets are exactly the ones
    containing mistral, which is simply a weak judge, so "diverse" and "contains a bad
    member" are inseparable. The correlation therefore comes out POSITIVE, which is
    the opposite of the mechanism and is an artifact.

    The clean mechanism evidence is the CROSS-DOMAIN pattern (see cv_gain_ci and
    plot_ensemble.py figure 3): the judge pool is held fixed while grounding varies,
    so correlation is isolated. Do not quote the number below.
    """
    from sklearn.metrics import cohen_kappa_score
    from scipy.stats import pearsonr
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    print(f"\n{'='*78}\n6. MECHANISM — diversity vs ensemble gain [{domain} / {strategy}]\n{'='*78}")
    if len(d) < 50:
        print("  too few rows"); return
    wrong = d[~d.truth]
    kap = {}
    for a, b in itertools.combinations(MODELS, 2):
        kap[(a, b)] = kap[(b, a)] = cohen_kappa_score(
            wrong[f"v_{a}"].astype(int), wrong[f"v_{b}"].astype(int))
    rows = []
    for size in range(2, 5):
        for combo in itertools.combinations(MODELS, size):
            cols = [f"v_{m}" for m in combo]
            best_member = max(evaluate(d.truth.values, d[c].values)["bal_acc"] for c in cols)
            best_rule = max(evaluate(d.truth.values, (d[cols].sum(axis=1) >= k).values)["bal_acc"]
                            for k in range(1, size + 1))
            mk = np.mean([kap[(a, b)] for a, b in itertools.combinations(combo, 2)])
            rows.append({"members": "+".join(combo), "size": size, "mean_kappa": mk,
                         "gain": best_rule - best_member})
    r = pd.DataFrame(rows)
    print(f"  {'members':34s} {'mean kappa':>11s} {'gain over best member':>23s}")
    for _, x in r.sort_values("mean_kappa").iterrows():
        print(f"  {x.members:34s} {x.mean_kappa:+10.3f} {x.gain*100:+22.1f}pp")
    if len(r) > 3:
        cc, pp = pearsonr(r.mean_kappa, r.gain)
        print(f"\n  correlation(kappa, gain) = {cc:+.3f}  p = {pp:.4f}")
        print("  *** CONFOUNDED -- DO NOT QUOTE. Low-kappa subsets here are the ones")
        print("      containing the weakest judge, so diversity and incompetence are")
        print("      inseparable. Use the cross-domain comparison instead. ***")


# ── main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="actual", choices=["pilot", "actual"])
    ap.add_argument("--domains", nargs="+", default=DOMAINS)
    ap.add_argument("--strategies", nargs="+", default=["cot"],
                    help="primary is cot; pass 'direct cot rubric' for the sensitivity sweep")
    ap.add_argument("--frame", default="neutral")
    ap.add_argument("--n-perm", type=int, default=2000)
    a = ap.parse_args()

    for dom in a.domains:
        suffix = ".jsonl" if a.mode == "actual" else "_pilot.jsonl"
        if not os.path.exists(os.path.join("data", "verified", f"{dom}{suffix}")):
            print(f"\n[{dom}] no verified data, skipping"); continue
        df = build_vote_frame(dom, a.mode, a.frame)
        for strat in a.strategies:
            print(f"\n\n{'#'*78}\n#  {dom.upper()}  /  strategy={strat}  /  frame={a.frame}\n{'#'*78}")
            loo_sweep(df, dom, strat)
            subset_sweep_noself(df, dom, strat)
            subset_sweep(df, dom, strat)
            cv_comparison(df, dom, strat)
            independence_test(df, dom, strat, a.n_perm)
            oracle_ceiling(df, dom, strat)
            cv_gain_ci(df, dom, strat)
            diversity_gain(df, dom, strat)
