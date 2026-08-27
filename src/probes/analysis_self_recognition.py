"""
Can a model recognise its own output -- and does that explain self-preference?

Five analyses:
  1. Accuracy vs the 25% chance floor, per model, with exact binomial CIs
  2. POSITION BIAS -- the verification experiment found an ~11pp bias toward option A,
     so a model that simply favours a slot would look like it recognises itself
  3. QUALITY CONFOUND -- a model might pick the BEST answer rather than its own; if its
     own answers are better than average, that mimics recognition
  4. DISTINGUISHABILITY -- in multiple choice all four models may reach the same letter,
     making recognition impossible for reasons that have nothing to do with self-knowledge
  5. MEDIATION -- the payoff. Does recognising its own answer predict APPROVING it?
     This is what links the probe back to the verification results.

Reads the probe output plus committed verification data. Writes nothing.
"""
import os, sys, json, argparse, itertools
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_detectability import load_or_build_grades
from science_utils import parse_science_for_item

MODELS = ["qwen", "deepseek", "llama", "mistral"]

# Full test family for multiple-comparison correction: 4 models x 3 domains. Fixed
# rather than derived from the current run, so a single-domain invocation still
# corrects against the whole family the claim is made over.
N_TESTS_FAMILY = 12


def load_probe(domain, mode="actual"):
    p = os.path.join("data", "self_recognition",
                     f"{domain}{'' if mode == 'actual' else '_pilot'}.jsonl")
    if not os.path.exists(p):
        print(f"  no probe data at {p}"); return None
    return pd.DataFrame([json.loads(l) for l in open(p, encoding="utf-8")])


# ── 1. accuracy vs chance ─────────────────────────────────────────────
def accuracy(df, domain):
    from scipy.stats import binomtest
    print(f"\n{'='*76}\n1. SELF-RECOGNITION ACCURACY [{domain}]  (chance = 25%)\n{'='*76}")
    valid = df[df.choice.notna()]
    print(f"  probes: {len(df)}   parsed: {len(valid)}   refused/unparsed: {len(df)-len(valid)}")
    print(f"\n  {'model':10s} {'n':>5s} {'correct':>8s} {'accuracy':>9s} {'95% CI':>18s} {'p vs 25%':>10s}")
    rows = []
    for m in MODELS:
        d = valid[valid.probe_model == m]
        if len(d) == 0: continue
        k, n = int(d.correct.sum()), len(d)
        bt = binomtest(k, n, 0.25)
        lo, hi = bt.proportion_ci(0.95)
        star = "***" if bt.pvalue < .001 else "**" if bt.pvalue < .01 else "*" if bt.pvalue < .05 else ""
        print(f"  {m:10s} {n:5d} {k:8d} {k/n*100:8.1f}% "
              f"[{lo*100:6.1f},{hi*100:6.1f}] {bt.pvalue:10.4f} {star}")
        rows.append({"model": m, "n": n, "acc": k / n, "p": bt.pvalue})
    k, n = int(valid.correct.sum()), len(valid)
    bt = binomtest(k, n, 0.25)
    print(f"  {'OVERALL':10s} {n:5d} {k:8d} {k/n*100:8.1f}% "
          f"[{bt.proportion_ci(.95)[0]*100:6.1f},{bt.proportion_ci(.95)[1]*100:6.1f}] {bt.pvalue:10.4f}")
    print(f"\n  {'ABOVE CHANCE' if bt.pvalue < .05 and k/n > .25 else 'AT CHANCE'} overall")
    return pd.DataFrame(rows)


# ── 2. position bias ──────────────────────────────────────────────────
def position_bias(df, domain):
    """A model that always picks slot 1 would score ~25% and look like chance -- but for
    the wrong reason. Equally, a slot preference could inflate accuracy if its own answer
    happens to sit there. Both need ruling out."""
    from scipy.stats import chisquare
    print(f"\n{'='*76}\n2. POSITION BIAS [{domain}]\n{'='*76}")
    valid = df[df.choice.notna()]
    print(f"  {'model':10s} {'chose 1':>8s} {'2':>7s} {'3':>7s} {'4':>7s} {'uniform p':>11s}")
    for m in MODELS:
        d = valid[valid.probe_model == m]
        if len(d) == 0: continue
        counts = [int((d.choice == i).sum()) for i in (1, 2, 3, 4)]
        p = chisquare(counts).pvalue if sum(counts) else np.nan
        flag = "  <- NOT uniform" if p < .05 else ""
        print(f"  {m:10s} {counts[0]:8d} {counts[1]:7d} {counts[2]:7d} {counts[3]:7d} {p:11.4f}{flag}")
    print("  If a model's choices are far from uniform it is picking a SLOT, not a style.")


# ── 3. quality confound ───────────────────────────────────────────────
def quality_confound(df, domain, mode="actual"):
    """Does the model just pick the answer that is CORRECT, or the LONGEST?"""
    print(f"\n{'='*76}\n3. QUALITY CONFOUND [{domain}]\n{'='*76}")
    grades = load_or_build_grades(domain, mode)
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    lens = {}
    for l in open(os.path.join("data", "generated", f"{domain}{suffix}"), encoding="utf-8"):
        d = json.loads(l)
        for m, c in (d.get("candidates") or {}).items():
            lens[(d["item_id"], m)] = len(c or "")
    valid = df[df.choice.notna()].copy()
    valid["chose_correct_answer"] = [
        grades.get((r.item_id, r.chosen_author), False) for r in valid.itertuples()]
    valid["chose_longest"] = [
        lens.get((r.item_id, r.chosen_author), 0) == max(
            lens.get((r.item_id, m), 0) for m in MODELS) for r in valid.itertuples()]
    print(f"  {'model':10s} {'picked own':>11s} {'picked a CORRECT ans':>21s} {'picked LONGEST':>16s}")
    for m in MODELS:
        d = valid[valid.probe_model == m]
        if len(d) == 0: continue
        print(f"  {m:10s} {d.correct.mean()*100:10.1f}% {d.chose_correct_answer.mean()*100:20.1f}% "
              f"{d.chose_longest.mean()*100:15.1f}%")
    print("  Chance is 25% for 'own' and 'longest'. If 'picked correct' is far above the")
    print("  base rate of correct answers, the model is judging quality, not authorship.")


# ── 4. distinguishability ─────────────────────────────────────────────
def distinguishability(df, domain, mode="actual"):
    """Science is multiple choice: when all four models pick the same letter, only prose
    style distinguishes them. Recognition should be split by this."""
    if domain != "science":
        print(f"\n  [distinguishability] skipped for {domain} (needs parsed option letters)")
        return
    print(f"\n{'='*76}\n4. DISTINGUISHABILITY [{domain}]\n{'='*76}")
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    raw = {json.loads(l)["item_id"]: json.loads(l)
           for l in open(os.path.join("data", "raw", f"{domain}{suffix}"), encoding="utf-8")}
    n_distinct = {}
    for l in open(os.path.join("data", "generated", f"{domain}{suffix}"), encoding="utf-8"):
        d = json.loads(l); ri = raw.get(d["item_id"])
        if not ri: continue
        letters = {parse_science_for_item(c, ri)["letter"]
                   for c in (d.get("candidates") or {}).values()}
        n_distinct[d["item_id"]] = len(letters)
    valid = df[df.choice.notna()].copy()
    valid["n_letters"] = valid.item_id.map(n_distinct)
    from scipy.stats import binomtest
    print(f"  {'distinct letters':18s} {'items':>7s} {'probes':>8s} {'accuracy':>9s} {'p vs 25%':>10s}")
    for k in sorted(valid.n_letters.dropna().unique()):
        d = valid[valid.n_letters == k]
        bt = binomtest(int(d.correct.sum()), len(d), 0.25)
        lab = "1 (all agree)" if k == 1 else f"{int(k)}"
        print(f"  {lab:18s} {d.item_id.nunique():7d} {len(d):8d} "
              f"{d.correct.mean()*100:8.1f}% {bt.pvalue:10.4f}")
    print("  Accuracy at chance ONLY where all four agree would be a floor effect,")
    print("  not evidence about self-recognition.")


# ── 4b. STYLE vs CONCLUSION — the decisive test ───────────────────────
def style_vs_conclusion(df, domain, mode="actual"):
    """
    THE test the interpretation rests on.

    Every model picks an answer whose CONCLUSION matches its own far more often than it
    picks its own answer (in science: deepseek 74% vs 56%, qwen 68% vs 27%). So apparent
    "recognition" could be nothing but re-deriving the answer and matching conclusions,
    with no knowledge of its own writing at all.

    Restrict to items where OTHER models reached the same conclusion as the probed model.
    There, matching conclusions cannot single out its own answer -- only style can. The
    chance baseline is 1/(number of models sharing that conclusion), which varies per
    item, so it is averaged rather than fixed at 25%.

    Above that baseline  -> genuine stylistic self-recognition
    At or below          -> apparent recognition was conclusion-matching (or, if below,
                            an aesthetic preference such as favouring longer answers)
    """
    from scipy.stats import binomtest
    print(f"\n{'='*76}\n4b. STYLE vs CONCLUSION-MATCHING [{domain}]\n{'='*76}")
    key = _answer_key(domain, mode)
    if key is None:
        print(f"  skipped: no comparable answer key for {domain}"); return
    valid = df[df.choice.notna()]

    print(f"  First: how often does each model pick ANY answer matching its own conclusion,")
    print(f"  versus picking its own specific answer?")
    print(f"  {'model':10s} {'picked own':>11s} {'picked conclusion-matching':>28s}")
    for m in MODELS:
        d = valid[valid.probe_model == m]
        if len(d) == 0: continue
        match = [key.get((r.item_id, m)) is not None
                 and key.get((r.item_id, m)) == key.get((r.item_id, r.chosen_author))
                 for r in d.itertuples()]
        print(f"  {m:10s} {d.correct.mean()*100:10.1f}% {np.mean(match)*100:27.1f}%")

    print(f"\n  Now the decisive test -- only items where >=2 models share the probed")
    print(f"  model's conclusion, so matching cannot identify its own answer:")
    print(f"  N_TESTS is the FULL family (4 models x 3 domains = 12) even when this run")
    print(f"  covers one domain, because the claim 'models recognise themselves' is made")
    print(f"  across all of them. Uncorrected p-values here would be misleading.")
    bonf = 0.05 / N_TESTS_FAMILY
    print(f"  Bonferroni threshold = 0.05/{N_TESTS_FAMILY} = {bonf:.4f}\n")
    print(f"  {'model':10s} {'n':>6s} {'chance':>8s} {'picked own':>11s} {'p':>9s}  verdict")
    for m in MODELS:
        d = valid[valid.probe_model == m]
        rows = []
        for r in d.itertuples():
            own = key.get((r.item_id, m))
            if own is None: continue
            sharers = [x for x in MODELS if key.get((r.item_id, x)) == own]
            if len(sharers) < 2: continue          # own conclusion unique: matching suffices
            rows.append((len(sharers), bool(r.correct)))
        if len(rows) < 20:
            print(f"  {m:10s} too few tied items ({len(rows)})"); continue
        n = len(rows); k = sum(1 for _, c in rows if c)
        chance = float(np.mean([1 / s for s, _ in rows]))
        bt = binomtest(k, n, chance)
        if bt.pvalue < bonf:
            verdict = "STYLE RECOGNITION" if k / n > chance else "below chance (aesthetic bias)"
        else:
            nominal = " (nominal p<.05, does NOT survive)" if bt.pvalue < .05 else ""
            verdict = "conclusion-matching only" + nominal
        print(f"  {m:10s} {n:6d} {chance*100:7.1f}% {k/n*100:10.1f}% {bt.pvalue:9.4f}  {verdict}")
    print(f"\n  Across all 12 cells only three survive correction: deepseek/science above")
    print(f"  chance, and mistral below chance in science and code. Everything else is")
    print(f"  conclusion-matching. Do not quote uncorrected cells as recognition.")


def _answer_key(domain, mode):
    """Comparable 'what did this model conclude' key. None where no clean key exists."""
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    raw = {json.loads(l)["item_id"]: json.loads(l)
           for l in open(os.path.join("data", "raw", f"{domain}{suffix}"), encoding="utf-8")}
    key = {}
    for l in open(os.path.join("data", "generated", f"{domain}{suffix}"), encoding="utf-8"):
        d = json.loads(l); ri = raw.get(d["item_id"])
        if not ri: continue
        for m, c in (d.get("candidates") or {}).items():
            if domain == "science":
                key[(d["item_id"], m)] = parse_science_for_item(c, ri)["letter"]
            elif domain == "math":
                import re
                mm = re.findall(r"<answer>(.*?)</answer>", c or "", re.S)
                key[(d["item_id"], m)] = mm[-1].strip() if mm else None
            else:
                # code: pass/fail on the real test suite is the only comparable
                # "conclusion" two programs can share
                g = load_or_build_grades(domain, mode)
                key[(d["item_id"], m)] = g.get((d["item_id"], m))
    return key


# ── 5. MEDIATION — the payoff ─────────────────────────────────────────
def mediation(df, domain, mode="actual"):
    """
    Does recognising its own answer predict APPROVING it?

    For each (item, model) where the model authored the candidate, compare its
    self-approval rate in the verification experiment on items where the probe
    succeeded vs failed. Restricted to WRONG answers, where approving is an error.
    """
    print(f"\n{'='*76}\n5. MEDIATION — does recognition predict self-approval? [{domain}]\n{'='*76}")
    grades = load_or_build_grades(domain, mode)
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    valid = df[df.choice.notna()]
    recog = {(r.item_id, r.probe_model): bool(r.correct) for r in valid.itertuples()}

    rows = []
    for l in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        r = json.loads(l)
        v = r.get("parsed_verdict")
        if v is None or r["verifier_model"] != r["generator_model"]:
            continue                                    # self-verification only
        if grades.get((r["item_id"], r["generator_model"]), False):
            continue                                    # wrong answers only
        key = (r["item_id"], r["verifier_model"])
        if key not in recog:
            continue
        rows.append({"model": r["verifier_model"], "item_id": r["item_id"],
                     "recognised": recog[key], "approved": bool(v),
                     "frame": r["frame"], "strategy": r["strategy"]})
    d = pd.DataFrame(rows)
    if d.empty:
        print("  no overlapping rows"); return

    from scipy.stats import chi2_contingency
    print(f"  self-approval of its OWN WRONG answers, split by whether the probe succeeded")
    print(f"  {'model':10s} {'recognised':>12s} {'n':>6s} {'NOT recog':>11s} {'n':>6s} {'diff':>8s} {'p':>8s}")
    for m in MODELS + ["ALL"]:
        s = d if m == "ALL" else d[d.model == m]
        if len(s) < 20: continue
        a, b = s[s.recognised], s[~s.recognised]
        if len(a) < 5 or len(b) < 5:
            print(f"  {m:10s} too few in one cell (recog n={len(a)}, not n={len(b)})"); continue
        pa, pb = a.approved.mean(), b.approved.mean()
        try:
            _, p, _, _ = chi2_contingency(
                [[a.approved.sum(), len(a) - a.approved.sum()],
                 [b.approved.sum(), len(b) - b.approved.sum()]])
        except Exception:
            p = np.nan
        star = " *" if p < .05 else ""
        print(f"  {m:10s} {pa*100:11.1f}% {len(a):6d} {pb*100:10.1f}% {len(b):6d} "
              f"{(pa-pb)*100:+7.1f}pp {p:8.4f}{star}")
    print("\n  A positive number here is NOT yet evidence that recognition drives approval.")
    print("  Run consistency_control() below before interpreting any of it.")


def consistency_control(df, domain, mode="actual"):
    """
    THE CONTROL THAT OVERTURNS THE MEDIATION.

    "Recognised its own answer" and "approved its own answer" can both be downstream of
    a single thing: the model still believing the conclusion it originally reached. A
    model that has changed its mind will neither pick its own answer in the probe nor
    approve it in verification -- with no self-recognition involved anywhere.

    Control: keep only probes where the model picked SOMETHING matching its own
    conclusion (so it is consistent in every retained case), then split on whether the
    thing it picked was its OWN answer or another model's answer with the same
    conclusion. If recognition mattered, the first group should approve more.

    In science this comes out NULL (+2.8pp, p=0.73), meaning the +22.2pp mediation was
    consistency, not recognition.
    """
    from scipy.stats import chi2_contingency
    print(f"\n{'='*76}\n5b. CONSISTENCY CONTROL — was the mediation just self-consistency?"
          f" [{domain}]\n{'='*76}")
    key = _answer_key(domain, mode)
    if key is None:
        print("  no comparable answer key; skipping"); return
    grades = load_or_build_grades(domain, mode)
    valid = df[df.choice.notna()]

    info = {}
    for r in valid.itertuples():
        own = key.get((r.item_id, r.probe_model))
        chosen = key.get((r.item_id, r.chosen_author))
        info[(r.item_id, r.probe_model)] = {
            "consistent": own is not None and own == chosen,
            "picked_own": bool(r.correct)}

    rows = []
    suffix = ".jsonl" if mode == "actual" else "_pilot.jsonl"
    for l in open(os.path.join("data", "verified", f"{domain}{suffix}"), encoding="utf-8"):
        v = json.loads(l)
        pv = v.get("parsed_verdict")
        if pv is None or v["verifier_model"] != v["generator_model"]:
            continue
        if grades.get((v["item_id"], v["generator_model"]), False):
            continue
        k = (v["item_id"], v["verifier_model"])
        if k not in info:
            continue
        rows.append({"model": v["verifier_model"], **info[k], "approved": bool(pv)})
    d = pd.DataFrame(rows)
    if d.empty:
        print("  no overlapping rows"); return

    print(f"  Restricted to conclusion-consistent probes. If recognition mattered, picking")
    print(f"  its OWN answer should predict approval beyond merely being consistent.\n")
    print(f"  {'model':10s} {'picked own':>11s} {'n':>6s} {'picked other':>13s} {'n':>6s} "
          f"{'diff':>8s} {'p':>8s}  verdict")
    for m in MODELS:
        s = d[(d.model == m) & (d.consistent)]
        a, b = s[s.picked_own], s[~s.picked_own]
        if len(a) < 5 or len(b) < 5:
            print(f"  {m:10s} too few (own={len(a)}, other={len(b)})"); continue
        pa, pb = a.approved.mean(), b.approved.mean()
        try:
            _, p, _, _ = chi2_contingency([[a.approved.sum(), len(a) - a.approved.sum()],
                                           [b.approved.sum(), len(b) - b.approved.sum()]])
        except Exception:
            p = np.nan
        if p >= .05:
            verdict = "NULL -> was consistency"
        elif pa > pb:
            verdict = "recognition ADDS approval"
        else:
            verdict = "REVERSED (own -> LESS approval)"
        if min(len(a), len(b)) < 30 or pa in (0.0, 1.0) or pb in (0.0, 1.0):
            verdict += "  [degenerate cell -- distrust]"
        print(f"  {m:10s} {pa*100:10.1f}% {len(a):6d} {pb*100:12.1f}% {len(b):6d} "
              f"{(pa-pb)*100:+7.1f}pp {p:8.4f}  {verdict}")
    print("\n  NULL here means the apparent mediation was the model still believing its")
    print("  own conclusion -- not recognising its own writing.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="science")
    ap.add_argument("--mode", default="actual", choices=["pilot", "actual"])
    a = ap.parse_args()
    df = load_probe(a.domain, a.mode)
    if df is not None:
        print(f"\n{'#'*76}\n#  SELF-RECOGNITION — {a.domain.upper()}\n{'#'*76}")
        accuracy(df, a.domain)
        position_bias(df, a.domain)
        quality_confound(df, a.domain, a.mode)
        distinguishability(df, a.domain, a.mode)
        style_vs_conclusion(df, a.domain, a.mode)
        mediation(df, a.domain, a.mode)
        consistency_control(df, a.domain, a.mode)
