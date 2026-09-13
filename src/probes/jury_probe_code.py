"""
Jury-vs-Grounded-Truth Probe (Code Domain)
===========================================

Extends "Neither Blinding Nor a Jury..." (JUDGe) with a new research question:
Can a small, deliberately complementary jury of models — without seeing any
execution/test results — approach the accuracy of the paper's best single
grounded verifier (Qwen), which DOES see execution results?

Two Juries with Contrasting Architectures & Evidence-Based Roles:
-----------------------------------------------------------------
Team A: The Coverage Jury (Maximizing Bug Recall) — Parallel Multi-Turn Debate
    1. The Stress-Tester:         Gemini 3.1 Pro (google/gemini-3.1-pro)
       ARC-AGI-2: 77.1%, GPQA Diamond: 94.3% — reasoning-first adversarial scenario generation.
    2. The Logic Tracer:          Claude Opus 4.7 (anthropic/claude-opus-4-7)
       SWE-bench Verified: 87.6%, SWE-bench Pro: 64.3% — depth-first line-by-line tracing.
    3. The Rule Auditor:          GLM-5.1 (zai-org/GLM-5.1)
       SWE-bench Pro: 58.4 — consistency-first requirement checking over long horizons.

Team B: The Precision Jury (Minimizing False Positives) — Sequential Pipeline
    1. The Security Auditor:      Nemotron 3 Super (nvidia/NVIDIA-Nemotron-3-Super-120B-A12B)
       Qodo Code Review: 73.4% precision — precision-first ("only flag what you can prove").
    2. The Edge-Case Hunter:      Kimi K2.7 Code (moonshotai/Kimi-K2.7-Code)
       MCP Mark Verified: 81.1%, Kimi Code Bench v2: 62.0 — systematic boundary exploration.
    3. The Instruction Fidelity:  Step 3.7 Flash (stepfun-ai/Step-3.7-Flash) or Command R+
       GPQA Diamond: 80.9%, SWE-bench Pro: 56.3% — grounding-first specification drift detector.

Execution Provider:
-------------------
All models run 100% through DeepInfra using standard API keys (DEEPINFRA_API_KEY).
If COHERE_API_KEY is provided in the environment, Command R+ will be called directly via Cohere;
otherwise, it seamlessly defaults to Step 3.7 Flash on DeepInfra.

Checkpoint & Fault Tolerance:
-----------------------------
- Results are flushed to disk immediately as each item completes.
- If interrupted by WiFi errors, rate limits, or low balance, simply re-run the script.
- The script automatically detects previous progress and asks whether to Continue (Resume)
  or Overwrite, ensuring zero wasted API calls or credits.
"""

import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Ensure src/probes is on sys.path so sibling modules (generate_jury_meta_report) can always be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from openai import AsyncOpenAI

# --------------------------------------------------------------------------
# Environment & Repo Path Resolution
# --------------------------------------------------------------------------

def find_repo_root():
    """Locate the root of the JUDGe repository to load benchmark data."""
    cur = Path(__file__).resolve().parent
    for _ in range(5):
        if (cur / "data" / "raw" / "code.jsonl").exists():
            return cur
        cur = cur.parent
    cwd = Path.cwd()
    for _ in range(5):
        if (cwd / "data" / "raw" / "code.jsonl").exists():
            return cwd
        cwd = cwd.parent
    return Path.cwd()

REPO_ROOT = find_repo_root()

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv()
except ImportError:
    pass

DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

# --------------------------------------------------------------------------
# Model Registry & Juries
# --------------------------------------------------------------------------

MODEL_REGISTRY = {
    # Team A: The Coverage Jury (Parallel Multi-Turn Debate)
    "gemini_3_1_pro": {
        "name": "Gemini 3.1 Pro",
        "provider": "deepinfra",
        "model_id": "google/gemini-3.1-pro",
        "role": "The Stress-Tester (Reasoning-first Adversarial Scenarios)",
    },
    "claude_opus_4_7": {
        "name": "Claude Opus 4.7",
        "provider": "deepinfra",
        "model_id": "anthropic/claude-opus-4-7",
        "role": "The Logic Tracer (Depth-first Line-by-Line Execution)",
    },
    "glm_5_1": {
        "name": "GLM-5.1",
        "provider": "deepinfra",
        "model_id": "zai-org/GLM-5.1",
        "role": "The Rule Auditor (Consistency-first Specification Auditor)",
    },

    # Team B: The Precision Jury (Sequential Pipeline)
    "nemotron_3_super": {
        "name": "Nemotron 3 Super (120B)",
        "provider": "deepinfra",
        "model_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
        "role": "The Security Auditor (Precision-first Provable Flaws)",
    },
    "kimi_k2_7_code": {
        "name": "Kimi K2.7 Code",
        "provider": "deepinfra",
        "model_id": "moonshotai/Kimi-K2.7-Code",
        "role": "The Edge-Case Hunter (Exploration-first Boundary Explorer)",
    },
    "instruction_fidelity": {
        "name": "Step 3.7 Flash" if not COHERE_API_KEY else "Command R+",
        "provider": "cohere" if COHERE_API_KEY else "deepinfra",
        "model_id": "command-r-plus" if COHERE_API_KEY else "stepfun-ai/Step-3.7-Flash",
        "role": "The Instruction Fidelity Checker (Grounding-first Specification Drift)",
    },
}

TEAMS = {
    "team_1": ["gemini_3_1_pro", "claude_opus_4_7", "glm_5_1"],
    "team_2": ["nemotron_3_super", "kimi_k2_7_code", "instruction_fidelity"],
}

TEAM_LABELS = {
    "team_1": "Team A (The Coverage Jury: Parallel Debate)",
    "team_2": "Team B (The Precision Jury: Sequential Pipeline)",
}

# Original Paper Benchmarks (Qwen with execution grounding on DeepSeek candidates)
BENCHMARKS = {
    "qwen / neutral+direct": 98.0,
    "qwen / self+direct":    97.3,
    "qwen / other+direct":   96.7,
}

# --------------------------------------------------------------------------
# Role-Specific Prompt Templates
# --------------------------------------------------------------------------

GEMINI_3_1_PRO_PROMPT = """You are the Stress-Tester on a code review jury. Your role is REASONING-FIRST and ADVERSARIAL.
Your goal is not merely to check if the code works on standard inputs, but to actively generate adversarial scenarios and extreme boundary inputs that WOULD break this code.

Brainstorm concrete edge cases:
- Empty collections, None/null inputs, single-element structures, zero or negative numbers.
- Extremely large or boundary-scale inputs that test complexity limits.
- Unusual orderings (already sorted, reverse-sorted, all identical elements, duplicate keys).
- Race conditions, edge-state transitions, or malformed shapes not explicitly excluded by the problem.

Construct at least one SPECIFIC test input designed to break the candidate solution. State the exact input and what the code incorrectly does or returns."""

CLAUDE_OPUS_4_7_PROMPT = """You are the Logic Tracer on a code review jury. Your role is DEPTH-FIRST and SYSTEMATIC.
Your job is to walk through loops, conditionals, and mathematical operations line-by-line to verify whether the algorithm is logically sound.

Focus specifically on:
- Off-by-one errors in indexing, slicing (e.g. [:k]), and loop bounds.
- State variable mutations and whether loop invariants hold across every single branch.
- "Boring" execution paths where bugs hide: error handling, edge-branch early returns, cleanup, and type conversions.
- Mathematical precision and division/rounding behavior.

Trace the logic mechanically with a concrete example. Identify the exact line number where any logical divergence or defect occurs."""

GLM_5_1_PROMPT = """You are the Rule Auditor on a code review jury. Your role is CONSISTENCY-FIRST and METICULOUS.
Your job is to check whether the candidate solution fulfills every explicit and implicit requirement in the stated problem.

Check specifically:
- Does the code solve the exact task asked, or does it solve a superficially similar but different problem?
- Are return types, return formats (e.g. -1 vs None vs empty list), and contract requirements strictly respected?
- Are there subtle constraints or negative conditions in the prompt that the code silently ignores?
- Does the implementation maintain stability and correctness without dropping requirements on edge branches?

Audit the candidate solution against the problem specification item by item."""

NEMOTRON_3_SUPER_PROMPT = """You are the Security Auditor in a sequential code verification pipeline. Your role is PRECISION-FIRST: "Only flag what you can prove."
In this jury, precision is paramount: if you flag a defect, subsequent reviewers will treat it with high confidence. Do NOT raise speculative doubts or stylistic noise.

Analyze the candidate solution for concrete, demonstrable flaws:
- Logical defects that can be definitively shown to produce incorrect results.
- Dangerous boundary assumptions that will fail runtime execution.
- Security-relevant or invariant-breaking logic errors.

If you find a provable flaw, state it concretely with exact proof. If you cannot prove a flaw exists, state that the solution appears sound."""

KIMI_K2_7_CODE_PROMPT = """You are the Edge-Case Hunter in a sequential code verification pipeline. Your role is EXPLORATION-FIRST.
You have been provided with the problem, the candidate solution, and the initial audit from the Security Auditor.

Your job is to systematically walk execution paths and boundary conditions that static analysis might overlook:
- Review the Security Auditor's findings: does their critique hold under rigorous inspection, or is it a false alarm?
- Explore unexplored boundary conditions: extreme values, duplicate keys, empty collections, singletons.
- Deeply inspect recursion limits, memory allocations, and state mutation during loop execution.

Synthesize whether the Security Auditor's flags are valid and whether additional boundary flaws exist."""

INSTRUCTION_FIDELITY_PROMPT = """You are the Instruction Fidelity Checker serving as the decisive final judge in a sequential code verification pipeline. Your role is GROUNDING-FIRST.
Your job is to catch SPECIFICATION DRIFT and FILTER FALSE POSITIVES. You do not just ask if the code is clever; you ask if it complies with the exact problem contract.

You have been given the problem, candidate solution, and prior reviews from the Security Auditor and Edge-Case Hunter.
Verify:
- Specification compliance: Does the code adhere strictly to the problem statement? Did prior reviewers hallucinate extra requirements not in the prompt?
- Grounding: Verify that any defect flagged by prior reviewers is grounded in the actual problem specification and code, not a theoretical concern that the prompt rules out.
- Final Verdict: Weigh the evidence and provide the definitive verdict on whether the code is CORRECT or INCORRECT."""

MODEL_PROMPTS = {
    "gemini_3_1_pro": GEMINI_3_1_PRO_PROMPT,
    "claude_opus_4_7": CLAUDE_OPUS_4_7_PROMPT,
    "glm_5_1": GLM_5_1_PROMPT,
    "nemotron_3_super": NEMOTRON_3_SUPER_PROMPT,
    "kimi_k2_7_code": KIMI_K2_7_CODE_PROMPT,
    "instruction_fidelity": INSTRUCTION_FIDELITY_PROMPT,
}

SHARED_TASK_INSTRUCTIONS = """
Task: decide whether the candidate solution below is CORRECT or INCORRECT for the stated problem.
No execution result or test output is available to you — you must reason about the code directly.

[Problem]
{question}

[Candidate Solution]
{code}
"""

VERDICT_INSTRUCTIONS_ROUND1 = """
IMPORTANT INSTRUCTION:
On the VERY FIRST LINE of your response, write your verdict in EXACTLY this format:
VERDICT: CORRECT
or
VERDICT: INCORRECT

Then, on subsequent lines, provide a concise 2-4 sentence explanation justifying your verdict.
"""

VERDICT_INSTRUCTIONS_DISCUSSION = """
You will now see what your fellow reviewers said. Read their points, then respond.
IMPORTANT INSTRUCTION:
On the VERY FIRST LINE of your response, write your verdict in EXACTLY this format:
VERDICT: CORRECT
or
VERDICT: INCORRECT

Then, on subsequent lines, explain whether you agree, push back with a specific counterexample, or revise your view.
"""

VERDICT_INSTRUCTIONS_FINAL = """
This is the FINAL decisive round. You must commit to one answer.
IMPORTANT INSTRUCTION:
On the VERY FIRST LINE of your response, write your verdict in EXACTLY this format:
VERDICT: CORRECT
or
VERDICT: INCORRECT

Then, on subsequent lines, provide your final justification.
"""

VERDICT_RE = re.compile(r"VERDICT:\s*(CORRECT|INCORRECT)", re.IGNORECASE)

def parse_verdict(content: str):
    if not content:
        return None
    # 1. Look for explicit VERDICT: CORRECT / INCORRECT
    matches = VERDICT_RE.findall(content)
    if matches:
        return matches[0].upper() == "CORRECT"

    # 2. Check the first few lines for standalone verdict words
    lines = [line.strip().upper() for line in content.strip().splitlines()[:5] if line.strip()]
    for line in lines:
        if line.startswith("CORRECT") or "IS CORRECT" in line:
            return True
        if line.startswith("INCORRECT") or "IS INCORRECT" in line or line.startswith("BUG"):
            return False

    # 3. Check for markdown bold **CORRECT** / **INCORRECT**
    bold_match = re.search(r"\*\*(CORRECT|INCORRECT)\*\*", content, re.IGNORECASE)
    if bold_match:
        return bold_match.group(1).upper() == "CORRECT"

    return None

# --------------------------------------------------------------------------
# Provider Dispatch (Unified DeepInfra & Cohere API)
# --------------------------------------------------------------------------

_deepinfra_client = None

def get_deepinfra_client():
    global _deepinfra_client
    if _deepinfra_client is None:
        key = os.environ.get("DEEPINFRA_API_KEY")
        if not key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is not set. Please export DEEPINFRA_API_KEY.")
        _deepinfra_client = AsyncOpenAI(
            api_key=key,
            base_url="https://api.deepinfra.com/v1/openai"
        )
    return _deepinfra_client

async def call_deepinfra(model_id, messages, temperature=0.0, max_tokens=2000, retries=2):
    client = get_deepinfra_client()
    for attempt in range(retries + 1):
        try:
            start = time.perf_counter()
            res = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            msg = res.choices[0].message
            content = msg.content or ""
            # Handle models where output is returned in reasoning_content
            reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
            if not content and reasoning:
                content = reasoning
            elif reasoning and "VERDICT:" not in content and "VERDICT:" in reasoning:
                content = content + "\n" + reasoning

            return {
                "content": content,
                "prompt_tokens": getattr(res.usage, "prompt_tokens", None),
                "completion_tokens": getattr(res.usage, "completion_tokens", None),
                "latency": time.perf_counter() - start,
            }
        except Exception as e:
            error_str = str(e).lower()
            if "402" in error_str or "balance" in error_str or "funds" in error_str or "payment" in error_str:
                print(f"\n" + "!" * 70)
                print(f"[FATAL API ERROR] DeepInfra balance depleted (HTTP 402):")
                print(f"  {e}")
                print(f"\nAll completed progress has been safely saved to disk!")
                print(f"1. Please top up your balance at https://deepinfra.com/dash/billing")
                print(f"2. Once funded, re-run your command and choose 'Continue' to resume.")
                print("!" * 70 + "\n")
                sys.exit(1)

            if attempt == retries:
                print(f"[deepinfra:{model_id}] failed after {retries} retries: {e}")
                return None
            await asyncio.sleep(2 ** attempt)

async def call_cohere(model_id, messages, temperature=0.0, max_tokens=2000, retries=2):
    try:
        import cohere
        client = cohere.AsyncClientV2(api_key=os.environ.get("COHERE_API_KEY"))
    except ImportError:
        print("Cohere library not installed. Falling back to DeepInfra Step 3.7 Flash.")
        return await call_deepinfra("stepfun-ai/Step-3.7-Flash", messages, temperature, max_tokens, retries)

    for attempt in range(retries + 1):
        try:
            start = time.perf_counter()
            res = await client.chat(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = res.message.content[0].text if res.message and res.message.content else ""
            return {
                "content": content,
                "prompt_tokens": getattr(res.usage, "tokens", {}).get("input_tokens", None) if hasattr(res, "usage") else None,
                "completion_tokens": getattr(res.usage, "tokens", {}).get("output_tokens", None) if hasattr(res, "usage") else None,
                "latency": time.perf_counter() - start,
            }
        except Exception as e:
            if attempt == retries:
                print(f"[cohere:{model_id}] failed after {retries} retries: {e}")
                return None
            await asyncio.sleep(2 ** attempt)

async def call_model(model_key, messages, temperature=0.0, max_tokens=2000):
    cfg = MODEL_REGISTRY[model_key]
    provider, model_id = cfg["provider"], cfg["model_id"]
    if provider == "deepinfra":
        return await call_deepinfra(model_id, messages, temperature=temperature, max_tokens=max_tokens)
    elif provider == "cohere":
        return await call_cohere(model_id, messages, temperature=temperature, max_tokens=max_tokens)
    raise ValueError(f"Unknown provider for {model_key}: {provider}")

# --------------------------------------------------------------------------
# Deliberation Transcripts & Protocols
# --------------------------------------------------------------------------

def format_transcript(transcript):
    lines = []
    for turn in transcript:
        verdict_str = "CORRECT" if turn["verdict"] else ("INCORRECT" if turn["verdict"] is False else "UNPARSED")
        speaker_name = turn.get("speaker_name", turn.get("speaker_key", "Reviewer"))
        stage_label = f"round {turn['round']}" if "round" in turn else f"stage {turn['stage']}"
        lines.append(f"--- {speaker_name} ({stage_label}, verdict: {verdict_str}) ---\n{turn['content']}")
    return "\n\n".join(lines)

def build_team_a_round1_prompt(model_key, item):
    persona_text = MODEL_PROMPTS[model_key]
    task = SHARED_TASK_INSTRUCTIONS.format(question=item["question"], code=item["code"])
    return persona_text + "\n" + task + VERDICT_INSTRUCTIONS_ROUND1

def build_team_a_discussion_prompt(model_key, item, transcript, is_final):
    persona_text = MODEL_PROMPTS[model_key]
    task = SHARED_TASK_INSTRUCTIONS.format(question=item["question"], code=item["code"])
    instr = VERDICT_INSTRUCTIONS_FINAL if is_final else VERDICT_INSTRUCTIONS_DISCUSSION
    return (
        persona_text
        + "\n"
        + task
        + "\n[Deliberation So Far]\n"
        + format_transcript(transcript)
        + "\n"
        + instr
    )

async def run_parallel_debate(team_name, members, item, item_index, sem, run_tag="full", max_messages=12):
    """Team A: Parallel Debate Protocol with Leader Rotation & Early Stop."""
    async with sem:
        transcript = []
        verdicts = {}

        # Round 1: parallel, independent, blind reviews
        prompts = [build_team_a_round1_prompt(m, item) for m in members]
        results = await asyncio.gather(
            *[call_model(m, [{"role": "user", "content": p}], max_tokens=2000) for m, p in zip(members, prompts)]
        )
        for m, res in zip(members, results):
            content = res["content"] if res else ""
            v = parse_verdict(content)
            verdicts[m] = v
            transcript.append({
                "round": 1,
                "speaker_key": m,
                "speaker_name": MODEL_REGISTRY[m]["name"],
                "model_id": MODEL_REGISTRY[m]["model_id"],
                "role": MODEL_REGISTRY[m]["role"],
                "content": content,
                "verdict": v,
                "latency_seconds": round(res["latency"], 3) if res and "latency" in res else None,
                "prompt_tokens": res.get("prompt_tokens") if res else None,
                "completion_tokens": res.get("completion_tokens") if res else None,
            })

        messages_used = 3
        round_num = 2
        # Leader rotation by item_index % 3
        order = members[item_index % 3 :] + members[: item_index % 3]

        while round_num <= 4 and messages_used < max_messages:
            resolved = [v for v in verdicts.values() if v is not None]
            # Early stop if all models agree unanimously after Round 2 or 3
            if round_num > 2 and len(set(resolved)) == 1 and len(resolved) == len(members):
                break
            for m in order:
                if messages_used >= max_messages:
                    break
                is_final = (round_num == 4 or messages_used == max_messages - 1)
                prompt = build_team_a_discussion_prompt(m, item, transcript, is_final)
                res = await call_model(m, [{"role": "user", "content": prompt}], max_tokens=2000)
                content = res["content"] if res else ""
                v = parse_verdict(content)
                if v is not None:
                    verdicts[m] = v
                transcript.append({
                    "round": round_num,
                    "speaker_key": m,
                    "speaker_name": MODEL_REGISTRY[m]["name"],
                    "model_id": MODEL_REGISTRY[m]["model_id"],
                    "role": MODEL_REGISTRY[m]["role"],
                    "content": content,
                    "verdict": v,
                    "latency_seconds": round(res["latency"], 3) if res and "latency" in res else None,
                    "prompt_tokens": res.get("prompt_tokens") if res else None,
                    "completion_tokens": res.get("completion_tokens") if res else None,
                })
                messages_used += 1
            round_num += 1

        final_votes = [v for v in verdicts.values() if v is not None]
        majority = Counter(final_votes).most_common(1)[0][0] if final_votes else None

        return {
            "run_tag": run_tag,
            "item_id": item["item_id"],
            "generator": "deepseek",
            "team": team_name,
            "team_label": TEAM_LABELS[team_name],
            "architecture": "parallel_debate",
            "members": [
                {
                    "key": m,
                    "name": MODEL_REGISTRY[m]["name"],
                    "model_id": MODEL_REGISTRY[m]["model_id"],
                    "role": MODEL_REGISTRY[m]["role"]
                }
                for m in members
            ],
            "input": {
                "problem_question": item["question"],
                "candidate_code": item["code"]
            },
            "actual_ground_truth": item["actual_correct"],
            "final_verdict": majority,
            "is_correct_classification": (majority == item["actual_correct"]) if majority is not None else False,
            "messages_used": messages_used,
            "member_verdicts": verdicts,
            "transcript": transcript,
        }

async def run_sequential_pipeline(team_name, members, item, item_index, sem, run_tag="full"):
    """Team B: Precision Sequential Pipeline ('Only flag what you can prove')."""
    async with sem:
        transcript = []
        verdicts = {}
        task_text = SHARED_TASK_INSTRUCTIONS.format(question=item["question"], code=item["code"])

        # Stage 1: Security Auditor (Nemotron 3 Super)
        m1 = members[0]
        p1 = (
            MODEL_PROMPTS[m1]
            + "\n"
            + task_text
            + "\nPerform a high-precision initial audit. State only provable defects.\n"
            + VERDICT_INSTRUCTIONS_ROUND1
        )
        res1 = await call_model(m1, [{"role": "user", "content": p1}], max_tokens=2000)
        c1 = res1["content"] if res1 else ""
        v1 = parse_verdict(c1)
        verdicts[m1] = v1
        transcript.append({
            "stage": 1,
            "speaker_key": m1,
            "speaker_name": MODEL_REGISTRY[m1]["name"],
            "model_id": MODEL_REGISTRY[m1]["model_id"],
            "role": MODEL_REGISTRY[m1]["role"],
            "content": c1,
            "verdict": v1,
            "latency_seconds": round(res1["latency"], 3) if res1 and "latency" in res1 else None,
            "prompt_tokens": res1.get("prompt_tokens") if res1 else None,
            "completion_tokens": res1.get("completion_tokens") if res1 else None,
        })

        # Stage 2: Edge-Case Hunter (Kimi K2.7 Code)
        m2 = members[1]
        p2 = (
            MODEL_PROMPTS[m2]
            + "\n"
            + task_text
            + f"\n[Stage 1 Audit from {MODEL_REGISTRY[m1]['name']}]\n{c1}\n"
            + "\nSystematically explore boundary conditions. Verify or refute the Stage 1 audit.\n"
            + VERDICT_INSTRUCTIONS_ROUND1
        )
        res2 = await call_model(m2, [{"role": "user", "content": p2}], max_tokens=2000)
        c2 = res2["content"] if res2 else ""
        v2 = parse_verdict(c2)
        verdicts[m2] = v2
        transcript.append({
            "stage": 2,
            "speaker_key": m2,
            "speaker_name": MODEL_REGISTRY[m2]["name"],
            "model_id": MODEL_REGISTRY[m2]["model_id"],
            "role": MODEL_REGISTRY[m2]["role"],
            "content": c2,
            "verdict": v2,
            "latency_seconds": round(res2["latency"], 3) if res2 and "latency" in res2 else None,
            "prompt_tokens": res2.get("prompt_tokens") if res2 else None,
            "completion_tokens": res2.get("completion_tokens") if res2 else None,
        })

        # Stage 3: Instruction Fidelity Checker (Decisive Final Judge)
        m3 = members[2]
        p3 = (
            MODEL_PROMPTS[m3]
            + "\n"
            + task_text
            + f"\n[Stage 1 Audit from {MODEL_REGISTRY[m1]['name']}]\n{c1}\n"
            + f"\n[Stage 2 Audit from {MODEL_REGISTRY[m2]['name']}]\n{c2}\n"
            + "\nCheck for specification drift, filter out false alarms, and deliver the final verdict.\n"
            + VERDICT_INSTRUCTIONS_FINAL
        )
        res3 = await call_model(m3, [{"role": "user", "content": p3}], max_tokens=2000)
        c3 = res3["content"] if res3 else ""
        v3 = parse_verdict(c3)
        verdicts[m3] = v3
        transcript.append({
            "stage": 3,
            "speaker_key": m3,
            "speaker_name": MODEL_REGISTRY[m3]["name"],
            "model_id": MODEL_REGISTRY[m3]["model_id"],
            "role": MODEL_REGISTRY[m3]["role"],
            "content": c3,
            "verdict": v3,
            "latency_seconds": round(res3["latency"], 3) if res3 and "latency" in res3 else None,
            "prompt_tokens": res3.get("prompt_tokens") if res3 else None,
            "completion_tokens": res3.get("completion_tokens") if res3 else None,
        })

        final_verdict = v3
        if final_verdict is None:
            valid_votes = [v for v in [v1, v2, v3] if v is not None]
            final_verdict = Counter(valid_votes).most_common(1)[0][0] if valid_votes else None

        return {
            "run_tag": run_tag,
            "item_id": item["item_id"],
            "generator": "deepseek",
            "team": team_name,
            "team_label": TEAM_LABELS[team_name],
            "architecture": "sequential_pipeline",
            "members": [
                {
                    "key": m,
                    "name": MODEL_REGISTRY[m]["name"],
                    "model_id": MODEL_REGISTRY[m]["model_id"],
                    "role": MODEL_REGISTRY[m]["role"]
                }
                for m in members
            ],
            "input": {
                "problem_question": item["question"],
                "candidate_code": item["code"]
            },
            "actual_ground_truth": item["actual_correct"],
            "final_verdict": final_verdict,
            "is_correct_classification": (final_verdict == item["actual_correct"]) if final_verdict is not None else False,
            "messages_used": 3,
            "member_verdicts": verdicts,
            "transcript": transcript,
        }

# --------------------------------------------------------------------------
# Data Loading
# --------------------------------------------------------------------------

def load_deepseek_code_items(limit=None):
    raw_path = REPO_ROOT / "data" / "raw" / "code.jsonl"
    gen_path = REPO_ROOT / "data" / "generated" / "code.jsonl"
    rep_path = REPO_ROOT / "reports" / "actual" / "code" / "actual_code_results_granular.csv"

    if not raw_path.exists() or not gen_path.exists() or not rep_path.exists():
        raise FileNotFoundError(
            f"Required benchmark files not found under {REPO_ROOT}.\n"
            f"Expected:\n  - {raw_path}\n  - {gen_path}\n  - {rep_path}"
        )

    questions = {}
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            questions[item["item_id"]] = item["question"]

    candidates = {}
    with open(gen_path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            if "deepseek" in item.get("candidates", {}):
                candidates[item["item_id"]] = item["candidates"]["deepseek"]

    truth = {}
    with open(rep_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["generator"] == "deepseek":
                truth[row["item_id"]] = row["candidate_is_correct"] == "True"

    items = []
    for item_id, q in questions.items():
        if item_id in candidates and item_id in truth:
            items.append(
                {"item_id": item_id, "question": q, "code": candidates[item_id], "actual_correct": truth[item_id]}
            )
    items.sort(key=lambda x: x["item_id"])
    return items[:limit] if limit else items

# --------------------------------------------------------------------------
# Orchestration & Evaluation Summarizer
# --------------------------------------------------------------------------

async def run_team(team_name, items, sem, trace_paths, run_tag, existing_team_records):
    members = TEAMS[team_name]
    completed_ids = set(existing_team_records.keys())
    pending_items = [item for item in items if item["item_id"] not in completed_ids]

    if not pending_items:
        print(f"  -> All {len(items)} items already completed! Skipping API calls.")
        return list(existing_team_records.values())

    if completed_ids:
        print(f"  -> Resuming: {len(completed_ids)} already done, {len(pending_items)} remaining to evaluate.")

    if team_name == "team_1":
        tasks = [run_parallel_debate(team_name, members, item, idx, sem, run_tag=run_tag) for idx, item in enumerate(pending_items)]
    else:
        tasks = [run_sequential_pipeline(team_name, members, item, idx, sem, run_tag=run_tag) for idx, item in enumerate(pending_items)]

    new_results = []
    # Write immediately as each item completes so no progress is ever lost!
    for f in asyncio.as_completed(tasks):
        r = await f
        new_results.append(r)
        for tp in trace_paths:
            with open(tp, "a", encoding="utf-8") as file:
                file.write(json.dumps(r) + "\n")

    combined_results = list(existing_team_records.values()) + new_results
    combined_results.sort(key=lambda x: x["item_id"])
    return combined_results

def summarize(results, team_name):
    n = len(results)
    correct = sum(1 for r in results if r["final_verdict"] == r["actual_ground_truth"])
    unparsed = sum(1 for r in results if r["final_verdict"] is None)
    avg_messages = sum(r["messages_used"] for r in results) / n if n else 0
    return {
        "team": team_name,
        "team_label": TEAM_LABELS[team_name],
        "n_items": n,
        "accuracy_pct": round(100 * correct / n, 1) if n else 0.0,
        "correct_count": correct,
        "incorrect_count": n - correct - unparsed,
        "unparsed_count": unparsed,
        "avg_messages_per_item": round(avg_messages, 1),
    }

async def main():
    parser = argparse.ArgumentParser(description="Jury-vs-Grounded Benchmark Code Probe")
    parser.add_argument("--team", choices=["team_1", "team_2", "both"], default="both",
                        help="team_1 (Coverage Parallel Debate), team_2 (Precision Sequential Pipeline), or both")
    parser.add_argument("--pilot", type=int, default=None, help="Run on only N items first (smoke test)")
    parser.add_argument("--concurrency", type=int, default=5, help="Async concurrency limit")
    parser.add_argument("--resume", action="store_true", help="Resume from previous checkpoint without prompting")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite previous checkpoint without prompting")
    args = parser.parse_args()

    reports_dir = REPO_ROOT / "reports" / "probes" / "jury_code_probe"
    os.makedirs(reports_dir, exist_ok=True)

    run_tag = f"pilot_{args.pilot}" if args.pilot else "full"
    trace_path_tagged = reports_dir / f"jury_traces_{run_tag}.jsonl"
    summary_path_tagged = reports_dir / f"summary_{run_tag}.json"
    trace_path_main = reports_dir / "jury_traces.jsonl"
    summary_path_main = reports_dir / "summary.json"

    # Detect existing progress in trace file
    existing_records = {"team_1": {}, "team_2": {}}
    if trace_path_tagged.exists():
        with open(trace_path_tagged, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    t = rec.get("team")
                    iid = rec.get("item_id")
                    # Only treat as completed if it yielded a valid final verdict
                    if t in existing_records and iid and rec.get("final_verdict") is not None:
                        existing_records[t][iid] = rec
                except Exception:
                    pass

    total_existing = sum(len(v) for v in existing_records.values())
    mode = "overwrite"

    if total_existing > 0:
        if args.overwrite:
            mode = "overwrite"
        elif args.resume:
            mode = "resume"
        else:
            print("\n" + "=" * 62)
            print(f" EXISTING PROGRESS DETECTED ({trace_path_tagged.name})")
            print("=" * 62)
            for t_key in ["team_1", "team_2"]:
                print(f"  * {TEAM_LABELS[t_key]}: {len(existing_records[t_key])} items already completed")
            
            if sys.stdin and sys.stdin.isatty():
                print("\nOptions:")
                print("  [C] Continue / Resume (skip completed items, save API costs)")
                print("  [O] Overwrite (delete previous progress and restart)")
                choice = input("\nSelect [C/O] (default: C): ").strip().lower()
                mode = "overwrite" if choice == "o" else "resume"
            else:
                print("\nNon-interactive session: defaulting to Continue / Resume.")
                mode = "resume"

    if mode == "overwrite":
        print(f"\n[Reset] Starting fresh and clearing old trace files...")
        open(trace_path_tagged, "w", encoding="utf-8").close()
        open(trace_path_main, "w", encoding="utf-8").close()
        existing_records = {"team_1": {}, "team_2": {}}
    else:
        print(f"\n[Resume] Keeping completed items. Only evaluating remaining items...")
        # Sync main file with current valid tagged records
        with open(trace_path_main, "w", encoding="utf-8") as f_out:
            for t in ["team_1", "team_2"]:
                for rec in existing_records[t].values():
                    f_out.write(json.dumps(rec) + "\n")

    trace_paths = [trace_path_tagged, trace_path_main]

    items = load_deepseek_code_items(limit=args.pilot)
    print(f"\n=======================================================")
    print(f" Mode: {run_tag.upper()} ({len(items)} DeepSeek items)")
    print(f" Correct: {sum(1 for i in items if i['actual_correct'])} | Incorrect: {sum(1 for i in items if not i['actual_correct'])}")
    print(f"=======================================================\n")

    sem = asyncio.Semaphore(args.concurrency)
    teams_to_run = ["team_1", "team_2"] if args.team == "both" else [args.team]

    summaries = []
    for team_name in teams_to_run:
        print(f"\n>>> Running {TEAM_LABELS[team_name]}...")
        for m in TEAMS[team_name]:
            info = MODEL_REGISTRY[m]
            print(f"  * {info['name']} ({info['model_id']}) -> {info['role']}")

        results = await run_team(team_name, items, sem, trace_paths, run_tag, existing_records[team_name])
        summary = summarize(results, team_name)
        summaries.append(summary)

    print("\n" + "=" * 65)
    print("      JURY vs GROUNDED BENCHMARK — CODE VERIFICATION      ")
    print("=" * 65)
    print("\nBenchmark to Beat (Qwen WITH execution grounding on DeepSeek items):")
    for label, acc in BENCHMARKS.items():
        print(f"  {label:<24} {acc}%")

    print("\nJury Results (NO execution grounding shown):")
    for s in summaries:
        gap_vs_best = s["accuracy_pct"] - max(BENCHMARKS.values())
        team_lbl = "Team A (Coverage)" if s['team'] == "team_1" else "Team B (Precision)"
        print(
            f"  {team_lbl:<20} accuracy={s['accuracy_pct']}%  "
            f"(n={s['n_items']}, unparsed={s['unparsed_count']}, "
            f"avg_msgs={s['avg_messages_per_item']}, gap_to_best={gap_vs_best:+.1f}pp)"
        )

    output_payload = {
        "run_mode": run_tag,
        "benchmarks": BENCHMARKS,
        "jury_results": summaries
    }
    with open(summary_path_main, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    with open(summary_path_tagged, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    try:
        from generate_jury_meta_report import compute_team_metrics, generate_markdown_report, load_traces
        by_team_traces = load_traces(trace_path_tagged)
        meta_metrics = {}
        for t_k in ["team_1", "team_2"]:
            recs = list(by_team_traces.get(t_k, {}).values())
            m_res = compute_team_metrics(recs)
            if m_res:
                meta_metrics[t_k] = m_res
        meta_md_path = reports_dir / f"jury_meta_report_{run_tag}.md"
        meta_json_path = reports_dir / f"jury_meta_report_{run_tag}.json"
        with open(meta_json_path, "w", encoding="utf-8") as mf:
            json.dump(meta_metrics, mf, indent=2)
        generate_markdown_report(meta_metrics, by_team_traces, meta_md_path)
        generate_markdown_report(meta_metrics, by_team_traces, reports_dir / "jury_meta_report.md")
    except Exception as me:
        print(f"Notice: Could not automatically refresh meta report: {me}")

    print(f"\nSaved Granular Traces to:")
    print(f"  - {trace_path_tagged}")
    print(f"  - {trace_path_main}")
    print(f"\nSaved Summaries to:")
    print(f"  - {summary_path_tagged}")
    print(f"  - {summary_path_main}")
    print(f"\nSaved Meta Report to:")
    print(f"  - {reports_dir / 'jury_meta_report.md'}\n")

if __name__ == "__main__":
    asyncio.run(main())
