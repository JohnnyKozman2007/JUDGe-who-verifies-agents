# JUDGe — *Who Verifies the Verifiers?*

A research pipeline measuring **LLM verifier bias and accuracy** across three domains: code, mathematics, and PhD-level science. The pipeline asks: when LLMs are used as judges of other LLMs' outputs, how accurate are they — and do they behave differently when told the answer they are reviewing is their own?

---

## Research Questions

As AI systems become more agentic, LLMs are increasingly used to verify the correctness of other AI-generated outputs ("LLM-as-judge"). This project investigates:

1. **How accurate** are LLM verifiers across code, math, and science domains?
2. **Are they biased by authorship framing?** Do they approve their own mistakes at higher rates (self-preservation bias) or reject their own correct answers (self-doubt bias)?
3. **Does verification strategy matter?** Direct judgment vs. chain-of-thought vs. rubric-style evaluation.
4. **Does the told frame vs. actual authorship matter differently?** The *belief effect* (told "you wrote it") is disentangled from the *reality effect* (actually wrote it).

---

## Pipeline Architecture

```
run.py
 ├─ Step 1: data_loader.py        → Fetches MATH / HumanEval+ / GPQA Diamond from HuggingFace
 ├─ Step 2: generate.py           → 4 models generate candidate answers
 ├─ Step 3: verify.py             → 4 verifiers × 3 frames × 3 strategies evaluate every candidate
 ├─ Step 4: validate_overrides.py → Fuzzes code disagreements; logs missed failures
 └─ (manual) report.py            → Produces CSVs, plots, executive summary
```

**Data directories:**
- `data/raw/` — benchmark items (question, ground truth, test harness)
- `data/generated/` — candidate answers from each of the 4 models
- `data/verified/` — verifier verdicts for each of the 144 combinations per item
- `data/validated/` — fuzz results for code domain disagreements
- `reports/` — CSV reports + executive summary markdown
- `plots/` — confusion matrices and bias plots

---

## Experimental Design

### Models Evaluated (4)

| Short Name | Model ID | Size |
|---|---|---|
| `qwen` | `Qwen/Qwen2.5-72B-Instruct` | 72B |
| `deepseek` | `deepseek-ai/DeepSeek-V3` | ~671B MoE |
| `llama` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 70B |
| `mistral` | `mistralai/Mistral-Nemo-Instruct-2407` | 12B |

> ⚠️ **Known limitation:** Mistral-Nemo at 12B is substantially smaller than the others. Observed differences in verifier accuracy may reflect capacity, not purely bias.

### Ownership Frames (3)

| Frame | Prompt Says |
|---|---|
| `self` | "You wrote the following candidate answer..." |
| `other` | "Another model wrote the following candidate answer..." |
| `neutral` | "Here is a candidate answer..." |

> ℹ️ The "self" frame measures a **framing effect** — does the attribution phrase "you wrote this" change LLM judgment? LLMs have no persistent memory, so this does not test true self-recognition. It tests how authorship attribution in the prompt context influences evaluation behavior.

### Verification Strategies (3)

| Strategy | Description |
|---|---|
| `direct` | Verdict only — no visible reasoning |
| `cot` | Brief chain-of-thought (max 3–4 sentences) + verdict |
| `rubric` | Rubric-scored evaluation + verdict |

### Scale

- **Pilot mode**: 10 items per domain
- **Actual mode**: 150 items per domain
- **Verifications per item**: 4 models × 4 models × 3 frames × 3 strategies = **144 verifications**
- **Total (actual, all domains)**: 150 × 3 × 144 = **64,800 verification calls**

---

## Domains & Ground Truth

### Code (HumanEval+)
Ground truth is established by **executing** the candidate's code against an official test harness. The verifier also receives an execution result block (stdout, exit code, traceback if any) before judging, grounding it in actual runtime behavior rather than code reading — addressing the ~70–90% false-positive rate from "fluent-looking but broken" code.

### Mathematics (MATH dataset)
Ground truth is established by extracting the LaTeX `\boxed{}` answer and performing numeric/exact-string matching. The extraction uses a brace-matched parser that handles nested LaTeX correctly.

### Science (GPQA Diamond)
Ground truth is a multiple-choice letter (A–D). The candidate's answer is extracted via a 5-tier parser (strict final-answer line → explicit statement → last-line fallback → option-text match → low-confidence tail). An ambiguous parse is always graded as incorrect.

---

## Code Domain Safeguards

### Differential Fuzzing (`fuzz_validate.py`)

When the verifier overrides a clean test pass (execution passed, verifier said incorrect), the pipeline runs a **differential fuzzer**:

1. `google/gemma-2-27b-it` (external to the 4 study models) generates 15 adversarial test inputs.
2. Both the candidate code and the ground-truth reference run on each input in isolated subprocesses with a 2-second timeout.
3. If outputs differ, `microsoft/WizardLM-2-8x22B` acts as an oracle to determine which implementation was correct.

**Possible verdicts:**

| Verdict | Meaning |
|---|---|
| `BUG_CONFIRMED` | Oracle confirmed the candidate has a real bug the verifier correctly caught |
| `REFERENCE_BUG` | Oracle says the ground-truth reference is wrong (benchmark data quality issue) |
| `NO_DISCREPANCY` | All 15 inputs produced identical outputs — verifier override looks like a false alarm |
| `SKIPPED_PIPELINE_FAIL` | Input generation, execution, or oracle failed; falls back to raw test result |

### Execution Grounding (`execution_grounding.py`)
The verifier receives a real execution result block before judging — stdout, exit code, and the last traceback frame if it crashed. This converts the task from "read and guess" to "explain why this execution outcome is correct or incorrect."

---

## Metrics Reported

| Metric | Formula | Notes |
|---|---|---|
| Accuracy | `(TP + TN) / Valid_Total` | Excludes formatting failures |
| Adjusted Accuracy | Same with fuzz-adjusted ground truth | Code domain only |
| FPR | `FP / (FP + TN)` | Self-Preservation Bias when split by frame |
| FNR | `FN / (FN + TP)` | Self-Doubt Bias when split by frame |
| FPR Self-Bias | `FPR(self) − FPR(other)` | Positive = more lenient on own mistakes |
| FNR Self-Bias | `FNR(self) − FNR(other)` | Positive = harsher on own correct answers |
| Dissociation Rate | % where reasoning contradicts verdict | cot/rubric strategies only |

Statistical significance is tested via chi-square per (verifier, domain, strategy) cell.

The **Belief vs. Reality** table crosses told frame against actual authorship to disentangle whether it is *being told* "you wrote it" or *actually having written it* that drives bias.

---

## Setup & Reproduction

### Prerequisites
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

### Configuration
Copy `.env.example` to `.env`:
```
DEEPINFRA_API_KEY=your_key_here
```

### Preflight Check
```bash
python preflight_check.py
```

### Run the Pipeline
```bash
# Pilot run (10 items/domain)
python run.py --mode pilot --domain all

# Full run (150 items/domain)
python run.py --mode actual --domain all

# Single domain
python run.py --mode pilot --domain code
```

### Generate Reports (manual, after pipeline completes)
```bash
python src/report.py --mode pilot --domains all
```

---

## Known Issues & Limitations

**Critical crash bug** — `validate_overrides.py` uses the variable `overwrite` inside `process_domain()` but it is not a parameter of that function. This raises a `NameError` on any run where output files already exist. Fix: add `overwrite=False` as a parameter to `process_domain()` and thread it through from `main()`.

**`NEITHER` oracle verdict → `BUG_CONFIRMED`** — When the oracle cannot determine which implementation is correct (e.g., both crash on a malformed input), the pipeline defaults to penalizing the candidate. This is logically incorrect and inflates apparent bug rates.

**Oracle is itself an LLM** — `_ask_oracle` uses `WizardLM-2-8x22B` to adjudicate correctness disputes. Since the paper studies LLM judgment quality, relying on an unevaluated LLM to establish ground truth creates a circular dependency. Oracle verdicts are soft signals, not gold-standard ground truth.

**15 fuzzing inputs is not empirically justified** — The paper should quantify how many inputs are needed for meaningful bug-detection power on HumanEval+. `NO_DISCREPANCY` may mean "fuzzer didn't find it in 15 tries," not "there is no bug."

**Dissociation detection is asymmetric** — The detection condition is more permissive for "verdict says correct, reasoning says incorrect" than for the reverse. Results are not symmetric across verdict directions.

**Mistral-12B capacity gap** — Mistral-Nemo at 12B is 6× smaller than the other study models. Apparent accuracy and bias differences may be capacity-driven rather than behavior-driven.

**"Self" frame measures framing, not memory** — The pipeline measures whether the attribution phrase "you wrote this" changes LLM behavior, not whether the LLM recognizes its own output. The paper should be explicit about this distinction.

---

## Project Structure

```
.
├── run.py                        # Pipeline orchestrator (Steps 1–4)
├── preflight_check.py            # API and model health check
├── requirements.txt
├── .env.example                  # Template for API key configuration
│
├── src/
│   ├── data_loader.py            # HuggingFace dataset fetching
│   ├── generate.py               # Candidate answer generation
│   ├── verify.py                 # Verifier LLM calls + JSON parsing
│   ├── validate_overrides.py     # Code domain: fuzz + missed-failure logging
│   ├── fuzz_validate.py          # Differential fuzzer + LLM oracle
│   ├── execution_grounding.py    # Subprocess code execution engine
│   ├── report.py                 # Post-hoc analysis, CSV, plots, summary
│   ├── prompts.py                # All prompt templates
│   ├── science_utils.py          # GPQA answer extraction and grading
│   ├── code_utils.py             # Code fence stripping utilities
│   └── models.py                 # DeepInfra API client + model registry
│
├── data/
│   ├── raw/                      # Benchmark items (ground truth, test harnesses)
│   ├── generated/                # Candidate answers from 4 models
│   ├── verified/                 # Verifier judgments (144 per item)
│   └── validated/                # Fuzz results for code overrides
│
├── reports/                      # CSV outputs from report.py
├── plots/                        # PNG charts from report.py
└── paper/                        # Paper drafts
```

---

## Citation

*(Add citation here when paper is published.)*

## License

*(Add license here.)*
