# Dynamic Executive Summary

**Total Verifications Processed:** 4320

## Highest Accuracy by Domain
![Accuracy Plot](../plots/pilot_accuracy_by_domain.png)

- **Code**: deepseek (Frame: self, Strategy: direct) achieved **55.0%** accuracy.
- **Math**: llama (Frame: self, Strategy: cot) achieved **97.5%** accuracy.
- **Science**: deepseek (Frame: self, Strategy: cot) achieved **75.0%** accuracy.

## Model Preferences by Domain (Best Configurations)
### Code
- **deepseek**: Prefers **self** frame & **direct** strategy (**55.0%**)
- **llama**: Prefers **neutral** frame & **direct** strategy (**52.5%**)
- **mistral**: Prefers **other** frame & **cot** strategy (**55.0%**)
- **qwen**: Prefers **neutral** frame & **direct** strategy (**52.5%**)
### Math
- **deepseek**: Prefers **other** frame & **cot** strategy (**95.0%**)
- **llama**: Prefers **self** frame & **cot** strategy (**97.5%**)
- **mistral**: Prefers **other** frame & **rubric** strategy (**95.0%**)
- **qwen**: Prefers **neutral** frame & **rubric** strategy (**95.0%**)
### Science
- **deepseek**: Prefers **self** frame & **cot** strategy (**75.0%**)
- **llama**: Prefers **self** frame & **cot** strategy (**70.0%**)
- **mistral**: Prefers **self** frame & **rubric** strategy (**65.0%**)
- **qwen**: Prefers **other** frame & **direct** strategy (**72.5%**)

## Strategy Performance per Model
| Model | cot | direct | rubric |
|-------|---|---|---|
| **deepseek** | 70.0% | 71.1% | 70.3% |
| **llama** | 69.4% | 69.4% | 68.6% |
| **mistral** | 66.9% | 66.9% | 68.1% |
| **qwen** | 68.1% | 69.4% | 69.7% |

## 1. Comprehensive Accuracy Breakdown
### Overall Average Across Everything
- **Overall**: 69.0%
### By Domain
- **Code**: 49.9%
- **Math**: 92.4%
- **Science**: 64.8%
### By Strategy
- **cot**: 68.6%
- **direct**: 69.2%
- **rubric**: 69.2%
### By Ownership Frame
- **neutral**: 68.8%
- **other**: 69.2%
- **self**: 69.0%
### By Model
- **deepseek**: 70.5%
- **llama**: 69.2%
- **mistral**: 67.3%
- **qwen**: 69.1%
### Top 3 Best Ownership + Strategy Combos
- **other + direct**: 70.0%
- **neutral + rubric**: 69.8%
- **self + direct**: 69.2%

## 2. Formatting Failure Rates (NaN / Instructions Missed)
### Overall Average Across Everything
- **Overall**: 0.4%
### By Domain
- **Code**: 0.2%
- **Math**: 0.6%
- **Science**: 0.5%
### By Strategy
- **cot**: 1.0%
- **direct**: 0.0%
- **rubric**: 0.3%
### By Ownership Frame
- **neutral**: 0.3%
- **other**: 0.6%
- **self**: 0.3%
### By Model
- **deepseek**: 0.6%
- **llama**: 0.7%
- **mistral**: 0.3%
- **qwen**: 0.1%
### Top 3 Best Ownership + Strategy Combos
- **neutral + direct**: 0.0%
- **neutral + rubric**: 0.0%
- **self + direct**: 0.0%

## 3. Verbosity Analysis (Average Characters)
### Overall Average Across Everything
- **Overall**: 113.5
### By Domain
- **Code**: 116.8
- **Math**: 97.7
- **Science**: 126.0
### By Strategy
- **cot**: 187.0
- **direct**: 0.0
- **rubric**: 153.5
### By Ownership Frame
- **neutral**: 113.0
- **other**: 112.6
- **self**: 114.8
### By Model
- **deepseek**: 98.3
- **llama**: 127.8
- **mistral**: 121.1
- **qwen**: 106.8
### Top 3 Best Ownership + Strategy Combos
- **self + cot**: 190.9
- **other + cot**: 185.1
- **neutral + cot**: 184.9

## 4. Dissociation Rates (Hallucinated Verdicts)
### Overall Average Across Everything
- **Overall**: 1.5%
### By Domain
- **Code**: 0.2%
- **Math**: 0.2%
- **Science**: 4.1%
### By Strategy
- **cot**: 1.7%
- **rubric**: 1.2%
### By Ownership Frame
- **neutral**: 1.5%
- **other**: 1.6%
- **self**: 1.5%
### By Model
- **deepseek**: 1.1%
- **llama**: 1.5%
- **mistral**: 1.1%
- **qwen**: 2.2%
### Top 3 Best Ownership + Strategy Combos
- **self + rubric**: 1.0%
- **neutral + rubric**: 1.2%
- **other + rubric**: 1.5%

### Dissociation Deep Dive (Reasoning vs Label)
Out of 43 hallucinated verifications:
- **Label was Right / Reasoning was Wrong**: 86.0% of the time.
- **Reasoning was Right / Label was Wrong**: 14.0% of the time.

## 5. Verifier Behavior Rates
### Overall Averages
- **Overall** -> Caught: 40.3% | Passed: 59.7% | Introduced: 11.8% | Confirmed: 88.2%
### By Domain
- **code** -> Caught: 23.4% | Passed: 76.6% | Introduced: 26.2% | Confirmed: 73.8%
- **math** -> Caught: 67.5% | Passed: 32.5% | Introduced: 2.4% | Confirmed: 97.6%
- **science** -> Caught: 46.2% | Passed: 53.8% | Introduced: 12.5% | Confirmed: 87.5%
### By Strategy
- **cot** -> Caught: 39.4% | Passed: 60.6% | Introduced: 11.9% | Confirmed: 88.1%
- **direct** -> Caught: 36.5% | Passed: 63.5% | Introduced: 8.9% | Confirmed: 91.1%
- **rubric** -> Caught: 45.0% | Passed: 55.0% | Introduced: 14.7% | Confirmed: 85.3%
### By Ownership Frame
- **neutral** -> Caught: 40.1% | Passed: 59.9% | Introduced: 12.0% | Confirmed: 88.0%
- **other** -> Caught: 41.0% | Passed: 59.0% | Introduced: 11.9% | Confirmed: 88.1%
- **self** -> Caught: 39.8% | Passed: 60.2% | Introduced: 11.6% | Confirmed: 88.4%
### By Model
- **deepseek** -> Caught: 47.0% | Passed: 53.0% | Introduced: 13.9% | Confirmed: 86.1%
- **llama** -> Caught: 41.2% | Passed: 58.8% | Introduced: 12.2% | Confirmed: 87.8%
- **mistral** -> Caught: 35.0% | Passed: 65.0% | Introduced: 11.1% | Confirmed: 88.9%
- **qwen** -> Caught: 38.0% | Passed: 62.0% | Introduced: 10.2% | Confirmed: 89.8%

## 6. Statistical Bias (Self vs Other)
### Top 3 Highest Self-Preservation Biases (FPR Gap)
*These models were most likely to falsely approve their own mistakes.*
![FPR Bias Plot](../plots/pilot_fpr_self_bias.png)

- **qwen** (math, rubric): **+42.9%** bias
- **qwen** (math, direct): **+14.3%** bias
- **deepseek** (math, rubric): **+14.3%** bias

### Top 3 Highest Self-Doubt Biases (FNR Gap)
*These models were most likely to falsely reject their own correct answers.*
![FNR Bias Plot](../plots/pilot_fnr_self_bias.png)

- **deepseek** (math, cot): **+6.1%** bias
- **mistral** (science, rubric): **+5.6%** bias
- **mistral** (science, direct): **+5.6%** bias

### Statistical Significance (P-Values for Bias)
*Chi-Square tests on raw False Positives and False Negatives between Self and Other frames. (p < 0.05 is statistically significant).*
- **deepseek**: FPR Bias p=0.9060 | FNR Bias p=0.8861
- **llama**: FPR Bias p=0.8108 | FNR Bias p=0.6625
- **mistral**: FPR Bias p=1.0000 | FNR Bias p=1.0000
- **qwen**: FPR Bias p=0.5442 | FNR Bias p=1.0000

## 7. Confusion Matrices (Visuals & Raw Data)
### deepseek
**True Positives:** 558 | **False Positives:** 229 | **True Negatives:** 203 | **False Negatives:** 90

![Confusion Matrix deepseek](../plots/pilot_confusion_matrix_deepseek.png)
### llama
**True Positives:** 569 | **False Positives:** 254 | **True Negatives:** 178 | **False Negatives:** 79

![Confusion Matrix llama](../plots/pilot_confusion_matrix_llama.png)
### mistral
**True Positives:** 576 | **False Positives:** 281 | **True Negatives:** 151 | **False Negatives:** 72

![Confusion Matrix mistral](../plots/pilot_confusion_matrix_mistral.png)
### qwen
**True Positives:** 582 | **False Positives:** 268 | **True Negatives:** 164 | **False Negatives:** 66

![Confusion Matrix qwen](../plots/pilot_confusion_matrix_qwen.png)
