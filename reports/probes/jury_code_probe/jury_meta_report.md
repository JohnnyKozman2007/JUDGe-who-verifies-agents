# JUDGe Extension: Jury-vs-Grounded Benchmark Meta-Report

## Executive Summary

This probe investigates whether a **multi-model deliberative jury**—operating without code execution or test output—can match or exceed the paper's best execution-grounded verifier (**Qwen 2.5 72B with test execution: 98.0%**).

### Baseline Grounded Benchmarks (from JUDGe Paper)
| Verifier / Setting | Execution Grounding | Accuracy |
|---|:---:|:---:|
| `qwen / neutral+direct` | **YES** (full test execution shown) | **98.0%** |
| `qwen / self+direct` | **YES** (full test execution shown) | **97.3%** |
| `qwen / other+direct` | **YES** (full test execution shown) | **96.7%** |

### Jury Architectures Evaluated (Zero Execution Grounding)
| Metric | Team A: Parallel Debate (Zero Grounding) | Team B: Sequential Pipeline (Zero Grounding) | Grounded Baseline: Qwen 72B (Direct + Execution, n=150) |
|---|:---:|:---:|:---:|
| **Evaluated Items (n)** | 150 / 150 | 150 / 150 | 150 |
| **Raw Accuracy** | **92.67%** | **88.67%** | **98.00%** |
| **Gap to Grounded (Raw Acc)** | **-5.33pp** | **-9.33pp** | Baseline |
| **Balanced Accuracy (Primary)** | **86.67%** | **81.67%** | **96.25%** |
| **Gap to Grounded (Bal Acc)** | **-9.58pp** | **-14.58pp** | Baseline |
| **Precision (Detecting Correct)** | 94.31% | 92.56% | 98.35% |
| **Confirm Rate / Recall (TPR)** | 96.67% | 93.33% | 99.17% |
| **Catch Rate / Specificity (TNR)** | 76.67% | 70.0% | 93.33% |
| **False Rejection Rate / FNR** | 3.33% | 6.67% | 0.83% |
| **False Approval Rate / FPR** | 23.33% | 30.0% | 6.67% |
| **F1 Score** | 0.9547 | 0.9295 | 0.9876 |
| **Avg Tokens per Problem** | 21,039 | 5,438 | 653 |
| **Total Compute Cost (150 items)** | **$13.71** | **$0.84** | ~$0.03 |
| **Avg Cost per Problem** | **$0.0914** | **$0.0056** | ~$0.0002 |

## Detailed Error Analysis & Architecture Dynamics

### 1. The Overthinking Trap in Parallel Debate (Team A)
In multi-turn unconstrained debate, frontier models frequently enter **adversarial infection**: when one reviewer hypothesizes an extreme theoretical constraint (e.g. IEEE-754 floating-point overflow for numbers exceeding $10^{18}$), other models often abandon correct solutions to agree with the critic. This creates a non-zero False Negative Rate on valid benchmark code.

### 2. The Grounding Gatekeeper in Sequential Pipeline (Team B)
Team B avoids debate spirals by enforcing a structured 3-stage chain:
1. **Nemotron 3 Super (120B)** establishes strict provable correctness.
2. **Kimi K2.7 Code** searches boundaries and proposes potential edge-case failures.
3. **Step 3.7 Flash** acts as an impartial **Instruction Fidelity Arbiter**, auditing Kimi's objections against the exact prompt specification before rendering the verdict. This decisively filters out pedantic false positives.

### Head-to-Head Disagreements on Common Problems
| Item ID | Actual Ground Truth | Team A Verdict | Team B Verdict | Winner |
|---|:---:|:---:|:---:|:---:|
| `code_HumanEval_11` | **True** | INCORRECT | CORRECT | **Team B** |
| `code_HumanEval_125` | **True** | INCORRECT | CORRECT | **Team B** |
| `code_HumanEval_127` | **False** | INCORRECT | CORRECT | **Team A** |
| `code_HumanEval_134` | **True** | CORRECT | INCORRECT | **Team A** |
| `code_HumanEval_145` | **False** | INCORRECT | CORRECT | **Team A** |
| `code_HumanEval_150` | **True** | CORRECT | INCORRECT | **Team A** |
| `code_HumanEval_21` | **True** | CORRECT | INCORRECT | **Team A** |
| `code_HumanEval_66` | **True** | CORRECT | INCORRECT | **Team A** |
| `code_HumanEval_79` | **True** | CORRECT | INCORRECT | **Team A** |
| `code_HumanEval_93` | **False** | INCORRECT | CORRECT | **Team A** |
| `code_HumanEval_94` | **False** | CORRECT | INCORRECT | **Team B** |
| `code_HumanEval_99` | **True** | CORRECT | INCORRECT | **Team A** |
