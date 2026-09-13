# Jury-vs-Grounded-Truth Probe — Code Domain

Extension to *"Neither Blinding Nor a Jury, Neither Capability Nor Strategy: What Brings a Verifier to Reliability"* (JUDGe). Companion script: `jury_probe_code.py`.

## 1. Motivation

The paper's conclusion (Sec. 4) highlights two key questions:
1. **Grounding is what fixes verification**: Showing execution/test results to a single model dramatically improves verification accuracy.
2. **Jury decorrelation**: "Training paradigms that deliberately decorrelate judges are more promising than larger panels drawn from the same distribution."

This probe tests both questions simultaneously in the code domain:
> **Can a small, deliberately complementary jury of models — with NO execution result shown — approach the accuracy of the paper's best single grounded verifier (98.0%)?**

- **If YES:** Role diversity and cross-model debate can partially substitute for missing execution grounding.
- **If NO:** It sharpens the paper's core thesis — even an elite, role-diverse jury of frontier models cannot replace an execution signal.

---

## 2. Item Pool & Benchmark to Beat

### Item Pool: DeepSeek's 150 Candidates
DeepSeek was confirmed as the paper's strongest code generator (80.0% genuine accuracy: 120 correct, 30 incorrect).
Per the paper's detectability finding (Sec. 3.2), errors from strong generators are the hardest to detect. Therefore, DeepSeek's 30 wrong candidates represent the critical test cases for the jury.

### Grounded Benchmark to Beat (Qwen + Execution Grounding)
Computed directly from the existing study records (`reports/actual/code/actual_code_results_granular.csv`):
* **Qwen / Neutral / Direct:** **98.0%** (The primary target to beat)
* **Qwen / Self / Direct:** **97.3%**
* **Qwen / Other / Direct:** **96.7%**

The jury receives **zero execution output** and must judge code purely through static reasoning and multi-agent interaction.

---

## 3. The Two Juries & Architectures

To test different multi-agent dynamics, this probe introduces two contrasting jury designs:
1. **Team A (The Coverage Jury):** A parallel multi-turn debate designed to maximize bug recall.
2. **Team B (The Precision Jury):** A multi-stage sequential pipeline designed to minimize false positives ("only flag what you can prove").

None of the models used in either team are from the paper's original 4 test models (zero overlap with Qwen2.5-72B, DeepSeek-V3, Llama-3.3-70B, or Mistral-Nemo).

---

### Team A: The Coverage Jury (Maximizing Bug Recall)

* **Architecture:** **Parallel Debate** (Round 1: all 3 models review independently and blind; Rounds 2–4: sequential discussion with leader rotation).
* **Team Philosophy:** Find as many bugs as possible, even at the cost of some false positives. Models cross-validate and critique each other's hypotheses.

| Role | Model ID | Model Name | Role Philosophy | Sourced Benchmark Evidence |
|:---|:---|:---|:---|:---|
| **The Stress-Tester** | `google/gemini-3.1-pro` | Gemini 3.1 Pro | **Reasoning-first Adversarial Scenarios:** Constructs extreme inputs (empty collections, race conditions, edge bounds) designed to break the candidate. | **77.1% on ARC-AGI-2** (measures novel logic pattern synthesis, beating previous Gemini 3 Pro at 31.1% and Claude Opus 4.6 at 68.8%); **94.3% on GPQA Diamond**. |
| **The Logic Tracer** | `anthropic/claude-opus-4-7` | Claude Opus 4.7 | **Depth-first Line-by-Line Tracing:** Walks through loops, conditionals, math operations, and "boring" execution paths (cleanup, error handling). | **87.6% on SWE-bench Verified**; **64.3% on SWE-bench Pro** (surpassing GPT-5.4 at 57.7% and Gemini 3.1 Pro at 54.2% on real GitHub issue resolution). |
| **The Rule Auditor** | `zai-org/GLM-5.1` | GLM-5.1 | **Consistency-first Requirement Checking:** Meticulously checks whether the code fulfills every explicit and implicit requirement in complex problem statements. | **58.4 on SWE-bench Pro** (top performer, designed specifically for sustained stability across hundreds of iterations without plateauing). |

---

### Team B: The Precision Jury (Minimizing False Positives)

* **Architecture:** **Sequential Pipeline** (Stage 1 $\rightarrow$ Stage 2 $\rightarrow$ Stage 3).
* **Team Philosophy:** Avoid crying wolf. "Only flag what you can prove." Each model builds upon and verifies the previous model's findings.

| Role | Model ID | Model Name | Role Philosophy | Sourced Benchmark Evidence |
|:---|:---|:---|:---|:---|
| **The Security Auditor** | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B` | Nemotron 3 Super (120B) | **Precision-first Initial Audit:** Fast and high-precision. Flags only concrete, provable defects rather than speculative doubts. | **73.4% precision on Qodo's Code Review Benchmark** (highest of any open-source model tested, outperforming models 2–3× its size). |
| **The Edge-Case Hunter** | `moonshotai/Kimi-K2.7-Code` | Kimi K2.7 Code | **Exploration-first Boundary Explorer:** Takes Nemotron's audit, explores boundary conditions, and systematically confirms or refutes findings. | **81.1% on MCP Mark Verified**; **62.0 on Kimi Code Bench v2** (+21.8% over K2.6); optimized for long-horizon agentic code exploration. |
| **The Instruction Fidelity Checker** | `stepfun-ai/Step-3.7-Flash` *(or `command-r-plus`)* | Step 3.7 Flash *(or Command R+)* | **Grounding-first Specification Drift Detector:** Catches specification drift, filters out false alarms from prior stages, and delivers the decisive final verdict. | **80.9% on GPQA Diamond**, **56.3% on SWE-bench Pro** *(or Command R+'s state-of-the-art citation and RAG grounding capabilities)*. |

---

## 4. Execution Protocols

### Team A Protocol: Parallel Multi-Turn Debate (Up to 12 messages per item)
1. **Round 1 (3 messages):** All 3 members answer in parallel, completely blind to each other.
2. **Rounds 2–4 (Up to 9 messages):** Sequential discussion. Each member sees the full transcript so far and can agree, push back, or revise their verdict.
3. **Leader Rotation:** The opening speaker for discussion rounds cycles by `item_index % 3` to prevent any single model from dominating the discussion.
4. **Early Stop:** If all 3 models reach unanimous agreement after Round 2 or 3, execution stops early to save tokens.
5. **Final Verdict:** Majority vote (2 of 3) over each member's last recorded verdict.

### Team B Protocol: Sequential Precision Pipeline (3 messages per item)
1. **Stage 1 (Nemotron 3 Super):** Runs first. Performs an initial precision-first audit.
2. **Stage 2 (Kimi K2.7 Code):** Receives the problem, code, and Stage 1 audit. Systematically stress-tests boundaries and verifies or refutes Stage 1 flags.
3. **Stage 3 (Instruction Fidelity Checker):** Receives the problem, code, and both prior audits. Checks for specification drift, filters false positives, and issues the decisive final verdict.

---

## 5. Running the Probe

### Prerequisites
All models run through **DeepInfra** using standard API keys:
```bash
export DEEPINFRA_API_KEY="your-deepinfra-key-here"

# (Optional: only if using Command R+ instead of Step 3.7 Flash)
# export COHERE_API_KEY="your-cohere-key-here"
```

### 1. Pilot Smoke Test (10 items)
Always run the pilot first to verify connectivity and parsing:
```bash
# Run 10 items for both teams
python "new probe/files (1)/jury_probe_code.py" --team both --pilot 10

# Or test a single team:
python "new probe/files (1)/jury_probe_code.py" --team team_1 --pilot 10
python "new probe/files (1)/jury_probe_code.py" --team team_2 --pilot 10
```

### 2. Full Benchmark Run (All 150 items)
Once the pilot completes cleanly, launch the full experiment:
```bash
python "new probe/files (1)/jury_probe_code.py" --team both
```

---

## 6. Output Files

* **Full Transcripts:** `reports/probes/jury_code_probe/jury_traces.jsonl`
  Contains the complete deliberation transcript, per-round verdicts, token usage, and latency for every single evaluated item.
* **Summary Results:** `reports/probes/jury_code_probe/summary.json`
  Records final jury accuracy, gap to the 98.0% grounded benchmark, unparsed counts, and average message counts per item.
