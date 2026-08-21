# Dynamic Executive Summary

**Total Verifications Processed:** 1440

## Highest Accuracy by Domain
![Accuracy Plot](../plots/pilot_math_accuracy_by_domain.png)

- **Math**: deepseek (Frame: neutral, Strategy: cot) achieved **90.0%** accuracy (**90.0% Adjusted**).

## Model Preferences by Domain (Best Configurations)
### Math
- **deepseek**: Prefers **neutral** frame & **cot** strategy (**90.0%**)
- **llama**: Prefers **neutral** frame & **cot** strategy (**87.5%**)
- **mistral**: Prefers **neutral** frame & **rubric** strategy (**90.0%**)
- **qwen**: Prefers **neutral** frame & **rubric** strategy (**90.0%**)

## Strategy Performance per Model (Raw Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 89.2% | 88.3% | 88.3% |
| **llama** | 87.5% | 85.0% | 87.5% |
| **mistral** | 85.8% | 80.8% | 85.0% |
| **qwen** | 85.8% | 85.8% | 87.5% |

## Strategy Performance per Model (Adjusted Accuracy)
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 89.2% | 88.3% | 88.3% |
| **llama** | 87.5% | 85.0% | 87.5% |
| **mistral** | 85.8% | 80.8% | 85.0% |
| **qwen** | 85.8% | 85.8% | 87.5% |

## 1. Comprehensive Accuracy Breakdown (Raw)
### Overall Average Across Everything
- **Overall**: 86.4%
### By Domain
- **Math**: 86.4%
### By Strategy
- **cot**: 87.1%
- **direct**: 85.0%
- **rubric**: 87.1%
### By Ownership Frame
- **neutral**: 87.3%
- **other**: 85.8%
- **self**: 86.0%
### By Model
- **deepseek**: 88.6%
- **llama**: 86.7%
- **mistral**: 83.9%
- **qwen**: 86.4%
### Top 3 Best Ownership + Strategy Combos
- **neutral + rubric**: 89.4%
- **neutral + cot**: 87.5%
- **other + cot**: 87.5%

## 1b. Comprehensive Accuracy Breakdown (Adjusted)
### Overall Average Across Everything
- **Overall**: 86.4%
### By Domain
- **Math**: 86.4%
### By Strategy
- **cot**: 87.1%
- **direct**: 85.0%
- **rubric**: 87.1%
### By Ownership Frame
- **neutral**: 87.3%
- **other**: 85.8%
- **self**: 86.0%
### By Model
- **deepseek**: 88.6%
- **llama**: 86.7%
- **mistral**: 83.9%
- **qwen**: 86.4%
### Top 3 Best Ownership + Strategy Combos
- **neutral + rubric**: 89.4%
- **neutral + cot**: 87.5%
- **other + cot**: 87.5%

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
- **Overall**: 174.5
### By Domain
- **Math**: 174.5
### By Strategy
- **cot**: 280.6
- **direct**: 0.0
- **rubric**: 242.9
### By Ownership Frame
- **neutral**: 172.1
- **other**: 176.5
- **self**: 174.9
### By Model
- **deepseek**: 167.7
- **llama**: 233.8
- **mistral**: 151.7
- **qwen**: 144.8
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 281.8
- **self + cot**: 281.0
- **neutral + cot**: 279.0

## 4. Dissociation Rates (Hallucinated Verdicts)
### Overall Average Across Everything
- **Overall**: 3.8%
### By Domain
- **Math**: 3.8%
### By Strategy
- **cot**: 4.0%
- **rubric**: 3.5%
### By Ownership Frame
- **neutral**: 3.8%
- **other**: 6.2%
- **self**: 1.2%
### By Model
- **deepseek**: 3.3%
- **llama**: 5.4%
- **mistral**: 2.1%
- **qwen**: 4.2%
### Top 3 Best Ownership + Strategy Combos
- **self + rubric**: 0.6%
- **self + cot**: 1.9%
- **neutral + rubric**: 3.1%

### Dissociation Deep Dive (Reasoning vs Label)
Out of 36 hallucinated verifications:
- **Label was Right / Reasoning was Wrong**: 69.4% of the time.
- **Reasoning was Right / Label was Wrong**: 30.6% of the time.

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 47.8% | Passed: 52.2% | Introduced: 0.7% | Confirmed: 99.3%
### By Domain
- **math** -> Caught: 47.8% | Passed: 52.2% | Introduced: 0.7% | Confirmed: 99.3%
### By Strategy
- **cot** -> Caught: 50.8% | Passed: 49.2% | Introduced: 0.8% | Confirmed: 99.2%
- **direct** -> Caught: 40.0% | Passed: 60.0% | Introduced: 0.0% | Confirmed: 100.0%
- **rubric** -> Caught: 52.5% | Passed: 47.5% | Introduced: 1.4% | Confirmed: 98.6%
### By Ownership Frame
- **neutral** -> Caught: 50.0% | Passed: 50.0% | Introduced: 0.3% | Confirmed: 99.7%
- **other** -> Caught: 47.5% | Passed: 52.5% | Introduced: 1.4% | Confirmed: 98.6%
- **self** -> Caught: 45.8% | Passed: 54.2% | Introduced: 0.6% | Confirmed: 99.4%
### By Model
- **deepseek** -> Caught: 60.0% | Passed: 40.0% | Introduced: 1.9% | Confirmed: 98.1%
- **llama** -> Caught: 46.7% | Passed: 53.3% | Introduced: 0.0% | Confirmed: 100.0%
- **mistral** -> Caught: 38.9% | Passed: 61.1% | Introduced: 1.1% | Confirmed: 98.9%
- **qwen** -> Caught: 45.6% | Passed: 54.4% | Introduced: 0.0% | Confirmed: 100.0%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../plots/pilot_math_fpr_self_bias.png)

- **mistral** (math, cot): **+30.0%** bias
- **mistral** (math, direct): **+10.0%** bias
- **qwen** (math, cot): **+10.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../plots/pilot_math_fnr_self_bias.png)

- **deepseek** (math, cot): **+0.0%** bias
- **deepseek** (math, direct): **+0.0%** bias
- **deepseek** (math, rubric): **+0.0%** bias

### Statistical Significance (P-Values for Bias)
*Chi-Square tests on raw False Positives/Negatives between Self and Other frames, computed PER (verifier, domain, strategy) cell - i.e. each p-value tests the exact same slice of data as the bias row above it. Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale, not a null result.*
- **mistral** (math, cot): FPR Bias p=0.3687 | FNR Bias p=1.0000
- **mistral** (math, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **qwen** (math, cot): FPR Bias p=1.0000 | FNR Bias p=1.0000

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
| deepseek | other | No | 85.6% | 45.8% |
| deepseek | other | Yes | 90.0% | 50.0% |
| deepseek | self | No | 88.9% | 33.3% |
| deepseek | self | Yes | 90.0% | 50.0% |
| llama | other | No | 82.2% | 59.3% |
| llama | other | Yes | 100.0% | 0.0% |
| llama | self | No | 82.2% | 59.3% |
| llama | self | Yes | 100.0% | 0.0% |
| mistral | other | No | 86.7% | 55.6% |
| mistral | other | Yes | 73.3% | 58.3% |
| mistral | self | No | 87.8% | 61.1% |
| mistral | self | Yes | 66.7% | 83.3% |
| qwen | other | No | 88.9% | 47.6% |
| qwen | other | Yes | 80.0% | 66.7% |
| qwen | self | No | 86.7% | 57.1% |
| qwen | self | Yes | 83.3% | 55.6% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `pilot_math_belief_vs_reality.csv`.

## 9. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 265 | **False Positives:** 36 | **True Negatives:** 54 | **False Negatives:** 5

![Confusion Matrix deepseek](../plots/pilot_math_confusion_matrix_deepseek.png)
### llama
**True Positives:** 270 | **False Positives:** 48 | **True Negatives:** 42 | **False Negatives:** 0

![Confusion Matrix llama](../plots/pilot_math_confusion_matrix_llama.png)
### mistral
**True Positives:** 267 | **False Positives:** 55 | **True Negatives:** 35 | **False Negatives:** 3

![Confusion Matrix mistral](../plots/pilot_math_confusion_matrix_mistral.png)
### qwen
**True Positives:** 270 | **False Positives:** 49 | **True Negatives:** 41 | **False Negatives:** 0

![Confusion Matrix qwen](../plots/pilot_math_confusion_matrix_qwen.png)
