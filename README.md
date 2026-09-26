# What Actually Fixes an LLM Verifier — And Why Nothing Else Does

A research pipeline and empirical study investigating **LLM verifier reliability, belief persistence, and evaluation biases** across code, mathematics, and PhD-level science. 

When LLMs act as automated judges ("LLM-as-judge") to verify the correctness of agent outputs, they suffer from a severe **specificity collapse**: while they reliably approve correct answers (87.9% True Positive Rate), they fail to catch errors (catching only 46.1% overall, and plunging to 26.4% in math). Furthermore, verifiers exhibit an **11.9 percentage point self-preference gap** when evaluating their own mistakes. Our findings show that prompt anonymization, model scaling, and multi-agent debate juries fail to restore reliability; only **environmental execution grounding** decorrelates judge errors and restores verifier integrity (achieving a 93.3% catch rate).

---

## 📌 Paper Navigation & Project History

This repository contains materials for both the original exploratory workshop paper and the expanded full-conference submission:

### 1. New Paper (Full Conference Submission — ICLR 2027)
- **Title**: *What Actually Fixes an LLM Verifier — And Why Nothing Else Does*
- **Track**: ICLR 2027 Conference Submission (9-page main text, double-blind review).
- **Directory to read**: [`ICLR/`](ICLR/)
  - Main manuscript: [`ICLR/paper.tex`](ICLR/paper.tex)
  - Modular sections: [`ICLR/sections/`](ICLR/sections/) (`00_abstract.tex` through `07_reproducibility.tex`, and `appendix.tex`)
  - Figures and plots: [`ICLR/figures/`](ICLR/figures/)
- **Anonymous Review Repository**: [https://anonymous.4open.science/r/JUDGe-who-verifies-agents-6A34/](https://anonymous.4open.science/r/JUDGe-who-verifies-agents-6A34/)
- **Key Contributions**:
  - **Full Factorial Scale**: 64,800 verification evaluations across 4 models, 3 domains, 3 ownership frames, and 3 verification strategies.
  - **The Mechanism (Belief Persistence vs. Prompt Framing)**: Disentangled using 5 targeted diagnostic probes. Telling a model "you wrote this" shifts accuracy by $<1$\thinspace{}pp (ruling out prompt sycophancy), whereas holding the identical error constant across 6,969 matched strata (779 unique errors) reveals an **11.9\,pp self-preference gap** ($95\%$ CI $[+10.4, +13.5]$) driven by shared generative blind spots.
  - **Why Multi-Agent Juries Fail**: Ungrounded debate juries catch only 76.7% of errors despite massive compute inflation because judges share correlated reasoning errors on incorrect candidates.
  - **Execution Grounding**: Environmental feedback emerges as the only tested intervention that decisively breaks specificity collapse, achieving a 93.3% error catch rate.

### 2. Old Paper (Workshop Submission — NeurIPS 2026)
- **Title**: *Neither Blinding Nor a Jury, Neither Capability Nor Strategy: What Brings a Verifier to Reliability*
- **Workshop**: Submitted to the **NeurIPS 2026 Workshop on "Who Verifies the Agents? Toward Reliable Agent Development"** (`[dblblindworkshop]{neurips_2026}`).
- **Authors**: *Omitted for double-blind review*
- **Directory to read**: [`paper/`](paper/)
  - Workshop manuscript: [`paper/paper.tex`](paper/paper.tex)
  - Style files: [`paper/neurips_2026.sty`](paper/neurips_2026.sty)
- **Scope**: Initial exploratory analysis investigating prompt blinding, rubrics, and the limitations of multi-agent voting juries.

---

## 📂 Repository Structure & Guide to Files

```
.
├── ICLR/                         # [NEW] Full Conference Paper (ICLR 2027)
│   ├── paper.tex                 # Main LaTeX driver
│   ├── sections/                 # Paper sections (00_abstract to 07_reproducibility)
│   ├── figures/                  # Publication figures
│   └── iclr2027_conference.sty   # ICLR style template
│
├── paper/                        # [OLD] Workshop Paper (NeurIPS 2026 Workshop)
│   ├── paper.tex                 # Workshop LaTeX source
│   └── neurips_2026.sty          # NeurIPS workshop style template
│
├── src/                          # Core experimental pipeline and analysis
│   ├── stratified_estimator.py   # [CRITICAL] Reproducible stratified estimator script
│   │                             # (computes the +11.9 pp self-preference gap,
│   │                             # 6,969 strata, 779 errors, and 95% CI)
│   ├── run.py                    # Pipeline orchestrator (Steps 1–4)
│   ├── data_loader.py            # HuggingFace benchmark ingestion
│   ├── generate.py               # Candidate answer generation across 4 models
│   ├── verify.py                 # Core verifier execution (144 runs/item)
│   ├── validate_overrides.py     # Code domain fuzzing audit coordinator
│   ├── fuzz_validate.py          # Differential fuzzer + LLM oracle arbitration
│   ├── execution_grounding.py    # Subprocess execution sandbox & traceback capture
│   ├── report.py                 # Metric compilation, balanced accuracy, and CSV tables
│   ├── prompts.py                # Evaluation prompt templates
│   ├── science_utils.py          # GPQA 5-tier answer parser
│   ├── code_utils.py             # Code cleaning and execution utilities
│   ├── models.py                 # API clients and model registry
│   │
│   └── probes/                   # Diagnostic probe scripts
│       ├── analysis_self_recognition.py # Self-recognition probe analysis
│       ├── run_self_preference_probe.py # Preference probe harness
│       ├── run_style_transfer.py        # Style transfer probe harness
│       ├── jury_probe_code.py           # Multi-agent debate jury evaluation
│       ├── analysis_ensemble.py         # Scaling & ensemble voting analysis
│       └── analysis_oversight.py        # Cross-capability oversight analysis & matrix
│
├── data/                         # Experimental traces and artifacts
│   ├── raw/                      # Ingested benchmark items (HumanEval+, MATH, GPQA)
│   ├── generated/                # Candidate answers from 4 generator models
│   ├── verified/                 # 64,800 verification decision records
│   └── validated/                # Differential fuzzing results on code overrides
│
├── reports/                      # Generated CSV summary reports and tables
│   ├── all/                      # Cross-domain aggregations and stratified statistics
│   ├── code/                     # Code domain performance tables
│   ├── math/                     # Math domain performance tables
│   ├── science/                  # Science domain performance tables
│   └── probes/                   # Detailed probe reports & tables (oversight, jury, ensemble, etc.)
│
└── plots/                        # Generated figures and confusion matrices
```

---

## 🧪 Experimental Design & Setup

### Models Evaluated (4)
| Model Short Name | Identifier | Architecture | Role |
|---|---|---|---|
| `qwen` | `Qwen/Qwen2.5-72B-Instruct` | 72B Dense | Generator & Verifier |
| `deepseek` | `deepseek-ai/DeepSeek-V3` | 671B MoE | Generator & Verifier |
| `llama` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 70B Dense | Generator & Verifier |
| `mistral` | `mistralai/Mistral-Nemo-Instruct-2407` | 12B Dense | Generator & Verifier |

### Factorial Evaluation Matrix
- **3 Domains**: Code ([HumanEval+](https://github.com/evalplus/evalplus)), Mathematics ([MATH](https://github.com/hendrycks/math)), Science ([GPQA Diamond](https://github.com/idavidrein/gpqa)).
- **Scale**: 150 items per domain $\times$ 4 generators $\times$ 4 verifiers $\times$ 3 frames $\times$ 3 strategies = **64,800 verification calls**.
- **3 Ownership Frames**:
  - `self`: *"You wrote the following candidate answer..."*
  - `other`: *"Another model wrote the following candidate answer..."*
  - `neutral`: *"Here is a candidate answer..."*
- **3 Verification Strategies**:
  - `direct`: Verdict only.
  - `cot`: Chain-of-thought rationale + verdict.
  - `rubric`: Rubric criteria scoring + verdict.

---

## 🚀 Reproduction & Execution

### 1. Environment Setup
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
# Edit .env with your DEEPINFRA_API_KEY
```

### 3. Verify System Health
```bash
python preflight_check.py
```

### 4. Running the Stratified Self-Preference Estimator
To reproduce the paper's headline $+11.9$\,pp self-preference gap, 6,969 strata, 779 unique errors, and 95% confidence interval:
```bash
python src/stratified_estimator.py
```

### 5. Running the Pipeline
```bash
# Pilot run (10 items/domain)
python run.py --mode pilot --domain all

# Full run (150 items/domain, 64,800 evaluations)
python run.py --mode actual --domain all

# Generate all CSV reports and summary statistics
python src/report.py --mode actual --domains all
```

---

## 🔍 Methodological Scope & Clarifications

1. **Stratified Error Matching**: Self-preference is computed by holding the exact erroneous text constant across 6,969 matched evaluator strata spanning 779 distinct error outputs, isolating generator identity from item difficulty and text variance.
2. **Differential Fuzzing Audit**: In the code domain, overrides of passing test harnesses are audited using differential fuzzing (`fuzz_validate.py`) with 15 adversarial inputs generated by `gemma-2-27b-it`. For disagreements, `WizardLM-2-8x22B` serves as an oracle. When the oracle returns `NEITHER` (cannot resolve ambiguity), the system falls back to test-harness truth (`SKIPPED_PIPELINE_FAIL`) without penalizing the candidate.
3. **Execution Grounding**: Code verifiers receive real runtime execution traces (stdout, exit codes, tracebacks), transforming evaluation from speculative reading to behavioral verification.
4. **Capacity Controls**: Analysis accounts for model parameter scaling, noting that Mistral-12B behaves primarily as an uncritical rubber-stamp compared to frontier 70B/671B models.

---

## 📄 Citation

*(Citation will be added upon acceptance / publication.)*
