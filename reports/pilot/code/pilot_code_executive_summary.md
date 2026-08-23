# Dynamic Executive Summary

**Total Verifications Processed:** 1440
**Pipeline Failures Handled:** 12 (These defaulted to basic test suite results rather than dropping rows)

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/pilot/code/pilot_code_accuracy_by_domain.png)

- **Code**: qwen (Frame: neutral, Strategy: direct) achieved **97.5%** accuracy (**97.5% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **self** frame & **direct** strategy (**95.0%**)
- **llama**: Prefers **neutral** frame & **cot** strategy (**90.0%**)
- **mistral**: Prefers **self** frame & **direct** strategy (**95.0%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**97.5%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 82.5% | 90.0% | 90.8% |
| **llama** | 89.2% | 79.2% | 86.7% |
| **mistral** | 75.0% | 93.3% | 77.3% |
| **qwen** | 85.8% | 95.8% | 89.2% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 82.5% | 90.0% | 90.8% |
| **llama** | 89.2% | 79.2% | 86.7% |
| **mistral** | 75.0% | 93.3% | 77.3% |
| **qwen** | 85.8% | 95.8% | 89.2% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 86.2%
### By Domain
- **Code**: 86.2%
### By Strategy
- **cot**: 83.1%
- **direct**: 89.6%
- **rubric**: 86.0%
### By Ownership Frame
- **neutral**: 86.5%
- **other**: 84.8%
- **self**: 87.5%
### By Model
- **deepseek**: 87.8%
- **llama**: 85.0%
- **mistral**: 81.9%
- **qwen**: 90.3%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 91.9%
- **neutral + direct**: 88.8%
- **other + direct**: 88.1%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 86.2%
### By Domain
- **Code**: 86.2%
### By Strategy
- **cot**: 83.1%
- **direct**: 89.6%
- **rubric**: 86.0%
### By Ownership Frame
- **neutral**: 86.5%
- **other**: 84.8%
- **self**: 87.5%
### By Model
- **deepseek**: 87.8%
- **llama**: 85.0%
- **mistral**: 81.9%
- **qwen**: 90.3%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 91.9%
- **neutral + direct**: 88.8%
- **other + direct**: 88.1%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.1%
### By Domain
- **Code**: 0.1%
### By Strategy
- **cot**: 0.0%
- **direct**: 0.0%
- **rubric**: 0.2%
### By Ownership Frame
- **neutral**: 0.0%
- **other**: 0.0%
- **self**: 0.2%
### By Model
- **deepseek**: 0.0%
- **llama**: 0.0%
- **mistral**: 0.3%
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
- **cot**: 302.2
- **direct**: 0.0
- **rubric**: 276.4
### By Ownership Frame
- **neutral**: 191.0
- **other**: 192.1
- **self**: 195.5
### By Model
- **deepseek**: 184.1
- **llama**: 231.0
- **mistral**: 171.2
- **qwen**: 185.3
### Top 3 Best Ownership + Strategy Combos
- **self + cot**: 308.4
- **other + cot**: 299.6
- **neutral + cot**: 298.6

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 84.7% | Passed: 15.3% | Introduced: 12.2% | Confirmed: 87.8%
### By Domain
- **code** -> Caught: 84.7% | Passed: 15.3% | Introduced: 12.2% | Confirmed: 87.8%
### By Strategy
- **cot** -> Caught: 82.5% | Passed: 17.5% | Introduced: 16.2% | Confirmed: 83.8%
- **direct** -> Caught: 85.8% | Passed: 14.2% | Introduced: 6.7% | Confirmed: 93.3%
- **rubric** -> Caught: 85.8% | Passed: 14.2% | Introduced: 13.8% | Confirmed: 86.2%
### By Ownership Frame
- **neutral** -> Caught: 85.0% | Passed: 15.0% | Introduced: 12.1% | Confirmed: 87.9%
- **other** -> Caught: 82.1% | Passed: 17.9% | Introduced: 12.5% | Confirmed: 87.5%
- **self** -> Caught: 87.0% | Passed: 13.0% | Introduced: 12.1% | Confirmed: 87.9%
### By Model
- **deepseek** -> Caught: 79.4% | Passed: 20.6% | Introduced: 3.9% | Confirmed: 96.1%
- **llama** -> Caught: 85.0% | Passed: 15.0% | Introduced: 15.0% | Confirmed: 85.0%
- **mistral** -> Caught: 93.3% | Passed: 6.7% | Introduced: 29.4% | Confirmed: 70.6%
- **qwen** -> Caught: 81.1% | Passed: 18.9% | Introduced: 0.6% | Confirmed: 99.4%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/pilot/code/pilot_code_fpr_self_bias.png)

- **deepseek** (code, cot): **+10.0%** bias
- **llama** (code, cot): **+0.0%** bias
- **mistral** (code, cot): **+0.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/pilot/code/pilot_code_fnr_self_bias.png)

- **mistral** (code, cot): **+5.0%** bias
- **deepseek** (code, cot): **+5.0%** bias
- **qwen** (code, cot): **+5.0%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **deepseek** (code, cot): FPR Bias p=0.7301 | FNR Bias p=1.0000
- **llama** (code, cot): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **mistral** (code, cot): FPR Bias p=1.0000 | FNR Bias p=1.0000

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/pilot/code/pilot_code_adj_fpr_self_bias.png)

- **deepseek** (code, cot): **+10.0%** adjusted bias
- **llama** (code, cot): **+0.0%** adjusted bias
- **mistral** (code, cot): **+0.0%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/pilot/code/pilot_code_adj_fnr_self_bias.png)

- **mistral** (code, cot): **+5.0%** adjusted bias
- **deepseek** (code, cot): **+5.0%** adjusted bias
- **qwen** (code, cot): **+5.0%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **deepseek** (code, cot): Adj FPR Bias p=0.7301 | Adj FNR Bias p=1.0000
- **llama** (code, cot): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000
- **mistral** (code, cot): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000

Full adjusted bias table: `pilot_code_adj_bias_metrics.csv`.

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

Full table: `pilot_code_domain_validity_checks.csv`.

### Code: Execution Grounding
*Instances where the code passed the test suite, but the verifier LLM overrode that execution signal and marked it INCORRECT.*
- **Total Overrides**: 70 out of 720 passing submissions.

#### By Verifier Model
- **deepseek**: 7
- **llama**: 10
- **mistral**: 52
- **qwen**: 1

### Science: Option Extraction Audit
*Science grading uses the shared correctness metrics above, with an additional parser audit because GPQA answers must map cleanly to one of A-D.*
*(No science domain data present)*

### Math: Answer Matching
*(No math domain data present)*

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 87.8% | 17.6% |
| deepseek | other | Yes | 80.0% | 66.7% |
| deepseek | self | No | 88.9% | 17.6% |
| deepseek | self | Yes | 90.0% | 22.2% |
| llama | other | No | 86.7% | 11.9% |
| llama | other | Yes | 73.3% | 27.8% |
| llama | self | No | 90.0% | 7.1% |
| llama | self | Yes | 76.7% | 22.2% |
| mistral | other | No | 77.8% | 11.9% |
| mistral | other | Yes | 90.0% | 0.0% |
| mistral | self | No | 80.9% | 4.9% |
| mistral | self | Yes | 90.0% | 5.6% |
| qwen | other | No | 90.0% | 20.0% |
| qwen | other | Yes | 86.7% | 26.7% |
| qwen | self | No | 91.1% | 15.6% |
| qwen | self | Yes | 90.0% | 20.0% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `pilot_code_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 173 | **False Positives:** 37 | **True Negatives:** 143 | **False Negatives:** 7

![Confusion Matrix deepseek](../../../plots/pilot/code/pilot_code_confusion_matrix_deepseek.png)
### llama
**True Positives:** 153 | **False Positives:** 27 | **True Negatives:** 153 | **False Negatives:** 27

![Confusion Matrix llama](../../../plots/pilot/code/pilot_code_confusion_matrix_llama.png)
### mistral
**True Positives:** 127 | **False Positives:** 12 | **True Negatives:** 167 | **False Negatives:** 53

![Confusion Matrix mistral](../../../plots/pilot/code/pilot_code_confusion_matrix_mistral.png)
### qwen
**True Positives:** 179 | **False Positives:** 34 | **True Negatives:** 146 | **False Negatives:** 1

![Confusion Matrix qwen](../../../plots/pilot/code/pilot_code_confusion_matrix_qwen.png)
