# Dynamic Executive Summary

**Total Verifications Processed:** 21600
**Pipeline Failures Handled:** 244 (These defaulted to basic test suite results rather than dropping rows)

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/actual/code/actual_code_accuracy_by_domain.png)

- **Code**: mistral (Frame: self, Strategy: direct) achieved **97.7%** accuracy (**97.5% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **other** frame & **direct** strategy (**92.0%**)
- **llama**: Prefers **other** frame & **cot** strategy (**92.5%**)
- **mistral**: Prefers **self** frame & **direct** strategy (**97.7%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**97.3%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 89.1% | 91.4% | 89.8% |
| **llama** | 91.9% | 86.9% | 91.2% |
| **mistral** | 71.7% | 97.4% | 63.9% |
| **qwen** | 90.9% | 96.7% | 90.6% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 89.2% | 91.4% | 89.7% |
| **llama** | 91.6% | 86.9% | 90.9% |
| **mistral** | 72.3% | 97.4% | 65.0% |
| **qwen** | 90.9% | 96.4% | 90.6% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 87.7%
### By Domain
- **Code**: 87.7%
### By Strategy
- **cot**: 85.9%
- **direct**: 93.1%
- **rubric**: 83.9%
### By Ownership Frame
- **neutral**: 86.9%
- **other**: 87.6%
- **self**: 88.5%
### By Model
- **deepseek**: 90.1%
- **llama**: 90.0%
- **mistral**: 77.7%
- **qwen**: 92.8%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 93.5%
- **other + direct**: 93.1%
- **neutral + direct**: 92.8%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 87.7%
### By Domain
- **Code**: 87.7%
### By Strategy
- **cot**: 86.0%
- **direct**: 93.0%
- **rubric**: 84.1%
### By Ownership Frame
- **neutral**: 87.1%
- **other**: 87.6%
- **self**: 88.5%
### By Model
- **deepseek**: 90.1%
- **llama**: 89.8%
- **mistral**: 78.3%
- **qwen**: 92.6%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 93.3%
- **other + direct**: 93.1%
- **neutral + direct**: 92.7%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.0%
### By Domain
- **Code**: 0.0%
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
- **Overall**: 192.9
### By Domain
- **Code**: 192.9
### By Strategy
- **cot**: 304.3
- **direct**: 0.0
- **rubric**: 274.5
### By Ownership Frame
- **neutral**: 192.4
- **other**: 193.3
- **self**: 193.1
### By Model
- **deepseek**: 187.1
- **llama**: 224.9
- **mistral**: 183.0
- **qwen**: 176.7
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 305.6
- **self + cot**: 303.9
- **neutral + cot**: 303.3

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 81.6% | Passed: 18.4% | Introduced: 9.6% | Confirmed: 90.4%
### By Domain
- **code** -> Caught: 81.6% | Passed: 18.4% | Introduced: 9.6% | Confirmed: 90.4%
### By Strategy
- **cot** -> Caught: 79.9% | Passed: 20.1% | Introduced: 11.4% | Confirmed: 88.6%
- **direct** -> Caught: 84.5% | Passed: 15.5% | Introduced: 3.0% | Confirmed: 97.0%
- **rubric** -> Caught: 80.3% | Passed: 19.7% | Introduced: 14.5% | Confirmed: 85.5%
### By Ownership Frame
- **neutral** -> Caught: 80.5% | Passed: 19.5% | Introduced: 10.2% | Confirmed: 89.8%
- **other** -> Caught: 81.1% | Passed: 18.9% | Introduced: 9.5% | Confirmed: 90.5%
- **self** -> Caught: 83.1% | Passed: 16.9% | Introduced: 9.2% | Confirmed: 90.8%
### By Model
- **deepseek** -> Caught: 75.9% | Passed: 24.1% | Introduced: 3.6% | Confirmed: 96.4%
- **llama** -> Caught: 78.0% | Passed: 22.0% | Introduced: 4.6% | Confirmed: 95.4%
- **mistral** -> Caught: 92.7% | Passed: 7.3% | Introduced: 29.0% | Confirmed: 71.0%
- **qwen** -> Caught: 79.6% | Passed: 20.4% | Introduced: 1.4% | Confirmed: 98.6%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/actual/code/actual_code_fpr_self_bias.png)

- **mistral** (code, rubric): **+3.2%** bias
- **deepseek** (code, rubric): **+0.5%** bias
- **qwen** (code, direct): **+0.5%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/actual/code/actual_code_fnr_self_bias.png)

- **llama** (code, cot): **+2.4%** bias
- **llama** (code, rubric): **+1.4%** bias
- **deepseek** (code, direct): **+1.0%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **mistral** (code, rubric): FPR Bias p=0.3257 | FNR Bias p=0.5308
- **deepseek** (code, rubric): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **qwen** (code, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/actual/code/actual_code_adj_fpr_self_bias.png)

- **qwen** (code, direct): **+1.5%** adjusted bias
- **deepseek** (code, rubric): **+0.3%** adjusted bias
- **mistral** (code, rubric): **+0.2%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/actual/code/actual_code_adj_fnr_self_bias.png)

- **llama** (code, cot): **+2.4%** adjusted bias
- **llama** (code, rubric): **+1.2%** adjusted bias
- **deepseek** (code, direct): **+0.7%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **qwen** (code, direct): Adj FPR Bias p=0.7397 | Adj FNR Bias p=1.0000
- **deepseek** (code, rubric): Adj FPR Bias p=1.0000 | Adj FNR Bias p=0.7050
- **mistral** (code, rubric): Adj FPR Bias p=1.0000 | Adj FNR Bias p=0.3549

Full adjusted bias table: `actual_code_adj_bias_metrics.csv`.

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

Full table: `actual_code_domain_validity_checks.csv`.

### Code: Execution Grounding
*Instances where the code passed the test suite, but the verifier LLM overrode that execution signal and marked it INCORRECT.*
- **Total Overrides**: 1458 out of 14940 passing submissions.

#### By Verifier Model
- **deepseek**: 137
- **llama**: 176
- **mistral**: 1091
- **qwen**: 54

### Science: Option Extraction Audit
*Science grading uses the shared correctness metrics above, with an additional parser audit because GPQA answers must map cleanly to one of A-D.*
*(No science domain data present)*

### Math: Answer Matching
*(No math domain data present)*

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 91.2% | 18.7% |
| deepseek | other | Yes | 88.4% | 46.7% |
| deepseek | self | No | 91.1% | 17.4% |
| deepseek | self | Yes | 88.4% | 47.8% |
| llama | other | No | 90.9% | 20.8% |
| llama | other | Yes | 87.1% | 33.3% |
| llama | self | No | 91.3% | 15.5% |
| llama | self | Yes | 89.3% | 26.2% |
| mistral | other | No | 75.7% | 7.0% |
| mistral | other | Yes | 83.1% | 6.7% |
| mistral | self | No | 77.9% | 7.2% |
| mistral | self | Yes | 84.2% | 8.1% |
| qwen | other | No | 92.4% | 19.5% |
| qwen | other | Yes | 92.0% | 28.9% |
| qwen | self | No | 93.3% | 17.7% |
| qwen | self | Yes | 92.7% | 26.3% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `actual_code_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 3602 | **False Positives:** 401 | **True Negatives:** 1264 | **False Negatives:** 133

![Confusion Matrix deepseek](../../../plots/actual/code/actual_code_confusion_matrix_deepseek.png)
### llama
**True Positives:** 3564 | **False Positives:** 367 | **True Negatives:** 1298 | **False Negatives:** 171

![Confusion Matrix llama](../../../plots/actual/code/actual_code_confusion_matrix_llama.png)
### mistral
**True Positives:** 2652 | **False Positives:** 121 | **True Negatives:** 1544 | **False Negatives:** 1083

![Confusion Matrix mistral](../../../plots/actual/code/actual_code_confusion_matrix_mistral.png)
### qwen
**True Positives:** 3683 | **False Positives:** 339 | **True Negatives:** 1326 | **False Negatives:** 52

![Confusion Matrix qwen](../../../plots/actual/code/actual_code_confusion_matrix_qwen.png)
