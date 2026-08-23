# Dynamic Executive Summary

**Total Verifications Processed:** 4320
**Pipeline Failures Handled:** 12 (These defaulted to basic test suite results rather than dropping rows)

## Highest Accuracy by Domain
![Accuracy Plot](../../../plots/pilot/all/pilot_all_accuracy_by_domain.png)

- **Code**: qwen (Frame: neutral, Strategy: direct) achieved **97.5%** accuracy (**97.5% Adjusted**).
- **Math**: deepseek (Frame: neutral, Strategy: direct) achieved **95.0%** accuracy (**95.0% Adjusted**).
- **Science**: deepseek (Frame: neutral, Strategy: direct) achieved **77.5%** accuracy (**77.5% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **self** frame & **direct** strategy (**95.0%**)
- **llama**: Prefers **neutral** frame & **cot** strategy (**90.0%**)
- **mistral**: Prefers **self** frame & **direct** strategy (**95.0%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**97.5%**)
### Math
- **deepseek**: Prefers **neutral** frame & **direct** strategy (**95.0%**)
- **llama**: Prefers **neutral** frame & **rubric** strategy (**92.5%**)
- **mistral**: Prefers **self** frame & **cot** strategy (**82.5%**)
- **qwen**: Prefers **neutral** frame & **cot** strategy (**90.0%**)
### Science
- **deepseek**: Prefers **neutral** frame & **direct** strategy (**77.5%**)
- **llama**: Prefers **other** frame & **rubric** strategy (**67.5%**)
- **mistral**: Prefers **other** frame & **cot** strategy (**75.0%**)
- **qwen**: Prefers **neutral** frame & **cot** strategy (**67.5%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 80.6% | 86.7% | 83.6% |
| **llama** | 82.2% | 76.7% | 81.7% |
| **mistral** | 75.3% | 77.2% | 74.1% |
| **qwen** | 80.8% | 82.5% | 81.7% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 80.6% | 86.7% | 83.6% |
| **llama** | 82.2% | 76.7% | 81.7% |
| **mistral** | 75.3% | 77.2% | 74.1% |
| **qwen** | 80.8% | 82.5% | 81.7% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 80.2%
### By Domain
- **Code**: 86.2%
- **Math**: 88.1%
- **Science**: 66.4%
### By Strategy
- **cot**: 79.7%
- **direct**: 80.8%
- **rubric**: 80.3%
### By Ownership Frame
- **neutral**: 80.0%
- **other**: 80.3%
- **self**: 80.5%
### By Model
- **deepseek**: 83.6%
- **llama**: 80.2%
- **mistral**: 75.5%
- **qwen**: 81.7%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 81.2%
- **self + rubric**: 81.0%
- **other + direct**: 80.8%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 80.2%
### By Domain
- **Code**: 86.2%
- **Math**: 88.1%
- **Science**: 66.4%
### By Strategy
- **cot**: 79.7%
- **direct**: 80.8%
- **rubric**: 80.3%
### By Ownership Frame
- **neutral**: 80.0%
- **other**: 80.3%
- **self**: 80.5%
### By Model
- **deepseek**: 83.6%
- **llama**: 80.2%
- **mistral**: 75.5%
- **qwen**: 81.7%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 81.2%
- **self + rubric**: 81.0%
- **other + direct**: 80.8%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.0%
### By Domain
- **Code**: 0.1%
- **Math**: 0.0%
- **Science**: 0.0%
### By Strategy
- **cot**: 0.0%
- **direct**: 0.0%
- **rubric**: 0.1%
### By Ownership Frame
- **neutral**: 0.0%
- **other**: 0.0%
- **self**: 0.1%
### By Model
- **deepseek**: 0.0%
- **llama**: 0.0%
- **mistral**: 0.1%
- **qwen**: 0.0%
### Top 3 Best Ownership + Strategy Combos
- **neutral + cot**: 0.0%
- **neutral + direct**: 0.0%
- **neutral + rubric**: 0.0%

## 3. Verbosity Analysis (Average Characters)
### Overall Average Across Everything
- **Overall**: 181.8
### By Domain
- **Code**: 192.9
- **Math**: 142.1
- **Science**: 210.3
### By Strategy
- **cot**: 297.0
- **direct**: 0.0
- **rubric**: 248.3
### By Ownership Frame
- **neutral**: 182.1
- **other**: 182.3
- **self**: 181.0
### By Model
- **deepseek**: 170.6
- **llama**: 221.8
- **mistral**: 169.0
- **qwen**: 165.7
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 298.8
- **self + cot**: 296.7
- **neutral + cot**: 295.3

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 66.1% | Passed: 33.9% | Introduced: 10.7% | Confirmed: 89.3%
### By Domain
- **code** -> Caught: 84.7% | Passed: 15.3% | Introduced: 12.2% | Confirmed: 87.8%
- **math** -> Caught: 55.8% | Passed: 44.2% | Introduced: 1.1% | Confirmed: 98.9%
- **science** -> Caught: 50.3% | Passed: 49.7% | Introduced: 21.7% | Confirmed: 78.3%
### By Strategy
- **cot** -> Caught: 66.5% | Passed: 33.5% | Introduced: 11.8% | Confirmed: 88.2%
- **direct** -> Caught: 62.2% | Passed: 37.8% | Introduced: 7.3% | Confirmed: 92.7%
- **rubric** -> Caught: 69.6% | Passed: 30.4% | Introduced: 12.9% | Confirmed: 87.1%
### By Ownership Frame
- **neutral** -> Caught: 65.4% | Passed: 34.6% | Introduced: 10.6% | Confirmed: 89.4%
- **other** -> Caught: 65.8% | Passed: 34.2% | Introduced: 10.4% | Confirmed: 89.6%
- **self** -> Caught: 67.1% | Passed: 32.9% | Introduced: 11.0% | Confirmed: 89.0%
### By Model
- **deepseek** -> Caught: 75.2% | Passed: 24.8% | Introduced: 11.0% | Confirmed: 89.0%
- **llama** -> Caught: 65.5% | Passed: 34.5% | Introduced: 10.4% | Confirmed: 89.6%
- **mistral** -> Caught: 57.3% | Passed: 42.7% | Introduced: 12.8% | Confirmed: 87.2%
- **qwen** -> Caught: 66.4% | Passed: 33.6% | Introduced: 8.5% | Confirmed: 91.5%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../../../plots/pilot/all/pilot_all_fpr_self_bias.png)

- **mistral** (science, cot): **+29.4%** bias
- **deepseek** (science, cot): **+11.8%** bias
- **deepseek** (math, direct): **+10.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../../../plots/pilot/all/pilot_all_fnr_self_bias.png)

- **mistral** (science, rubric): **+13.0%** bias
- **mistral** (science, direct): **+13.0%** bias
- **llama** (science, rubric): **+8.7%** bias

### Statistical Significance (P-Values for Bias) — Raw numbers, chi-square per (verifier, domain, strategy) cell.
*Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale.*
- **mistral** (science, cot): FPR Bias p=0.1671 | FNR Bias p=0.6008
- **deepseek** (science, cot): FPR Bias p=0.7197 | FNR Bias p=1.0000
- **deepseek** (math, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000

## 6b. Statistical Bias — Fuzz-Adjusted (Corrected Ground Truth)
*Same analysis as Section 6 but using fuzz-adjusted ground truth for the code domain. Rows where the fuzzer found a `REFERENCE_BUG` (reference was wrong) or `BUG_CONFIRMED` (candidate had a real bug) are reclassified before computing FPR/FNR. For math and science domains the adjusted numbers are identical to raw. Differences between raw and adjusted in code domain reflect the impact of oracle corrections.*

### Top 3 Highest Adjusted Self-Preservation Biases (Adj FPR Gap)
![Adj FPR Bias Plot](../../../plots/pilot/all/pilot_all_adj_fpr_self_bias.png)

- **mistral** (science, cot): **+29.4%** adjusted bias
- **deepseek** (science, cot): **+11.8%** adjusted bias
- **deepseek** (math, direct): **+10.0%** adjusted bias

### Top 3 Highest Adjusted Self-Doubt Biases (Adj FNR Gap)
![Adj FNR Bias Plot](../../../plots/pilot/all/pilot_all_adj_fnr_self_bias.png)

- **mistral** (science, rubric): **+13.0%** adjusted bias
- **mistral** (science, direct): **+13.0%** adjusted bias
- **llama** (science, rubric): **+8.7%** adjusted bias

### Statistical Significance (P-Values for Adjusted Bias)
- **mistral** (science, cot): Adj FPR Bias p=0.1671 | Adj FNR Bias p=0.6008
- **deepseek** (science, cot): Adj FPR Bias p=0.7197 | Adj FNR Bias p=1.0000
- **deepseek** (math, direct): Adj FPR Bias p=1.0000 | Adj FNR Bias p=1.0000

Full adjusted bias table: `pilot_all_adj_bias_metrics.csv`.

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

Full table: `pilot_all_domain_validity_checks.csv`.

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
- **Candidate Parse Rate**: 100.0% of science verification rows had a detected A-D answer.
- **Ambiguous Candidate Rate**: 0.0% of science verification rows were marked ambiguous by the parser.
- **Best Science Generator**: llama with 70.0% generation accuracy.
- **Best Science Verifier Cell**: deepseek / neutral / direct at 77.5% accuracy.
- **Highest Science False-Approval Cell**: mistral / other / direct with 88.2% FPR.
Full science audit files: `pilot_all_science_generation_audit.csv`, `pilot_all_science_generator_summary.csv`, `pilot_all_science_verifier_diagnostics.csv`.

### Math: Answer Matching
- Math candidates are graded by boxed-answer extraction first, then numeric/exact matching. Symbolically equivalent but differently formatted answers remain a limitation to mention in the paper.
- **Math Verification Rows**: 1440

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 83.3% | 18.9% |
| deepseek | other | Yes | 83.3% | 50.0% |
| deepseek | self | No | 82.2% | 23.4% |
| deepseek | self | Yes | 86.7% | 36.7% |
| llama | other | No | 79.6% | 36.9% |
| llama | other | Yes | 80.0% | 30.0% |
| llama | self | No | 80.7% | 33.3% |
| llama | self | Yes | 83.3% | 20.0% |
| mistral | other | No | 78.1% | 38.5% |
| mistral | other | Yes | 73.3% | 44.4% |
| mistral | self | No | 77.0% | 38.9% |
| mistral | self | Yes | 67.8% | 55.6% |
| qwen | other | No | 82.6% | 30.5% |
| qwen | other | Yes | 76.7% | 50.0% |
| qwen | self | No | 84.4% | 23.8% |
| qwen | self | Yes | 76.7% | 50.0% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `pilot_all_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 585 | **False Positives:** 105 | **True Negatives:** 318 | **False Negatives:** 72

![Confusion Matrix deepseek](../../../plots/pilot/all/pilot_all_confusion_matrix_deepseek.png)
### llama
**True Positives:** 589 | **False Positives:** 146 | **True Negatives:** 277 | **False Negatives:** 68

![Confusion Matrix llama](../../../plots/pilot/all/pilot_all_confusion_matrix_llama.png)
### mistral
**True Positives:** 573 | **False Positives:** 180 | **True Negatives:** 242 | **False Negatives:** 84

![Confusion Matrix mistral](../../../plots/pilot/all/pilot_all_confusion_matrix_mistral.png)
### qwen
**True Positives:** 601 | **False Positives:** 142 | **True Negatives:** 281 | **False Negatives:** 56

![Confusion Matrix qwen](../../../plots/pilot/all/pilot_all_confusion_matrix_qwen.png)
