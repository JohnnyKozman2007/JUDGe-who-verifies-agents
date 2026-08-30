"""
Figures for: can ensembling repair an unreliable judge?

  1. k-of-3 sweep (deployment-realistic pool) vs the best single judge, per domain
  2. Pairwise judge agreement (Cohen's kappa) heatmaps -- the mechanism
  3. kappa vs cross-validated ensemble gain, 9 points (3 domains x 3 strategies).
     This replaces a within-domain diversity/gain test, which was confounded:
     low-kappa subsets were simply the ones containing the weakest judge, so
     "diversity" and "has a bad member" were inseparable. Varying grounding across
     domains while holding the judge pool fixed isolates correlation cleanly.
  4. Observed vs independence-null unanimous approval of wrong answers

Reads committed data + grade cache. Writes PNGs only.
"""
import os, sys, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_ensemble import build_vote_frame, evaluate, MODELS, VCOLS

DOMAINS = ["science", "math", "code"]
STRATS = ["direct", "cot", "rubric"]
COL = {"science": "#C44E52", "math": "#4C72B0", "code": "#55A868"}
MARK = {"direct": "o", "cot": "s", "rubric": "^"}
OUT = os.path.join("reports", "probes", "Do-stronger-models-make-mistakes-that-are-harder-to-catch", "ensemble")
os.makedirs(OUT, exist_ok=True)
MODE = "actual"

frames = {d: build_vote_frame(d, MODE, "neutral") for d in DOMAINS}


# ── 1. k-of-3 sweep vs best single ────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
for ax, dom in zip(axes, DOMAINS):
    df = frames[dom]
    for strat in STRATS:
        d = df[(df.strategy == strat) & (df.n_loo_valid == 3)]
        if len(d) < 50: continue
        ys = [evaluate(d.truth.values, (d.n_loo >= k).values)["bal_acc"] * 100 for k in (1, 2, 3)]
        ax.plot([1, 2, 3], ys, MARK[strat] + "-", label=f"{strat}", lw=1.8, ms=6,
                color=COL[dom], alpha=.55 + .2 * STRATS.index(strat))
        best_single = max(
            evaluate(d[(d.generator != m)].truth.values,
                     d[(d.generator != m)][f"v_{m}"].values)["bal_acc"]
            for m in MODELS if len(d[d.generator != m]) > 30) * 100
        ax.axhline(best_single, ls=":", lw=1, color=COL[dom], alpha=.5)
    ax.set_xticks([1, 2, 3]); ax.set_xlabel("k  (approve if >= k of 3 judges approve)")
    ax.set_title(dom); ax.grid(alpha=.3); ax.legend(fontsize=8)
axes[0].set_ylabel("balanced accuracy (%)")
plt.suptitle("Ensemble rules vs best single judge (dotted = best single)", y=1.02)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "1_k_of_n_sweep.png"), dpi=200, bbox_inches="tight")
plt.close(); print("saved 1_k_of_n_sweep.png")


# ── 2. kappa heatmaps ─────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
for ax, dom in zip(axes, DOMAINS):
    d = frames[dom]
    d = d[(d.strategy == "cot") & (~d.truth)].dropna(subset=VCOLS)
    K = np.ones((4, 4))
    for i, a in enumerate(MODELS):
        for j, b in enumerate(MODELS):
            if i != j:
                K[i, j] = cohen_kappa_score(d[f"v_{a}"].astype(int), d[f"v_{b}"].astype(int))
    im = ax.imshow(K, cmap="RdYlBu_r", vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{K[i,j]:.2f}", ha="center", va="center", fontsize=9,
                    color="white" if K[i, j] > .6 else "black")
    ax.set_xticks(range(4)); ax.set_xticklabels(MODELS, rotation=45, fontsize=8)
    ax.set_yticks(range(4)); ax.set_yticklabels(MODELS, fontsize=8)
    mk = np.mean([K[i, j] for i in range(4) for j in range(4) if i != j])
    ax.set_title(f"{dom}   mean $\\kappa$ = {mk:+.2f}")
fig.colorbar(im, ax=axes, fraction=.02, pad=.02, label="Cohen's $\\kappa$")
plt.suptitle("Judges agree far beyond chance -- except under execution grounding (code)", y=1.03)
plt.savefig(os.path.join(OUT, "2_kappa_heatmap.png"), dpi=200, bbox_inches="tight")
plt.close(); print("saved 2_kappa_heatmap.png")


# ── 3. kappa vs cross-validated ensemble gain (the mechanism) ─────────
def cv_gain(df, strategy, n_splits=200, seed=0):
    """
    Returns (mean kappa, mean gain, ci_low, ci_high). PAIRED per split -- the gain is
    computed within each split before averaging, so the CI reflects split-to-split
    variability in the difference rather than the spread of two independent means.
    """
    d = df[df.strategy == strategy].dropna(subset=VCOLS)
    if len(d) < 100: return None, None, None, None
    items = d.item_id.unique(); rng = np.random.default_rng(seed)
    gains = []
    for _ in range(n_splits):
        perm = rng.permutation(items)
        tr = d[d.item_id.isin(set(perm[:len(perm)//2]))]
        te = d[d.item_id.isin(set(perm[len(perm)//2:]))]
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
        e = evaluate(te.truth.values, (te[cols].sum(axis=1) >= k).values)["bal_acc"]
        gains.append((e - s) * 100)
    g = np.array(gains)
    lo, hi = np.percentile(g, [2.5, 97.5])
    wrong = d[~d.truth]
    ks = [cohen_kappa_score(wrong[f"v_{a}"].astype(int), wrong[f"v_{b}"].astype(int))
          for a, b in itertools.combinations(MODELS, 2)]
    return float(np.mean(ks)), float(g.mean()), float(lo), float(hi)

plt.figure(figsize=(7.2, 5.4))
pts = []
for dom in DOMAINS:
    for strat in STRATS:
        k, g, lo, hi = cv_gain(frames[dom], strat)
        if k is None: continue
        pts.append((k, g))
        # 95% CI over item splits; excluding zero is the whole claim
        plt.errorbar(k, g, yerr=[[g - lo], [hi - g]], fmt="none",
                     ecolor=COL[dom], elinewidth=1.6, capsize=4, alpha=.75, zorder=1)
        plt.scatter(k, g, s=120, color=COL[dom], marker=MARK[strat],
                    edgecolor="k", linewidth=.6, zorder=2,
                    label=f"{dom} / {strat}")
plt.axhline(0, color="k", lw=1, ls="--")
if len(pts) > 3:
    from scipy.stats import pearsonr
    xs, ys = zip(*pts)
    r, p = pearsonr(xs, ys)
    z = np.polyfit(xs, ys, 1)
    xx = np.linspace(min(xs), max(xs), 50)
    plt.plot(xx, np.polyval(z, xx), "k-", alpha=.4, lw=1.5)
    plt.title(f"Ensembling helps only when judges fail independently\n"
              f"r = {r:+.2f}, p = {p:.3f}  (n={len(pts)} domain x strategy cells)"
              f"\nbars = 95% CI over item splits; above zero = reliable gain")
plt.xlabel("mean pairwise Cohen's $\\kappa$ among judges (error correlation)")
plt.ylabel("cross-validated ensemble gain over best single (pp)")
plt.legend(fontsize=7, ncol=2, loc="upper right"); plt.grid(alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "3_kappa_vs_gain.png"), dpi=200)
plt.close(); print("saved 3_kappa_vs_gain.png")


# ── 4. observed vs independence-null unanimity ────────────────────────
plt.figure(figsize=(7, 4.4))
x = np.arange(len(DOMAINS)); w = .36
obs_v, null_v = [], []
rng = np.random.default_rng(0)
for dom in DOMAINS:
    d = frames[dom]
    d = d[(d.strategy == "cot") & (~d.truth)].dropna(subset=VCOLS)
    obs_v.append((d[VCOLS].sum(axis=1) == 4).mean() * 100)
    arrs = [d[c].values.astype(bool) for c in VCOLS]
    null_v.append(np.mean([(np.column_stack([rng.permutation(a) for a in arrs]).sum(axis=1) == 4).mean()
                           for _ in range(500)]) * 100)
plt.bar(x - w/2, obs_v, w, label="observed", color="#D62728")
plt.bar(x + w/2, null_v, w, label="if errors were independent", color="#7F7F7F", alpha=.8)
for i, (o, n) in enumerate(zip(obs_v, null_v)):
    if n > .05:
        plt.text(i, max(o, n) + 1.5, f"{o/n:.1f}x", ha="center", fontsize=10, weight="bold")
plt.xticks(x, DOMAINS); plt.ylabel("wrong answers approved by ALL FOUR judges (%)")
plt.title("Judges fail together, not independently\n(except under execution grounding)")
plt.legend(); plt.grid(alpha=.3, axis="y")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "4_correlated_failure.png"), dpi=200)
plt.close(); print("saved 4_correlated_failure.png")
print(f"\nall figures -> {OUT}/")
