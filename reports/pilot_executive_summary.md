# Dynamic Executive Summary

**Total Verifications Processed:** 1440

## Highest Accuracy by Domain
![Accuracy Plot](../plots/pilot_accuracy_by_domain.png)

- **Code**: mistral (Frame: neutral, Strategy: direct) achieved **100.0%** accuracy.

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **self** frame & **direct** strategy (**87.5%**)
- **llama**: Prefers **self** frame & **cot** strategy (**87.5%**)
- **mistral**: Prefers **neutral** frame & **direct** strategy (**100.0%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**95.0%**)

## Strategy Performance per Model
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 65.0% | 78.3% | 72.5% |
| **llama** | 81.7% | 75.0% | 80.8% |
| **mistral** | 73.3% | 100.0% | 72.5% |
| **qwen** | 71.7% | 90.8% | 75.0% |

## 1. Comprehensive Accuracy Breakdown
### Overall Average Across Everything
- **Overall**: 78.1%
### By Domain
- **Code**: 78.1%
### By Strategy
- **cot**: 72.9%
- **direct**: 86.0%
- **rubric**: 75.2%
### By Ownership Frame
- **neutral**: 77.7%
- **other**: 75.4%
- **self**: 81.0%
### By Model
- **deepseek**: 71.9%
- **llama**: 79.2%
- **mistral**: 81.9%
- **qwen**: 79.2%
### Top 3 Best Ownership + Strategy Combos
- **self + direct**: 89.4%
- **neutral + direct**: 85.0%
- **other + direct**: 83.8%

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
- **Overall**: 134.1
### By Domain
- **Code**: 134.1
### By Strategy
- **cot**: 219.7
- **direct**: 0.0
- **rubric**: 182.7
### By Ownership Frame
- **neutral**: 132.8
- **other**: 135.4
- **self**: 134.3
### By Model
- **deepseek**: 101.7
- **llama**: 156.6
- **mistral**: 149.3
- **qwen**: 128.9
### Top 3 Best Ownership + Strategy Combos
- **other + cot**: 222.4
- **neutral + cot**: 218.9
- **self + cot**: 217.9

## 4. Dissociation Rates (Hallucinated Verdicts)
### Overall Average Across Everything
- **Overall**: 6.0%
### By Domain
- **Code**: 6.0%
### By Strategy
- **cot**: 8.1%
- **rubric**: 4.0%
### By Ownership Frame
- **neutral**: 5.0%
- **other**: 5.9%
- **self**: 7.2%
### By Model
- **deepseek**: 7.1%
- **llama**: 6.7%
- **mistral**: 0.4%
- **qwen**: 10.0%
### Top 3 Best Ownership + Strategy Combos
- **neutral + rubric**: 3.1%
- **other + rubric**: 3.1%
- **self + rubric**: 5.6%

### Dissociation Deep Dive (Reasoning vs Label)
Out of 58 hallucinated verifications:
- **Label was Right / Reasoning was Wrong**: 0.0% of the time.
- **Reasoning was Right / Label was Wrong**: 100.0% of the time.

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 70.8% | Passed: 29.2% | Introduced: 8.5% | Confirmed: 91.5%
### By Domain
- **code** -> Caught: 70.8% | Passed: 29.2% | Introduced: 8.5% | Confirmed: 91.5%
### By Strategy
- **cot** -> Caught: 60.6% | Passed: 39.4% | Introduced: 4.2% | Confirmed: 95.8%
- **direct** -> Caught: 78.5% | Passed: 21.5% | Introduced: 0.0% | Confirmed: 100.0%
- **rubric** -> Caught: 73.4% | Passed: 26.6% | Introduced: 21.4% | Confirmed: 78.6%
### By Ownership Frame
- **neutral** -> Caught: 70.5% | Passed: 29.5% | Introduced: 8.9% | Confirmed: 91.1%
- **other** -> Caught: 67.3% | Passed: 32.7% | Introduced: 9.5% | Confirmed: 90.5%
- **self** -> Caught: 74.7% | Passed: 25.3% | Introduced: 7.1% | Confirmed: 92.9%
### By Model
- **deepseek** -> Caught: 56.8% | Passed: 43.2% | Introduced: 0.0% | Confirmed: 100.0%
- **llama** -> Caught: 69.7% | Passed: 30.3% | Introduced: 3.2% | Confirmed: 96.8%
- **mistral** -> Caught: 88.9% | Passed: 11.1% | Introduced: 31.0% | Confirmed: 69.0%
- **qwen** -> Caught: 67.9% | Passed: 32.1% | Introduced: 0.0% | Confirmed: 100.0%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../plots/pilot_fpr_self_bias.png)

- **qwen** (code, cot): **+7.7%** bias
- **qwen** (code, rubric): **+0.0%** bias
- **mistral** (code, direct): **+0.0%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../plots/pilot_fnr_self_bias.png)

- **deepseek** (code, cot): **+0.0%** bias
- **deepseek** (code, direct): **+0.0%** bias
- **deepseek** (code, rubric): **+0.0%** bias

### Statistical Significance (P-Values for Bias)
*Chi-Square tests on raw False Positives/Negatives between Self and Other frames, computed PER (verifier, domain, strategy) cell - i.e. each p-value tests the exact same slice of data as the bias row above it. Small pilot sample sizes (~20/cell) mean most will read as not significant; that's expected at this scale, not a null result.*
- **qwen** (code, cot): FPR Bias p=0.7809 | FNR Bias p=1.0000
- **qwen** (code, rubric): FPR Bias p=1.0000 | FNR Bias p=1.0000
- **mistral** (code, direct): FPR Bias p=1.0000 | FNR Bias p=1.0000

## 7. Test Suite Overrides (Code Domain)
*Instances where the code passed the test suite (ground truth correct), but the verifier LLM overrode that signal and marked it INCORRECT.*
- **Total Overrides**: 43 out of 504 passing submissions.

### By Verifier Model
- **deepseek**: 0
- **llama**: 4
- **mistral**: 39
- **qwen**: 0

## 8. Belief vs. Reality (Told Frame vs. Actual Authorship)
*Answers Primary Question 1: does TELLING a verifier 'you wrote this' change its accuracy, independent of whether that's true? Rows below cross the told frame against ground-truth authorship (actual_source).*

| Verifier | Told Frame | Actually Self-Authored? | Accuracy | FPR |
|---|---|---|---|---|
| deepseek | other | No | 74.4% | 38.3% |
| deepseek | other | Yes | 53.3% | 77.8% |
| deepseek | self | No | 82.2% | 26.7% |
| deepseek | self | Yes | 66.7% | 55.6% |
| llama | other | No | 86.7% | 22.9% |
| llama | other | Yes | 43.3% | 56.7% |
| llama | self | No | 92.2% | 12.5% |
| llama | self | Yes | 60.0% | 40.0% |
| mistral | other | No | 75.6% | 15.8% |
| mistral | other | Yes | 90.0% | 4.8% |
| mistral | self | No | 81.1% | 12.3% |
| mistral | self | Yes | 96.7% | 0.0% |
| qwen | other | No | 75.6% | 31.9% |
| qwen | other | Yes | 83.3% | 55.6% |
| qwen | self | No | 75.6% | 31.9% |
| qwen | self | Yes | 80.0% | 66.7% |

Read this as 2x2 per verifier: (told self / actually self) vs (told self / actually other) vs (told other / actually self) vs (told other / actually other). A gap between the first two rows (same actual authorship, different label) isolates the pure *belief* effect. A gap between rows 1 and 3 (same label, different truth) isolates the pure *reality* effect. Full data: `belief_vs_reality.csv`.

## 7. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 126 | **False Positives:** 101 | **True Negatives:** 133 | **False Negatives:** 0

![Confusion Matrix deepseek](../plots/pilot_confusion_matrix_deepseek.png)
### llama
**True Positives:** 122 | **False Positives:** 71 | **True Negatives:** 163 | **False Negatives:** 4

![Confusion Matrix llama](../plots/pilot_confusion_matrix_llama.png)
### mistral
**True Positives:** 87 | **False Positives:** 26 | **True Negatives:** 208 | **False Negatives:** 39

![Confusion Matrix mistral](../plots/pilot_confusion_matrix_mistral.png)
### qwen
**True Positives:** 126 | **False Positives:** 75 | **True Negatives:** 159 | **False Negatives:** 0

![Confusion Matrix qwen](../plots/pilot_confusion_matrix_qwen.png)
