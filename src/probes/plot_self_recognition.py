"""
Figures for: can a model recognise its own output?

  1. Accuracy vs the 25% chance floor, per model per domain, with exact binomial CIs
  2. THE DECISIVE TEST -- restricted to items where other models reached the same
     conclusion, so conclusion-matching cannot identify a model's own answer and only
     style can. Chance here is 1/(models sharing the conclusion), not 25%.
  3. Mediation -- does recognising its own answer predict APPROVING it? Only meaningful
     for models that recognise above chance in panel 2.

Skips any domain whose probe has not been run. Writes PNGs only.
"""
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_self_recognition import load_probe, _answer_key, MODELS, N_TESTS_FAMILY

BONF = 0.05 / N_TESTS_FAMILY   # 12 cells (4 models x 3 domains); uncorrected p<.05
                               # would label llama/code as recognition, which it is not
from analysis_detectability import load_or_build_grades

DOMAINS = ["science", "math", "code"]
COL = {"science": "#C44E52", "math": "#4C72B0", "code": "#55A868"}
OUT = os.path.join("reports", "probes", "self_recognition")
os.makedirs(OUT, exist_ok=True)
MODE = "actual"

probes = {}
for d in DOMAINS:
    p = load_probe(d, MODE)
    if p is not None and len(p) > 100:
        probes[d] = p[p.choice.notna()]
if not probes:
    sys.exit("no probe data found")
DOMS = list(probes)
print(f"  domains with data: {DOMS}")


# ── 1. accuracy vs chance ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.5, 4.6))
w = 0.8 / len(DOMS)
x = np.arange(len(MODELS))
for di, dom in enumerate(DOMS):
    accs, los, his = [], [], []
    for m in MODELS:
        d = probes[dom][probes[dom].probe_model == m]
        k, n = int(d.correct.sum()), len(d)
        bt = binomtest(k, n, .25)
        lo, hi = bt.proportion_ci(.95)
        accs.append(k / n * 100); los.append(lo * 100); his.append(hi * 100)
    pos = x + (di - (len(DOMS) - 1) / 2) * w
    ax.bar(pos, accs, w * .9, color=COL[dom], label=dom, alpha=.88)
    ax.errorbar(pos, accs, yerr=[np.array(accs) - los, np.array(his) - accs],
                fmt="none", ecolor="k", elinewidth=1, capsize=3)
ax.axhline(25, color="k", ls="--", lw=1.4)
ax.text(len(MODELS) - .45, 26.5, "chance (25%)", fontsize=9, ha="right")
ax.set_xticks(x); ax.set_xticklabels(MODELS)
ax.set_ylabel("picked its own answer (%)")
ax.set_title("Can a model identify which answer it wrote?")
ax.legend(); ax.grid(alpha=.3, axis="y")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "1_accuracy.png"), dpi=200)
plt.close(); print("saved 1_accuracy.png")


# ── 2. the decisive test ──────────────────────────────────────────────
fig, axes = plt.subplots(1, len(DOMS), figsize=(4.8 * len(DOMS), 4.4), squeeze=False)
for ax, dom in zip(axes[0], DOMS):
    key = _answer_key(dom, MODE)
    obs, chc, sig = [], [], []
    for m in MODELS:
        d = probes[dom][probes[dom].probe_model == m]
        rows = []
        for r in d.itertuples():
            own = key.get((r.item_id, m))
            if own is None: continue
            sh = [xx for xx in MODELS if key.get((r.item_id, xx)) == own]
            if len(sh) < 2: continue
            rows.append((len(sh), bool(r.correct)))
        if len(rows) < 20:
            obs.append(np.nan); chc.append(np.nan); sig.append(False); continue
        n = len(rows); k = sum(1 for _, c in rows if c)
        ch = float(np.mean([1 / s for s, _ in rows]))
        obs.append(k / n * 100); chc.append(ch * 100)
        sig.append(binomtest(k, n, ch).pvalue < BONF)
    xx = np.arange(len(MODELS))
    ax.bar(xx - .2, chc, .38, color="#AAAAAA", label="chance (ties)")
    bars = ax.bar(xx + .2, obs, .38, color=COL[dom], label="observed")
    for i, (o, c, s) in enumerate(zip(obs, chc, sig)):
        if np.isnan(o): continue
        if s and o > c:
            ax.text(i + .2, o + 1.5, "STYLE", ha="center", fontsize=8,
                    weight="bold", color="#B22222")
        elif s and o < c:
            ax.text(i + .2, o + 1.5, "below", ha="center", fontsize=8, color="#555")
    ax.set_xticks(xx); ax.set_xticklabels(MODELS, fontsize=9)
    ax.set_title(dom); ax.grid(alpha=.3, axis="y"); ax.set_ylim(0, 75)
axes[0][0].set_ylabel("picked its own answer (%)")
axes[0][0].legend(fontsize=8)
plt.suptitle("Decisive test: only items where conclusion-matching CANNOT identify its own answer\n"
             f"labels applied at Bonferroni-corrected p < {BONF:.4f} across all 12 cells",
             y=1.04, fontsize=11)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "2_style_vs_conclusion.png"),
                                dpi=200, bbox_inches="tight")
plt.close(); print("saved 2_style_vs_conclusion.png")


# ── 3. mediation ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, len(DOMS), figsize=(4.8 * len(DOMS), 4.4), squeeze=False)
for ax, dom in zip(axes[0], DOMS):
    grades = load_or_build_grades(dom, MODE)
    recog = {(r.item_id, r.probe_model): bool(r.correct) for r in probes[dom].itertuples()}
    rows = []
    for l in open(os.path.join("data", "verified", f"{dom}.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        v = r.get("parsed_verdict")
        if v is None or r["verifier_model"] != r["generator_model"]: continue
        if grades.get((r["item_id"], r["generator_model"]), False): continue
        k = (r["item_id"], r["verifier_model"])
        if k not in recog: continue
        rows.append({"model": r["verifier_model"], "recognised": recog[k], "approved": bool(v)})
    d = pd.DataFrame(rows)
    yes, no = [], []
    for m in MODELS:
        s = d[d.model == m]
        a, b = s[s.recognised], s[~s.recognised]
        yes.append(a.approved.mean() * 100 if len(a) >= 5 else np.nan)
        no.append(b.approved.mean() * 100 if len(b) >= 5 else np.nan)
    xx = np.arange(len(MODELS))
    ax.bar(xx - .2, no, .38, color="#AAAAAA", label="did NOT recognise")
    ax.bar(xx + .2, yes, .38, color=COL[dom], label="recognised own answer")
    for i, (y, n_) in enumerate(zip(yes, no)):
        if not (np.isnan(y) or np.isnan(n_)):
            ax.text(i, max(y, n_) + 2, f"{y-n_:+.0f}pp", ha="center", fontsize=8)
    ax.set_xticks(xx); ax.set_xticklabels(MODELS, fontsize=9)
    ax.set_title(dom); ax.grid(alpha=.3, axis="y")
axes[0][0].set_ylabel("approved its OWN WRONG answer (%)")
axes[0][0].legend(fontsize=8)
plt.suptitle("Does recognising your own answer make you approve it?", y=1.02, fontsize=11)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "3_mediation.png"), dpi=200, bbox_inches="tight")
plt.close(); print("saved 3_mediation.png")
print(f"\nall figures -> {OUT}/")
