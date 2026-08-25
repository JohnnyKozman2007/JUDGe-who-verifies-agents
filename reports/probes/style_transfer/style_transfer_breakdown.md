# Causal Style Transfer Metrics (Stylistic Fingerprinting Probe)

## VERIFIER: DEEPSEEK
- **Total Baseline False Positives Tested:** 928
- **Original FPR:** 100.0%
- **Control FPR (Placebo Rewrite):** 85.5% (793/928)
- **Mistral Style FPR (Style Stripped):** 85.2% (791/928)
- **Net FPR Drop (Effect of Style):** -0.2%

> **Conclusion:** Changing the prose and formatting style had statistically zero impact on DEEPSEEK's self-bias. The 'Stylistic Fingerprinting' hypothesis is dead.

## VERIFIER: QWEN
- **Total Baseline False Positives Tested:** 1088
- **Original FPR:** 100.0%
- **Control FPR (Placebo Rewrite):** 91.8% (999/1088)
- **Mistral Style FPR (Style Stripped):** 90.3% (983/1088)
- **Net FPR Drop (Effect of Style):** -1.5%

> **Conclusion:** Changing the prose and formatting style had statistically zero impact on QWEN's self-bias. The 'Stylistic Fingerprinting' hypothesis is dead.

