# Dynamic Executive Summary

**Total Verifications Processed:** 1440

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/pilot/math/pilot_math_accuracy_by_domain.png)

- **Math**: deepseek (Frame: neutral, Strategy: direct) achieved **95.0%** accuracy (**95.0% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Math
- **deepseek**: Prefers **neutral** frame & **direct** strategy (**95.0%**)
- **llama**: Prefers **neutral** frame & **rubric** strategy (**92.5%**)
- **mistral**: Prefers **self** frame & **cot** strategy (**82.5%**)
- **qwen**: Prefers **neutral** frame & **cot** strategy (**90.0%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 92.5% | 92.5% | 92.5% |
| **llama** | 91.7% | 89.2% | 91.7% |
| **mistral** | 80.0% | 79.2% | 79.2% |
| **qwen** | 90.0% | 89.2% | 90.0% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 92.5% | 92.5% | 92.5% |
| **llama** | 91.7% | 89.2% | 91.7% |
| **mistral** | 80.0% | 79.2% | 79.2% |
| **qwen** | 90.0% | 89.2% | 90.0% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 88.1%
### By Domain
- **Math**: 88.1%
### By Strategy
- **cot**: 88.5%
- **direct**: 87.5%
- **rubric**: 88.3%
### By Ownership Frame
- **neutral**: 87.9%
- **other**: 88.8%
- **self**: 87.7%
### By Model
- **deepseek**: 92.5%
- **llama**: 90.8%
- **mistral**: 79.4%
- **qwen**: 89.7%
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 89.4%
- **self + cot**: 88.8%
- **other + rubric**: 88.8%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 88.1%
### By Domain
- **Math**: 88.1%
### By Strategy
- **cot**: 88.5%
- **direct**: 87.5%
- **rubric**: 88.3%
### By Ownership Frame
- **neutral**: 87.9%
- **other**: 88.8%
- **self**: 87.7%
### By Model
- **deepseek**: 92.5%
- **llama**: 90.8%
- **mistral**: 79.4%
- **qwen**: 89.7%
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 89.4%
- **self + cot**: 88.8%
- **other + rubric**: 88.8%

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
- **Overall**: 142.1
### By Domain
- **Math**: 142.1
### By Strategy
- **cot**: 236.4
- **direct**: 0.0
- **rubric**: 190.0
### By Ownership Frame
- **neutral**: 143.2
- **other**: 143.6
- **self**: 139.6
### By Model
- **deepseek**: 119.2
- **llama**: 194.6
- **mistral**: 137.9
- **qwen**: 116.7
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 245.0
- **neutral + cot**: 234.9
- **self + cot**: 229.1

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 55.8% | Passed: 44.2% | Introduced: 1.1% | Confirmed: 98.9%
### By Domain
- **math** -> Caught: 55.8% | Passed: 44.2% | Introduced: 1.1% | Confirmed: 98.9%
### By Strategy
- **cot** -> Caught: 57.5% | Passed: 42.5% | Introduced: 1.1% | Confirmed: 98.9%
- **direct** -> Caught: 50.0% | Passed: 50.0% | Introduced: 0.0% | Confirmed: 100.0%
- **rubric** -> Caught: 60.0% | Passed: 40.0% | Introduced: 2.2% | Confirmed: 97.8%
### By Ownership Frame
- **neutral** -> Caught: 55.0% | Passed: 45.0% | Introduced: 1.1% | Confirmed: 98.9%
- **other** -> Caught: 57.5% | Passed: 42.5% | Introduced: 0.8% | Confirmed: 99.2%
- **self** -> Caught: 55.0% | Passed: 45.0% | Introduced: 1.4% | Confirmed: 98.6%
### By Model
- **deepseek** -> Caught: 73.3% | Passed: 26.7% | Introduced: 1.1% | Confirmed: 98.9%
- **llama** -> Caught: 63.3% | Passed: 36.7% | Introduced: 0.0% | Confirmed: 100.0%
- **mistral** -> Caught: 27.8% | Passed: 72.2% | Introduced: 3.3% | Confirmed: 96.7%
- **qwen** -> Caught: 58.9% | Passed: 41.1% | Introduced: 0.0% | Confirmed: 100.0%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/pilot/math/pilot_math_fpr_self_bias.png)

- **deepseek** (math, direct): **+10.0%** bias
- **deepseek** (math, cot): **+10.0%** bias
- **mistral** (math, direct): **+10.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/pilot/math/pilot_math_fnr_self_bias.png)

- **mistral** (math, rubric): **+3.3%** bias
- **deepseek** (math, cot): **+3.3%** bias
- **deepseek** (math, rubric): **+3.3%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **deepseek** (math, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **deepseek** (math, cot): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **mistral** (math, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/pilot/math/pilot_math_adj_fpr_self_bias.png)

- **deepseek** (math, direct): **+10.0%** adjusted bias
- **deepseek** (math, cot): **+10.0%** adjusted bias
- **mistral** (math, direct): **+10.0%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/pilot/math/pilot_math_adj_fnr_self_bias.png)

- **mistral** (math, rubric): **+3.3%** adjusted bias
- **deepseek** (math, cot): **+3.3%** adjusted bias
- **deepseek** (math, rubric): **+3.3%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **deepseek** (math, direct): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000
- **deepseek** (math, cot): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000
- **mistral** (math, direct): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000

Full adjusted bias table: `pilot_math_adj_bias_metrics.csv`.

## 6c. Oracle & Fuzzing Statistics (Code Domain)
*These rows represent code verifications where the verifier overrode a passing execution result (i.e. test passed but verifier said incorrect). The fuzzer ran differential testing on each and an LLM oracle adjudicated mismatches. This section quantifies how often the verifier was right vs. wrong, and how often the benchmark reference itself was the problem.*

**Total override cases fuzzed:** 70

### Verdict Breakdown

| Verdict | Count | % of Fuzzed |
|---|---|---|
| `BUG_CONFIRMED` | 0 | 0.0% |
| `REFERENCE_BUG` | 0 | 0.0% |
| `NO_DISCREPANCY` | 58 | 82.9% |
| `SKIPPED_PIPELINE_FAIL` | 12 | 17.1% |

### Verdicts by Verifier Model

| Verifier | BUG_CONFIRMED | REFERENCE_BUG | NO_DISCREPANCY | SKIPPED_PIPELINE_FAIL |
|---|---|---|---|---|
| deepseek | 0 | 0 | 5 | 2 |
| llama | 0 | 0 | 10 | 0 |
| mistral | 0 | 0 | 42 | 10 |
| qwen | 0 | 0 | 1 | 0 |

### Verdicts by Generator Model

| Generator | BUG_CONFIRMED | REFERENCE_BUG | NO_DISCREPANCY | SKIPPED_PIPELINE_FAIL |
|---|---|---|---|---|
| deepseek | 0 | 0 | 32 | 10 |
| llama | 0 | 0 | 2 | 1 |
| mistral | 0 | 0 | 6 | 1 |
| qwen | 0 | 0 | 18 | 0 |

### Verifier Override Accuracy
*% of overrides that were JUSTIFIED (BUG_CONFIRMED) vs. UNJUSTIFIED (NO_DISCREPANCY or REFERENCE_BUG)*

| Verifier | Total Overrides | Justified (%) | Unjustified (%) | Inconclusive (%) |
|---|---|---|---|---|
| deepseek | 7 | 0.0% | 71.4% | 28.6% |
| llama | 10 | 0.0% | 100.0% | 0.0% |
| mistral | 52 | 0.0% | 80.8% | 19.2% |
| qwen | 1 | 0.0% | 100.0% | 0.0% |


## 7. Domain-Specific Validity Checks
*These checks are diagnostic safeguards around domain-specific grading. They support the shared metrics above; they do not replace the common accuracy/FPR/FNR analysis.*

Full table: `pilot_math_domain_validity_checks.csv`.

### Code: Execution Grounding
*Instances where the code passed the test suite, but the verifier LLM overrode that execution signal and marked it INCORRECT.*
*(No code domain data present)*

### Science: Option Extraction Audit
*Science grading uses the shared correctness metrics above, with an additional parser audit because GPQA answers must map cleanly to one of A-D.*
*(No science domain data present)*

### Math: Answer Matching
- Math candidates are graded by boxed-answer extraction first, then numeric/exact matching. Symbolically equivalent but differently formatted answers remain a limitation to mention in the paper.
- **Math Verification Rows**: 1440

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 95.6% | 16.7% |
| deepseek | other | Yes | 90.0% | 50.0% |
| deepseek | self | No | 91.1% | 25.0% |
| deepseek | self | Yes | 90.0% | 50.0% |
| llama | other | No | 88.9% | 37.0% |
| llama | other | Yes | 96.7% | 33.3% |
| llama | self | No | 88.9% | 37.0% |
| llama | self | Yes | 96.7% | 33.3% |
| mistral | other | No | 84.4% | 61.1% |
| mistral | other | Yes | 66.7% | 83.3% |
| mistral | self | No | 84.4% | 61.1% |
| mistral | self | Yes | 63.3% | 91.7% |
| qwen | other | No | 93.3% | 28.6% |
| qwen | other | Yes | 80.0% | 66.7% |
| qwen | self | No | 93.3% | 28.6% |
| qwen | self | Yes | 80.0% | 66.7% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `pilot_math_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 267 | **False Positives:** 24 | **True Negatives:** 66 | **False Negatives:** 3

![Confusion Matrix deepseek](../../../plots/pilot/math/pilot_math_confusion_matrix_deepseek.png)
### llama
**True Positives:** 270 | **False Positives:** 33 | **True Negatives:** 57 | **False Negatives:** 0

![Confusion Matrix llama](../../../plots/pilot/math/pilot_math_confusion_matrix_llama.png)
### mistral
**True Positives:** 261 | **False Positives:** 65 | **True Negatives:** 25 | **False Negatives:** 9

![Confusion Matrix mistral](../../../plots/pilot/math/pilot_math_confusion_matrix_mistral.png)
### qwen
**True Positives:** 270 | **False Positives:** 37 | **True Negatives:** 53 | **False Negatives:** 0

![Confusion Matrix qwen](../../../plots/pilot/math/pilot_math_confusion_matrix_qwen.png)
