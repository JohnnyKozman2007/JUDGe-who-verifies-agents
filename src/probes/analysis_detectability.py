"""
Do stronger generators produce less detectable errors?

Primary analysis is an item-stratified conditional logit: within a single item,
compare how often judges catch a strong generator's error vs a weak one's. Item
strata remove difficulty as a confound BY CONSTRUCTION rather than by adjustment.

Self-verification rows (verifier == generator) are excluded throughout: a model
systematically approves its own errors, which would mechanically inflate the
undetectability of exactly the generators we are testing.

Reads committed data only. Writes nothing except a grade cache.
"""
import os, sys, json, argparse
import numpy as np
import pandas as pd
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from science_utils import grade_science_candidate, parse_science_for_item
from execution_grounding import run_candidate_code

DOMAINS = ["science", "math", "code"]
MODELS = ["qwen", "deepseek", "llama", "mistral"]


# ── Step 0: grade cache ───────────────────────────────────────────────
def load_or_build_grades(domain, mode="actual"):
    """
    Cache grades to disk. Code grading spawns 600 subprocesses; never redo it.

    Caches live in data/graded/ and are committed for reproducibility. They are
    DERIVED from data/generated/ -- if candidates are ever regenerated, delete this
    directory or every downstream number will be computed against stale grades.
    """
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    cache_dir = os.path.join("reports", "probes", "Do-stronger-models-make-mistakes-that-are-harder-to-catch")
    os.makedirs(cache_dir, exist_ok=True)
    cache = os.path.join(cache_dir, f"graded_{domain}{'_pilot' if mode=='pilot' else ''}.json")
    if os.path.exists(cache):
        return {tuple(k.split("|")): v for k, v in json.load(open(cache)).items()}

    raw = {json.loads(l)["item_id"]: json.loads(l)
           for l in open(os.path.join("data", "raw", f"{domain}{suffix}"), encoding="utf-8")}
    grades = {}
    if domain == "math":
        from report import grade_math          # single source of truth

    for line in open(os.path.join("data", "generated", f"{domain}{suffix}"), encoding="utf-8"):
        d = json.loads(line)
        ri = raw.get(d["item_id"])
        if not ri:
            continue
        for m, c in (d.get("candidates") or {}).items():
            if domain == "science":
                ok = grade_science_candidate(c, ri)
            elif domain == "math":
                ok = grade_math(c, ri["ground_truth"])
            else:
                ok = bool(c) and run_candidate_code(
                    c, ri["test"], entry_point=ri.get("entry_point")).ran_successfully
            grades[(d["item_id"], m)] = bool(ok)

    json.dump({f"{k[0]}|{k[1]}": v for k, v in grades.items()}, open(cache, "w"))
    print(f"  [{domain}] cached {len(grades)} grades -> {cache}")
    return grades


# ── Step 1: analysis frame ────────────────────────────────────────────
def build_frame(domain, mode="actual"):
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    grades = load_or_build_grades(domain, mode)

    gen_acc, gen_n = defaultdict(int), defaultdict(int)
    for (item, m), ok in grades.items():
        gen_acc[m] += ok
        gen_n[m] += 1
    acc = {m: gen_acc[m] / gen_n[m] for m in gen_n}

    difficulty = defaultdict(int)                 # how many generators solved each item
    for (item, m), ok in grades.items():
        difficulty[item] += ok

    rows = []
    for line in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        r = json.loads(line)
        v = r.get("parsed_verdict")
        if v is None:
            continue
        if r["verifier_model"] == r["generator_model"]:      # THREAT 2: drop self-verification
            continue
        if grades.get((r["item_id"], r["generator_model"]), False):
            continue                                          # wrong candidates only
        rows.append({
            "domain": domain,
            "item_id": r["item_id"],
            "generator": r["generator_model"],
            "verifier": r["verifier_model"],
            "frame": r["frame"],
            "strategy": r["strategy"],
            "gen_acc": acc[r["generator_model"]],
            "difficulty": difficulty[r["item_id"]],
            "rejected": int(v is False),                      # judge CAUGHT the error
        })
    df = pd.DataFrame(rows)
    df.attrs["acc"] = acc
    return df


# ── Step 2: PRIMARY — item-stratified conditional logit ───────────────
def primary(df, domain):
    from statsmodels.discrete.conditional_models import ConditionalLogit
    print(f"\n{'='*72}\nPRIMARY — item-stratified conditional logit [{domain}]\n{'='*72}")

    # keep only items with >=2 distinct generators erring: needed for within-item contrast
    keep = df.groupby("item_id")["generator"].nunique()
    keep = set(keep[keep >= 2].index)
    d = df[df.item_id.isin(keep)].copy()
    print(f"  items with >=2 erring generators: {len(keep)}   rows: {len(d)}")
    if len(keep) < 10:
        print("  too few strata; skipping"); return None

    y = d["rejected"].values
    X = pd.DataFrame({"gen_acc": d["gen_acc"].values})
    try:
        res = ConditionalLogit(y, X, groups=d["item_id"].values).fit(disp=0)
        b, p = res.params["gen_acc"], res.pvalues["gen_acc"]
        lo, hi = res.conf_int().loc["gen_acc"]
        print(f"  gen_acc coefficient = {b:+.3f}   p = {p:.3e}   95% CI [{lo:+.3f}, {hi:+.3f}]")
        print(f"  odds ratio per +10pp generator accuracy: {np.exp(b*0.10):.3f}")
        print("  NEGATIVE coefficient = stronger generators' errors are caught LESS -> claim supported")
    except Exception as e:
        print(f"  conditional logit failed: {e}")
        res = None

    # per-generator adjusted rates, within-item demeaned
    d["item_mean"] = d.groupby("item_id")["rejected"].transform("mean")
    d["adj"] = d["rejected"] - d["item_mean"]
    print(f"\n  {'generator':10s} {'gen acc':>8s} {'raw catch':>10s} {'item-adj':>10s} {'n':>7s}")
    for m in sorted(df.attrs["acc"], key=lambda x: -df.attrs["acc"][x]):
        s = d[d.generator == m]
        if len(s) == 0: continue
        print(f"  {m:10s} {df.attrs['acc'][m]*100:7.1f}% {s.rejected.mean()*100:9.1f}% "
              f"{s.adj.mean()*100:+9.1f}pp {len(s):7d}")
    return res


# ── Step 3: robustness — thresholds + continuous outcome ──────────────
def robustness(df, domain):
    print(f"\n{'='*72}\nROBUSTNESS — undetectability definition [{domain}]\n{'='*72}")
    per = df.groupby(["item_id", "generator"]).agg(
        approve_rate=("rejected", lambda s: 1 - s.mean()),
        n=("rejected", "size"),
        gen_acc=("gen_acc", "first"),
        difficulty=("difficulty", "first")).reset_index()
    per = per[per.n >= 20]

    print(f"  {'generator':10s} {'gen acc':>8s} " +
          "".join(f"{t:>9s}" for t in ["=100%", ">=90%", ">=75%"]) + f"{'mean appr':>11s}")
    for m in sorted(df.attrs["acc"], key=lambda x: -df.attrs["acc"][x]):
        s = per[per.generator == m]
        if len(s) == 0: continue
        row = f"  {m:10s} {df.attrs['acc'][m]*100:7.1f}% "
        for t in [1.0, 0.9, 0.75]:
            row += f"{(s.approve_rate >= t).mean()*100:8.1f}%"
        row += f"{s.approve_rate.mean()*100:10.1f}%"
        print(row)

    # continuous outcome with item fixed effects (within-item demeaning)
    per["adj_appr"] = per.approve_rate - per.groupby("item_id").approve_rate.transform("mean")
    sub = per[per.groupby("item_id").item_id.transform("size") >= 2]
    if len(sub) > 10:
        from scipy.stats import pearsonr, spearmanr
        r, p = pearsonr(sub.gen_acc, sub.adj_appr)
        rs, ps = spearmanr(sub.gen_acc, sub.adj_appr)
        print(f"\n  continuous, item-demeaned:  Pearson r={r:+.3f} p={p:.2e} | "
              f"Spearman rho={rs:+.3f} p={ps:.2e}   (n={len(sub)} item-generator pairs)")
        print("  POSITIVE = stronger generators' errors approved more -> claim supported")

def permutation_test(df, domain, n_perm=2000, seed=0):
    """
    Honest p-value for the generator-strength effect.

    gen_acc takes only 4 distinct values, so the conditional-logit p-value is
    pseudo-replicated (thousands of rows, four clusters). This permutes generator
    identity WITHIN item: it preserves item difficulty and the marginal spread of
    approval rates, while breaking any link between which generator wrote the error
    and how often judges caught it. Requires >=2 erring generators per item so there
    is something to permute.
    """
    rng = np.random.default_rng(seed)
    per = df.groupby(["item_id", "generator"]).agg(
        appr=("rejected", lambda s: 1 - s.mean()),
        gen_acc=("gen_acc", "first")).reset_index()
    per = per[per.groupby("item_id")["generator"].transform("size") >= 2].copy()
    if len(per) < 20:
        print(f"\n  PERMUTATION TEST [{domain}] skipped: only {len(per)} pairs")
        return None, None
    per["adj"] = per.appr - per.groupby("item_id").appr.transform("mean")

    obs = np.corrcoef(per.gen_acc, per.adj)[0, 1]
    null = np.empty(n_perm)
    for i in range(n_perm):
        shuffled = per.groupby("item_id")["gen_acc"].transform(
            lambda s: rng.permutation(s.values))
        null[i] = np.corrcoef(shuffled, per.adj)[0, 1]
    p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (n_perm + 1)

    print(f"\n  PERMUTATION TEST [{domain}]  ({n_perm} perms, "
          f"{per.item_id.nunique()} items, {len(per)} item-generator pairs)")
    print(f"    observed r = {obs:+.4f}")
    print(f"    null r: mean={null.mean():+.4f} sd={null.std():.4f} "
          f"95% range [{np.percentile(null,2.5):+.4f}, {np.percentile(null,97.5):+.4f}]")
    print(f"    p = {p:.4f}  -> {'SIGNIFICANT' if p < 0.05 else 'NOT significant'}")
    return obs, p

def _item_demeaned(df):
    """Per (item, generator) approval rate, demeaned within item. Shared by the
    robustness checks below so they all measure the same quantity."""
    per = df.groupby(["item_id", "generator"]).agg(
        appr=("rejected", lambda s: 1 - s.mean()),
        gen_acc=("gen_acc", "first")).reset_index()
    per = per[per.groupby("item_id")["generator"].transform("size") >= 2].copy()
    if len(per) < 20:
        return None
    per["adj"] = per.appr - per.groupby("item_id").appr.transform("mean")
    return per


def leave_one_verifier_out(df, domain):
    """
    Is the effect an artifact of one judge? Mistral approves ~81% of everything, so
    if it alone drove the correlation the finding would be about that judge, not
    about generators. Re-estimates with each judge held out in turn.
    """
    print(f"\n{'='*72}\nROBUSTNESS — leave-one-verifier-out [{domain}]\n{'='*72}")
    base = _item_demeaned(df)
    if base is None:
        print("  too few pairs; skipping"); return
    r_all = np.corrcoef(base.gen_acc, base.adj)[0, 1]
    print(f"  {'held-out judge':18s} {'r':>10s} {'change':>9s}")
    print(f"  {'(none - full)':18s} {r_all:+10.4f} {'':>9s}")
    for v in sorted(df.verifier.unique()):
        sub = _item_demeaned(df[df.verifier != v])
        if sub is None:
            print(f"  {'drop ' + v:18s} {'n/a':>10s}"); continue
        r = np.corrcoef(sub.gen_acc, sub.adj)[0, 1]
        print(f"  {'drop ' + v:18s} {r:+10.4f} {r - r_all:+9.4f}")
    print("  Effect should survive every single-judge exclusion.")


def by_strategy(df, domain):
    """
    Does better prompting mitigate the gradient? Rubric lowers overall FPR by ~9pp,
    so if it also flattened this effect it would be a usable defence. Reported
    separately because a null here is itself a finding.
    """
    print(f"\n{'='*72}\nROBUSTNESS — effect by verification strategy [{domain}]\n{'='*72}")
    print(f"  {'strategy':10s} {'r':>10s} {'n pairs':>9s}")
    for s in ["direct", "cot", "rubric"]:
        sub = _item_demeaned(df[df.strategy == s])
        if sub is None:
            print(f"  {s:10s} {'n/a':>10s}"); continue
        r = np.corrcoef(sub.gen_acc, sub.adj)[0, 1]
        print(f"  {s:10s} {r:+10.4f} {len(sub):9d}")
    print("  Similar r across strategies = prompting does NOT mitigate the gradient.")


def bootstrap_ci(df, domain, n_boot=2000, seed=0):
    """
    95% CI on each generator's item-adjusted approval rate, resampling ITEMS (the
    independent unit) rather than rows. Point estimates alone cannot show whether
    two generators genuinely differ; non-overlapping CIs can.
    """
    print(f"\n{'='*72}\nBOOTSTRAP 95% CI — item-adjusted approval [{domain}]\n{'='*72}")
    per = _item_demeaned(df)
    if per is None:
        print("  too few pairs; skipping"); return
    items = per.item_id.unique()
    rng = np.random.default_rng(seed)
    print(f"  {'generator':10s} {'gen acc':>8s} {'adj appr':>10s} {'95% CI':>22s}")
    for g in sorted(per.gen_acc.unique(), reverse=True):
        name = df[df.gen_acc == g].generator.iloc[0]
        boots = []
        for _ in range(n_boot):
            samp = rng.choice(items, len(items), replace=True)
            vals = per[per.item_id.isin(samp) & (per.gen_acc == g)].adj
            if len(vals):
                boots.append(vals.mean())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        star = "" if (lo < 0 < hi) else " *"
        print(f"  {name:10s} {g*100:7.1f}% {per[per.gen_acc == g].adj.mean()*100:+9.1f}pp "
              f"[{lo*100:+7.1f}, {hi*100:+7.1f}]{star}")
    print("  * = CI excludes zero. Non-overlapping CIs between two generators means")
    print("    their difference is real (relevant to math's non-monotonicity).")


# ── Step 4: mechanism — is it mediated by judge agreement? ────────────
def mechanism(df, domain, mode="actual"):
    """Science/math only: does the judge independently arrive at the same wrong answer?"""
    if domain == "code":
        print(f"\n  [mechanism] skipped for code (no scalar answer to compare)"); return
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    raw = {json.loads(l)["item_id"]: json.loads(l)
           for l in open(os.path.join("data", "raw", f"{domain}{suffix}"), encoding="utf-8")}
    ans = {}
    for line in open(os.path.join("data", "generated", f"{domain}{suffix}"), encoding="utf-8"):
        d = json.loads(line); ri = raw.get(d["item_id"])
        if not ri: continue
        for m, c in (d.get("candidates") or {}).items():
            if domain == "science":
                ans[(d["item_id"], m)] = parse_science_for_item(c, ri)["letter"]
            else:
                import re
                mm = re.findall(r"<answer>(.*?)</answer>", c or "", re.S)
                ans[(d["item_id"], m)] = mm[-1].strip() if mm else None

    print(f"\n{'='*72}\nMECHANISM — does judge agreement explain it? [{domain}]\n{'='*72}")
    d = df.copy()
    d["judge_agrees"] = [
        1 if (ans.get((r.item_id, r.generator)) is not None
              and ans.get((r.item_id, r.generator)) == ans.get((r.item_id, r.verifier))) else 0
        for r in d.itertuples()]
    print(f"  {'generator':10s} {'gen acc':>8s} {'judges agreeing':>16s} {'catch|agree':>12s} {'catch|disagree':>15s}")
    for m in sorted(df.attrs["acc"], key=lambda x: -df.attrs["acc"][x]):
        s = d[d.generator == m]
        if len(s) == 0: continue
        a, dis = s[s.judge_agrees == 1], s[s.judge_agrees == 0]
        print(f"  {m:10s} {df.attrs['acc'][m]*100:7.1f}% {s.judge_agrees.mean()*100:15.1f}% "
              f"{a.rejected.mean()*100 if len(a) else float('nan'):11.1f}% "
              f"{dis.rejected.mean()*100 if len(dis) else float('nan'):14.1f}%")
    print("  If 'judges agreeing' rises with gen_acc, agreement MEDIATES the effect.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="actual", choices=["pilot", "actual"])
    ap.add_argument("--domains", nargs="+", default=DOMAINS)
    a = ap.parse_args()
    for dom in a.domains:
        if not os.path.exists(os.path.join("data", "verified",
                f"{dom}{'_pilot.jsonl' if a.mode=='pilot' else '.jsonl'}")):
            print(f"\n[{dom}] no verified data, skipping"); continue
        print(f"\n\n{'#'*72}\n#  {dom.upper()}\n{'#'*72}")
        df = build_frame(dom, a.mode)
        print(f"  rows (wrong candidates, self-verification excluded): {len(df)}")
        primary(df, dom)
        robustness(df, dom)
        permutation_test(df, dom)
        leave_one_verifier_out(df, dom)
        by_strategy(df, dom)
        bootstrap_ci(df, dom)
        mechanism(df, dom, a.mode)
