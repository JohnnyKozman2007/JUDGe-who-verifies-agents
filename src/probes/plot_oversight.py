"""
Figures for: does verification ability follow from generation ability?

Four panels, matching the analysis in analysis_oversight.py:
  1. 4x4 oversight heatmap per domain (diagonal = self-verification, greyed out)
  2. Sign-test scatter over model pairs -- the honest NULL: points fall on both
     sides of the diagonal (10/18), so the "oversight flows downward" claim fails
  3. Difficulty stratification -- catch rate vs how many generators solved the item
  4. Metric validity -- catch rate vs balanced accuracy in code, where the weakest
     judge ranks 1st on one and last on the other

Reads committed data + the grade cache. Writes PNGs only.
"""
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_oversight import build_oversight_frame, full_confusion_by_verifier
from analysis_detectability import load_or_build_grades

DOMAINS = ["science", "math", "code"]
COL = {"science": "#C44E52", "math": "#4C72B0", "code": "#55A868"}
OUT = os.path.join("reports", "probes", "Do-stronger-models-make-mistakes-that-are-harder-to-catch", "oversight")
os.makedirs(OUT, exist_ok=True)
MODE = "actual"

frames = {d: build_oversight_frame(d, MODE) for d in DOMAINS}


# ── 1. oversight heatmaps ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
cmap = LinearSegmentedColormap.from_list("wr", ["#FFF5EB", "#D94801"])
for ax, dom in zip(axes, DOMAINS):
    df = frames[dom]; acc = df.attrs["acc"]
    order = sorted(acc, key=lambda m: -acc[m])
    M = np.full((len(order), len(order)), np.nan)
    for i, v in enumerate(order):
        for j, g in enumerate(order):
            if v == g: continue
            cell = df[(df.verifier == v) & (df.generator == g)]
            if len(cell): M[i, j] = cell.rejected.mean() * 100
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=100)
    for i in range(len(order)):
        for j in range(len(order)):
            if i == j:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="#DDDDDD"))
                ax.text(j, i, "self", ha="center", va="center", fontsize=8, color="#777")
            else:
                ax.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=9,
                        color="white" if M[i, j] > 55 else "black")
    lab = [f"{m}\n{acc[m]*100:.0f}%" for m in order]
    ax.set_xticks(range(len(order))); ax.set_xticklabels(lab, fontsize=8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(lab, fontsize=8)
    ax.set_xlabel("generator (whose error)"); ax.set_ylabel("verifier (the judge)")
    ax.set_title(f"{dom}  —  error-catch rate (%)")
fig.colorbar(im, ax=axes, fraction=.02, pad=.02, label="catch rate (%)")
plt.savefig(os.path.join(OUT, "1_oversight_matrix.png"), dpi=200, bbox_inches="tight")
plt.close()
print("saved 1_oversight_matrix.png")


# ── 2. sign-test scatter: the honest null ─────────────────────────────
plt.figure(figsize=(6.2, 6))
wins = tot = 0
for dom in DOMAINS:
    df = frames[dom]; acc = df.attrs["acc"]
    models = sorted(acc, key=lambda m: -acc[m])
    xs, ys = [], []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            s, w = models[i], models[j]
            sw = df[(df.verifier == s) & (df.generator == w)].rejected.mean()
            ws = df[(df.verifier == w) & (df.generator == s)].rejected.mean()
            if np.isnan(sw) or np.isnan(ws): continue
            xs.append(ws * 100); ys.append(sw * 100)
            tot += 1; wins += (sw > ws)
    plt.scatter(xs, ys, s=80, alpha=.85, color=COL[dom], label=dom, edgecolor="k", linewidth=.5)
lim = [0, 100]
plt.plot(lim, lim, "k--", lw=1)
plt.fill_between(lim, lim, [100, 100], alpha=.06, color="green")
plt.text(8, 92, "above line =\nstronger judge better\n(hypothesis)", fontsize=8, va="top")
plt.text(55, 12, "below line =\nhypothesis fails", fontsize=8)
plt.xlim(lim); plt.ylim(lim)
plt.xlabel("weaker model judging stronger model's errors (% caught)")
plt.ylabel("stronger model judging weaker model's errors (% caught)")
plt.title(f"Oversight is NOT reliably downward\n{wins}/{tot} pairs support the hypothesis (chance = 50%)")
plt.legend(); plt.grid(alpha=.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "2_sign_test_scatter.png"), dpi=200)
plt.close()
print(f"saved 2_sign_test_scatter.png  ({wins}/{tot} pairs)")


# ── 3. difficulty stratification ──────────────────────────────────────
plt.figure(figsize=(6.6, 4.4))
for dom in DOMAINS:
    df = frames[dom].copy()
    grades = load_or_build_grades(dom, MODE)
    solved = {}
    for (item, m), ok in grades.items():
        solved[item] = solved.get(item, 0) + ok
    df["n_solvers"] = df.item_id.map(solved)
    g = df.groupby("n_solvers").rejected.mean().reset_index()
    plt.plot(g.n_solvers, g.rejected * 100, "o-", color=COL[dom], lw=2, ms=7, label=dom)
plt.xlabel("generators that solved the item (0 = nobody could)")
plt.ylabel("error-catch rate (%)")
plt.title("Verification tracks the competence frontier\n(ungrounded domains only; code is flat)")
plt.xticks([0, 1, 2, 3, 4]); plt.legend(); plt.grid(alpha=.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "3_difficulty_stratification.png"), dpi=200)
plt.close()
print("saved 3_difficulty_stratification.png")


# ── 4. metric validity: the ranking flip ──────────────────────────────
import contextlib, io
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
for ax, dom in zip(axes, DOMAINS):
    with contextlib.redirect_stdout(io.StringIO()):        # suppress its printout
        d = full_confusion_by_verifier(dom, MODE)
    d = d.sort_values("catch_rate", ascending=False).reset_index(drop=True)
    x = np.arange(len(d)); w = .38
    ax.bar(x - w/2, d.catch_rate * 100, w, label="catch rate (gameable)", color="#D62728", alpha=.85)
    ax.bar(x + w/2, d.balanced_acc * 100, w, label="balanced accuracy", color="#2C7FB8", alpha=.85)
    ax.set_xticks(x); ax.set_xticklabels(d.verifier, fontsize=9)
    ax.set_title(f"{dom}"); ax.grid(alpha=.3, axis="y")
    flip = list(d.verifier) != list(d.sort_values("balanced_acc", ascending=False).verifier)
    if flip:
        ax.text(.5, .04, "RANKINGS DISAGREE", transform=ax.transAxes, ha="center",
                fontsize=9, weight="bold", color="#B22222")
axes[0].set_ylabel("%"); axes[0].legend(fontsize=8, loc="lower left")
plt.suptitle("Error-catch rate is not a valid judge metric: it rewards indiscriminate rejection", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "4_metric_validity.png"), dpi=200, bbox_inches="tight")
plt.close()
print("saved 4_metric_validity.png")
print(f"\nall figures -> {OUT}/")
