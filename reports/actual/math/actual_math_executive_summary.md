# Dynamic Executive Summary

**Total Verifications Processed:** 21600

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/actual/math/actual_math_accuracy_by_domain.png)

- **Math**: deepseek (Frame: neutral, Strategy: rubric) achieved **69.2%** accuracy (**69.2% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Math
- **deepseek**: Prefers **neutral** frame & **rubric** strategy (**69.2%**)
- **llama**: Prefers **self** frame & **cot** strategy (**66.0%**)
- **mistral**: Prefers **other** frame & **rubric** strategy (**59.5%**)
- **qwen**: Prefers **other** frame & **direct** strategy (**67.3%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 68.4% | 67.5% | 68.6% |
| **llama** | 65.6% | 64.7% | 64.7% |
| **mistral** | 58.4% | 57.9% | 58.9% |
| **qwen** | 66.2% | 66.8% | 66.4% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 68.4% | 67.5% | 68.6% |
| **llama** | 65.6% | 64.7% | 64.7% |
| **mistral** | 58.4% | 57.9% | 58.9% |
| **qwen** | 66.2% | 66.8% | 66.4% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 64.5%
### By Domain
- **Math**: 64.5%
### By Strategy
- **cot**: 64.6%
- **direct**: 64.2%
- **rubric**: 64.7%
### By Ownership Frame
- **neutral**: 64.4%
- **other**: 64.6%
- **self**: 64.6%
### By Model
- **deepseek**: 68.1%
- **llama**: 65.0%
- **mistral**: 58.4%
- **qwen**: 66.5%
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 64.8%
- **self + cot**: 64.8%
- **other + rubric**: 64.8%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 64.5%
### By Domain
- **Math**: 64.5%
### By Strategy
- **cot**: 64.6%
- **direct**: 64.2%
- **rubric**: 64.7%
### By Ownership Frame
- **neutral**: 64.4%
- **other**: 64.6%
- **self**: 64.6%
### By Model
- **deepseek**: 68.1%
- **llama**: 65.0%
- **mistral**: 58.4%
- **qwen**: 66.5%
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 64.8%
- **self + cot**: 64.8%
- **other + rubric**: 64.8%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.0%
### By Domain
- **Math**: 0.0%
### By Strategy
- **cot**: 0.0%
- **direct**: 0.0%
- **rubric**: 0.0%
### By Ownership Frame
- **neutral**: 0.0%
- **other**: 0.0%
- **self**: 0.0%
### By Model
- **deepseek**: 0.0%
- **llama**: 0.0%
- **mistral**: 0.0%
- **qwen**: 0.0%
### Top 3 Best Ownership + Strategy Combos
- **neutral + cot**: 0.0%
- **neutral + direct**: 0.0%
- **neutral + rubric**: 0.0%

## 3. Verbosity Analysis (Average Characters)
### Overall Average Across Everything
- **Overall**: 180.0
### By Domain
- **Math**: 180.0
### By Strategy
- **cot**: 285.9
- **direct**: 0.0
- **rubric**: 254.0
### By Ownership Frame
- **neutral**: 180.2
- **other**: 179.8
- **self**: 179.9
### By Model
- **deepseek**: 174.7
- **llama**: 239.6
- **mistral**: 149.5
- **qwen**: 156.1
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 287.0
- **neutral + cot**: 285.8
- **self + cot**: 285.1

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 26.4% | Passed: 73.6% | Introduced: 5.6% | Confirmed: 94.4%
### By Domain
- **math** -> Caught: 26.4% | Passed: 73.6% | Introduced: 5.6% | Confirmed: 94.4%
### By Strategy
- **cot** -> Caught: 26.5% | Passed: 73.5% | Introduced: 5.4% | Confirmed: 94.6%
- **direct** -> Caught: 24.9% | Passed: 75.1% | Introduced: 4.8% | Confirmed: 95.2%
- **rubric** -> Caught: 27.8% | Passed: 72.2% | Introduced: 6.4% | Confirmed: 93.6%
### By Ownership Frame
- **neutral** -> Caught: 25.6% | Passed: 74.4% | Introduced: 5.2% | Confirmed: 94.8%
- **other** -> Caught: 27.1% | Passed: 72.9% | Introduced: 5.9% | Confirmed: 94.1%
- **self** -> Caught: 26.5% | Passed: 73.5% | Introduced: 5.6% | Confirmed: 94.4%
### By Model
- **deepseek** -> Caught: 40.9% | Passed: 59.1% | Introduced: 10.4% | Confirmed: 89.6%
- **llama** -> Caught: 23.9% | Passed: 76.1% | Introduced: 2.7% | Confirmed: 97.3%
- **mistral** -> Caught: 10.0% | Passed: 90.0% | Introduced: 3.6% | Confirmed: 96.4%
- **qwen** -> Caught: 30.9% | Passed: 69.1% | Introduced: 5.5% | Confirmed: 94.5%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/actual/math/actual_math_fpr_self_bias.png)

- **mistral** (math, rubric): **+3.8%** bias
- **mistral** (math, cot): **+2.7%** bias
- **deepseek** (math, rubric): **+2.3%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/actual/math/actual_math_fnr_self_bias.png)

- **deepseek** (math, direct): **+0.9%** bias
- **deepseek** (math, rubric): **+0.9%** bias
- **llama** (math, cot): **+-0.3%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **mistral** (math, rubric): FPR Bias p=0.2592 | FNR Bias p=1.0000
- **mistral** (math, cot): FPR Bias p=0.4001 | FNR Bias p=0.5625
- **deepseek** (math, rubric): FPR Bias p=0.6614 | FNR Bias p=0.8182

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/actual/math/actual_math_adj_fpr_self_bias.png)

- **mistral** (math, rubric): **+3.8%** adjusted bias
- **mistral** (math, cot): **+2.7%** adjusted bias
- **deepseek** (math, rubric): **+2.3%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/actual/math/actual_math_adj_fnr_self_bias.png)

- **deepseek** (math, direct): **+0.9%** adjusted bias
- **deepseek** (math, rubric): **+0.9%** adjusted bias
- **llama** (math, cot): **+-0.3%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **mistral** (math, rubric): Adj FPR Bias p=0.2592 | Adj FNR Bias p=1.0000
- **mistral** (math, cot): Adj FPR Bias p=0.4001 | Adj FNR Bias p=0.5625
- **deepseek** (math, rubric): Adj FPR Bias p=0.6614 | Adj FNR Bias p=0.8182

Full adjusted bias table: `actual_math_adj_bias_metrics.csv`.

## 6c. Oracle & Fuzzing Statistics (Code Domain)
*These rows represent code verifications where the verifier overrode a passing execution result (i.e. test passed but verifier said incorrect). The fuzzer ran differential testing on each and an LLM oracle adjudicated mismatches. This section quantifies how often the verifier was right vs. wrong, and how often the benchmark reference itself was the problem.*

**Total override cases fuzzed:** 1856

### Verdict Breakdown

| Verdict | Count | % of Fuzzed |
|---|---|---|
| `BUG_CONFIRMED` | 167 | 9.0% |
| `REFERENCE_BUG` | 15 | 0.8% |
| `NO_DISCREPANCY` | 1430 | 77.0% |
| `SKIPPED_PIPELINE_FAIL` | 168 | 9.1% |

### REFERENCE_BUG Deep Dive (15 cases)
*These are items where the HumanEval+ reference solution itself appears to be incorrect. The verifier's override was justified — the candidate was actually more correct than the reference.*

**Affected item IDs:** code_HumanEval_126, code_HumanEval_134, code_HumanEval_17, code_HumanEval_59, code_HumanEval_78

**By generator model (which model's candidate was vindicated):**
- qwen: 8
- deepseek: 5
- mistral: 1
- llama: 1

### Verdicts by Verifier Model

| Verifier | BUG_CONFIRMED | REFERENCE_BUG | NO_DISCREPANCY | SKIPPED_PIPELINE_FAIL |
|---|---|---|---|---|
| deepseek | 9 | 3 | 137 | 10 |
| llama | 25 | 0 | 206 | 18 |
| mistral | 129 | 12 | 1018 | 132 |
| qwen | 4 | 0 | 69 | 8 |

### Verdicts by Generator Model

| Generator | BUG_CONFIRMED | REFERENCE_BUG | NO_DISCREPANCY | SKIPPED_PIPELINE_FAIL |
|---|---|---|---|---|
| deepseek | 41 | 5 | 436 | 40 |
| llama | 62 | 1 | 279 | 50 |
| mistral | 17 | 1 | 322 | 17 |
| qwen | 47 | 8 | 393 | 61 |

### Verifier Override Accuracy
*% of overrides that were JUSTIFIED (BUG_CONFIRMED) vs. UNJUSTIFIED (NO_DISCREPANCY or REFERENCE_BUG)*

| Verifier | Total Overrides | Justified (%) | Unjustified (%) | Inconclusive (%) |
|---|---|---|---|---|
| deepseek | 159 | 5.7% | 88.1% | 6.3% |
| llama | 249 | 10.0% | 82.7% | 7.2% |
| mistral | 1291 | 10.0% | 79.8% | 10.2% |
| qwen | 81 | 4.9% | 85.2% | 9.9% |


## 7. Domain-Specific Validity Checks
*These checks are diagnostic safeguards around domain-specific grading. They support the shared metrics above; they do not replace the common accuracy/FPR/FNR analysis.*

Full table: `actual_math_domain_validity_checks.csv`.

### Code: Execution Grounding
*Instances where the code passed the test suite, but the verifier LLM overrode that execution signal and marked it INCORRECT.*
*(No code domain data present)*

### Science: Option Extraction Audit
*Science grading uses the shared correctness metrics above, with an additional parser audit because GPQA answers must map cleanly to one of A-D.*
*(No science domain data present)*

### Math: Answer Matching
- Math candidates are graded by boxed-answer extraction first, then numeric/exact matching. Symbolically equivalent but differently formatted answers remain a limitation to mention in the paper.
- **Math Verification Rows**: 21600

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 69.9% | 54.3% |
| deepseek | other | Yes | 64.2% | 70.6% |
| deepseek | self | No | 69.0% | 55.6% |
| deepseek | self | Yes | 64.0% | 71.1% |
| llama | other | No | 62.0% | 73.5% |
| llama | other | Yes | 72.4% | 93.3% |
| llama | self | No | 63.3% | 71.4% |
| llama | self | Yes | 72.9% | 91.7% |
| mistral | other | No | 62.9% | 89.9% |
| mistral | other | Yes | 45.8% | 86.0% |
| mistral | self | No | 62.9% | 91.4% |
| mistral | self | Yes | 43.8% | 89.2% |
| qwen | other | No | 68.4% | 62.2% |
| qwen | other | Yes | 61.8% | 86.8% |
| qwen | self | No | 67.9% | 64.0% |
| qwen | self | Yes | 62.7% | 85.2% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `actual_math_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 2708 | **False Positives:** 1404 | **True Negatives:** 972 | **False Negatives:** 316

![Confusion Matrix deepseek](../../../plots/actual/math/actual_math_confusion_matrix_deepseek.png)
### llama
**True Positives:** 2943 | **False Positives:** 1809 | **True Negatives:** 567 | **False Negatives:** 81

![Confusion Matrix llama](../../../plots/actual/math/actual_math_confusion_matrix_llama.png)
### mistral
**True Positives:** 2915 | **False Positives:** 2138 | **True Negatives:** 238 | **False Negatives:** 109

![Confusion Matrix mistral](../../../plots/actual/math/actual_math_confusion_matrix_mistral.png)
### qwen
**True Positives:** 2857 | **False Positives:** 1642 | **True Negatives:** 734 | **False Negatives:** 167

![Confusion Matrix qwen](../../../plots/actual/math/actual_math_confusion_matrix_qwen.png)
