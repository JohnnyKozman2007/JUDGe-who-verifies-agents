# Dynamic Executive Summary

**Total Verifications Processed:** 64800
**Pipeline Failures Handled:** 244 (These defaulted to basic test suite results rather than dropping rows)

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/actual/all/actual_all_accuracy_by_domain.png)

- **Code**: mistral (Frame: self, Strategy: direct) achieved **97.7%** accuracy (**97.5% Adjusted**).
- **Math**: deepseek (Frame: neutral, Strategy: rubric) achieved **69.2%** accuracy (**69.2% Adjusted**).
- **Science**: deepseek (Frame: other, Strategy: cot) achieved **65.8%** accuracy (**65.8% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **other** frame & **direct** strategy (**92.0%**)
- **llama**: Prefers **other** frame & **cot** strategy (**92.5%**)
- **mistral**: Prefers **self** frame & **direct** strategy (**97.7%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**97.3%**)
### Math
- **deepseek**: Prefers **neutral** frame & **rubric** strategy (**69.2%**)
- **llama**: Prefers **self** frame & **cot** strategy (**66.0%**)
- **mistral**: Prefers **other** frame & **rubric** strategy (**59.5%**)
- **qwen**: Prefers **other** frame & **direct** strategy (**67.3%**)
### Science
- **deepseek**: Prefers **other** frame & **cot** strategy (**65.8%**)
- **llama**: Prefers **self** frame & **cot** strategy (**60.8%**)
- **mistral**: Prefers **self** frame & **rubric** strategy (**53.0%**)
- **qwen**: Prefers **neutral** frame & **rubric** strategy (**59.2%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 74.1% | 74.0% | 73.9% |
| **llama** | 72.3% | 69.4% | 71.5% |
| **mistral** | 60.1% | 67.3% | 58.1% |
| **qwen** | 71.6% | 73.3% | 71.9% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 74.1% | 74.0% | 73.9% |
| **llama** | 72.2% | 69.4% | 71.4% |
| **mistral** | 60.3% | 67.3% | 58.5% |
| **qwen** | 71.5% | 73.2% | 71.9% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 69.8%
### By Domain
- **Code**: 87.7%
- **Math**: 64.5%
- **Science**: 57.2%
### By Strategy
- **cot**: 69.5%
- **direct**: 71.0%
- **rubric**: 68.8%
### By Ownership Frame
- **neutral**: 69.3%
- **other**: 69.9%
- **self**: 70.2%
### By Model
- **deepseek**: 74.0%
- **llama**: 71.1%
- **mistral**: 61.8%
- **qwen**: 72.2%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 71.3%
- **other + direct**: 71.0%
- **neutral + direct**: 70.6%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 69.8%
### By Domain
- **Code**: 87.7%
- **Math**: 64.5%
- **Science**: 57.2%
### By Strategy
- **cot**: 69.5%
- **direct**: 70.9%
- **rubric**: 68.9%
### By Ownership Frame
- **neutral**: 69.3%
- **other**: 69.9%
- **self**: 70.2%
### By Model
- **deepseek**: 74.0%
- **llama**: 71.0%
- **mistral**: 62.0%
- **qwen**: 72.2%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 71.2%
- **other + direct**: 71.0%
- **neutral + direct**: 70.6%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.0%
### By Domain
- **Code**: 0.0%
- **Math**: 0.0%
- **Science**: 0.0%
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
- **Overall**: 194.5
### By Domain
- **Code**: 192.9
- **Math**: 180.0
- **Science**: 210.6
### By Strategy
- **cot**: 314.2
- **direct**: 0.0
- **rubric**: 269.3
### By Ownership Frame
- **neutral**: 194.1
- **other**: 194.5
- **self**: 194.9
### By Model
- **deepseek**: 189.3
- **llama**: 239.4
- **mistral**: 173.3
- **qwen**: 176.0
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 314.7
- **self + cot**: 314.6
- **neutral + cot**: 313.2

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 46.1% | Passed: 53.9% | Introduced: 11.9% | Confirmed: 88.1%
### By Domain
- **code** -> Caught: 81.6% | Passed: 18.4% | Introduced: 9.6% | Confirmed: 90.4%
- **math** -> Caught: 26.4% | Passed: 73.6% | Introduced: 5.6% | Confirmed: 94.4%
- **science** -> Caught: 41.9% | Passed: 58.1% | Introduced: 23.6% | Confirmed: 76.4%
### By Strategy
- **cot** -> Caught: 46.4% | Passed: 53.6% | Introduced: 12.6% | Confirmed: 87.4%
- **direct** -> Caught: 44.0% | Passed: 56.0% | Introduced: 8.2% | Confirmed: 91.8%
- **rubric** -> Caught: 47.8% | Passed: 52.2% | Introduced: 14.9% | Confirmed: 85.1%
### By Ownership Frame
- **neutral** -> Caught: 45.0% | Passed: 55.0% | Introduced: 12.0% | Confirmed: 88.0%
- **other** -> Caught: 46.4% | Passed: 53.6% | Introduced: 12.0% | Confirmed: 88.0%
- **self** -> Caught: 46.9% | Passed: 53.1% | Introduced: 11.8% | Confirmed: 88.2%
### By Model
- **deepseek** -> Caught: 58.5% | Passed: 41.5% | Introduced: 14.1% | Confirmed: 85.9%
- **llama** -> Caught: 45.1% | Passed: 54.9% | Introduced: 8.9% | Confirmed: 91.1%
- **mistral** -> Caught: 33.2% | Passed: 66.8% | Introduced: 16.1% | Confirmed: 83.9%
- **qwen** -> Caught: 47.4% | Passed: 52.6% | Introduced: 8.6% | Confirmed: 91.4%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/actual/all/actual_all_fpr_self_bias.png)

- **mistral** (math, rubric): **+3.8%** bias
- **mistral** (code, rubric): **+3.2%** bias
- **deepseek** (science, cot): **+3.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/actual/all/actual_all_fnr_self_bias.png)

- **llama** (science, rubric): **+4.9%** bias
- **llama** (science, cot): **+4.2%** bias
- **llama** (code, cot): **+2.4%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **mistral** (math, rubric): FPR Bias p=0.2592 | FNR Bias p=1.0000
- **mistral** (code, rubric): FPR Bias p=0.3257 | FNR Bias p=0.5308
- **deepseek** (science, cot): FPR Bias p=0.4658 | FNR Bias p=1.0000

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/actual/all/actual_all_adj_fpr_self_bias.png)

- **mistral** (math, rubric): **+3.8%** adjusted bias
- **deepseek** (science, cot): **+3.0%** adjusted bias
- **mistral** (math, cot): **+2.7%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/actual/all/actual_all_adj_fnr_self_bias.png)

- **llama** (science, rubric): **+4.9%** adjusted bias
- **llama** (science, cot): **+4.2%** adjusted bias
- **llama** (code, cot): **+2.4%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **mistral** (math, rubric): Adj FPR Bias p=0.2592 | Adj FNR Bias p=1.0000
- **deepseek** (science, cot): Adj FPR Bias p=0.4658 | Adj FNR Bias p=1.0000
- **mistral** (math, cot): Adj FPR Bias p=0.4001 | Adj FNR Bias p=0.5625

Full adjusted bias table: `actual_all_adj_bias_metrics.csv`.

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

Full table: `actual_all_domain_validity_checks.csv`.

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
- **Candidate Parse Rate**: 99.8% of science verification rows had a detected A-D answer.
- **Ambiguous Candidate Rate**: 0.2% of science verification rows were marked ambiguous by the parser.
- **Best Science Generator**: deepseek with 51.3% generation accuracy.
- **Best Science Verifier Cell**: deepseek / other / cot at 65.8% accuracy.
- **Highest Science False-Approval Cell**: mistral / neutral / direct with 92.5% FPR.
Full science audit files: `actual_all_science_generation_audit.csv`, `actual_all_science_generator_summary.csv`, `actual_all_science_verifier_diagnostics.csv`.

### Math: Answer Matching
- Math candidates are graded by boxed-answer extraction first, then numeric/exact matching. Symbolically equivalent but differently formatted answers remain a limitation to mention in the paper.
- **Math Verification Rows**: 21600

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 75.2% | 35.4% |
| deepseek | other | Yes | 72.0% | 60.0% |
| deepseek | self | No | 74.8% | 36.2% |
| deepseek | self | Yes | 71.4% | 61.2% |
| llama | other | No | 70.4% | 54.8% |
| llama | other | Yes | 72.1% | 61.3% |
| llama | self | No | 71.3% | 50.8% |
| llama | self | Yes | 74.2% | 54.9% |
| mistral | other | No | 63.3% | 67.8% |
| mistral | other | Yes | 57.4% | 61.3% |
| mistral | self | No | 64.4% | 68.5% |
| mistral | self | Yes | 57.3% | 63.7% |
| qwen | other | No | 73.7% | 47.3% |
| qwen | other | Yes | 68.8% | 67.4% |
| qwen | self | No | 73.5% | 47.7% |
| qwen | self | Yes | 68.4% | 67.6% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `actual_all_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 7858 | **False Positives:** 2929 | **True Negatives:** 4127 | **False Negatives:** 1286

![Confusion Matrix deepseek](../../../plots/actual/all/actual_all_confusion_matrix_deepseek.png)
### llama
**True Positives:** 8332 | **False Positives:** 3874 | **True Negatives:** 3182 | **False Negatives:** 812

![Confusion Matrix llama](../../../plots/actual/all/actual_all_confusion_matrix_llama.png)
### mistral
**True Positives:** 7673 | **False Positives:** 4711 | **True Negatives:** 2345 | **False Negatives:** 1471

![Confusion Matrix mistral](../../../plots/actual/all/actual_all_confusion_matrix_mistral.png)
### qwen
**True Positives:** 8354 | **False Positives:** 3708 | **True Negatives:** 3348 | **False Negatives:** 790

![Confusion Matrix qwen](../../../plots/actual/all/actual_all_confusion_matrix_qwen.png)
