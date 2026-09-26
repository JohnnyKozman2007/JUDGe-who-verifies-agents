# JUDGe Oversight Matrix: Cross-Capability Error Detection

This artifact provides the pairwise cross-capability oversight win-rate matrix corresponding to **Table 6** (`tab:oversight-full`) in the paper.

## Table 6: Oversight Matrix (Pairwise Error Catch Rate on Identical Candidates)

Proportion of identical error candidates where a more capable verifier correctly rejected an error that a less capable verifier approved.

| Stronger Judge | Weaker Judge | Code Domain | Math Domain | Science Domain |
|---|---|:---:|:---:|:---:|
| **DeepSeek-V3 (671B)** | **Mistral-Nemo (12B)** | 54.2% | 61.8% | 58.4% |
| **DeepSeek-V3 (671B)** | **Llama-3.3-70B** | 48.9% | 52.3% | 51.1% |
| **DeepSeek-V3 (671B)** | **Qwen2.5-72B** | 49.5% | 53.7% | 50.8% |
| **Qwen2.5-72B (72B)** | **Mistral-Nemo (12B)** | 56.1% | 58.2% | 54.6% |
| **Llama-3.3-70B (70B)** | **Mistral-Nemo (12B)** | 53.8% | 55.4% | 53.1% |
| **Qwen2.5-72B (72B)** | **Llama-3.3-70B** | 50.4% | 51.1% | 49.7% |

### Key Findings & Dynamics
1. **Stronger vs. 12B Baseline:** Frontier models (DeepSeek-V3, Qwen-72B, Llama-70B) outperform the 12B baseline (Mistral) across ungrounded domains (53.1%–61.8% win rates).
2. **Diminishing Returns Within Frontier Scale:** When comparing frontier models against each other (e.g., DeepSeek vs. Qwen, DeepSeek vs. Llama, Qwen vs. Llama), oversight win rates collapse to near-chance (48.9%–53.7%).
3. **Absence of Scaling in Code:** In code, the strongest judge (DeepSeek) loses head-to-head against smaller models (48.9% vs Llama, 49.5% vs Qwen) due to hyper-assertive test overruling.

Generated from committed evaluation data via `src/probes/analysis_oversight.py` and `src/probes/plot_oversight.py`.
