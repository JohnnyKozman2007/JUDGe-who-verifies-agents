import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_detectability import build_frame

DOMAINS, COL = ["science", "math", "code"], {"science": "#C44E52", "math": "#4C72B0", "code": "#55A868"}
P = {"science": "<0.001", "math": "<0.001", "code": "=0.064"}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

for dom in DOMAINS:
    df = build_frame(dom, "actual")
    per = df.groupby(["item_id", "generator"]).agg(
        appr=("rejected", lambda s: 1 - s.mean()), gen_acc=("gen_acc", "first")).reset_index()
    per = per[per.groupby("item_id")["generator"].transform("size") >= 2].copy()
    per["adj"] = per.appr - per.groupby("item_id").appr.transform("mean")
    g = per.groupby("gen_acc")["adj"].mean().reset_index().sort_values("gen_acc")
    ax1.plot(g.gen_acc * 100, g.adj * 100, "o-", color=COL[dom], lw=2, ms=7,
             label=f"{dom} (p{P[dom]})")
    # panel 2: fully-undetectable rate
    full = per.groupby("gen_acc").appr.apply(lambda s: (s >= 1.0).mean()).reset_index()
    ax2.plot(full.gen_acc * 100, full.appr * 100, "s--", color=COL[dom], lw=2, ms=7, label=dom)

ax1.axhline(0, color="k", lw=.8, ls=":")
ax1.set_xlabel("generator accuracy (%)"); ax1.set_ylabel("item-adjusted approval of its errors (pp)")
ax1.set_title("Stronger generators' errors are approved more"); ax1.legend(); ax1.grid(alpha=.3)
ax2.set_xlabel("generator accuracy (%)"); ax2.set_ylabel("errors undetected by ALL judges (%)")
ax2.set_title("Execution grounding eliminates undetectable errors"); ax2.legend(); ax2.grid(alpha=.3)
plt.tight_layout()
os.makedirs("plots/actual/detectability", exist_ok=True)
plt.savefig("plots/actual/detectability/detectability.png", dpi=200)
print("saved -> plots/actual/detectability/detectability.png")