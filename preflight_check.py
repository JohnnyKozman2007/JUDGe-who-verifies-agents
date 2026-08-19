import argparse
import asyncio
import importlib
import json
import os
import py_compile
import sys
from collections import Counter
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    print("[FAIL] python-dotenv is missing. Install it with: pip install python-dotenv")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

FRAMES = ("self", "other", "neutral")
STRATEGIES = ("direct", "cot", "rubric")
EXPECTED_MODEL_ALIASES = {"qwen", "deepseek", "llama", "mistral"}

FAILURES = []
WARNINGS = []


def ok(msg):
    print(f"[OK] {msg}")


def warn(msg):
    WARNINGS.append(msg)
    print(f"[WARN] {msg}")


def fail(msg):
    FAILURES.append(msg)
    print(f"[FAIL] {msg}")


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                fail(f"{path} has invalid JSON on line {line_no}: {e}")
    return rows


def check_env():
    load_dotenv(REPO_ROOT / ".env")

    if (REPO_ROOT / ".env").exists():
        ok(".env file found")
    else:
        warn(".env file not found in repo root; using shell environment only")

    for key in ("HF_TOKEN", "DEEPINFRA_API_KEY"):
        if os.environ.get(key):
            ok(f"{key} is present")
        else:
            fail(f"{key} is missing")

    if not os.environ.get("HF_HUB_DISABLE_SYMLINKS_WARNING"):
        warn("HF_HUB_DISABLE_SYMLINKS_WARNING is not set; optional, but useful on Windows")


def check_required_files():
    required = [
        "run.py",
        "src/data_loader.py",
        "src/generate.py",
        "src/verify.py",
        "src/report.py",
        "src/prompts.py",
        "src/models.py",
        "src/science_utils.py",
    ]

    for rel_path in required:
        path = REPO_ROOT / rel_path
        if not path.exists():
            fail(f"Missing required file: {rel_path}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            ok(f"Compiled {rel_path}")
        except Exception as e:
            fail(f"Compile failed for {rel_path}: {e}")


def check_packages():
    packages = ["datasets", "openai", "pandas", "matplotlib", "seaborn", "scipy"]
    for package in packages:
        try:
            importlib.import_module(package)
            ok(f"Python package available: {package}")
        except Exception as e:
            fail(f"Missing/broken package {package}: {e}")


def check_repo_imports_and_prompts():
    try:
        from models import MODELS
        from prompts import get_generation_prompt, get_verification_prompt
        from science_utils import parse_science_candidate_answer

        actual_aliases = set(MODELS.keys())
        if actual_aliases != EXPECTED_MODEL_ALIASES:
            fail(f"MODELS keys are {sorted(actual_aliases)}, expected {sorted(EXPECTED_MODEL_ALIASES)}")
        else:
            ok(f"Found expected model aliases: {sorted(actual_aliases)}")

        sample_question = "What is the correct option?\nOptions:\nA. Alpha\nB. Beta\nC. Gamma\nD. Delta\n"
        gen_prompt = get_generation_prompt("science", sample_question)
        if "FINAL ANSWER" not in gen_prompt:
            fail("Science generation prompt does not enforce FINAL ANSWER format")
        else:
            ok("Science generation prompt includes FINAL ANSWER format")

        for strategy in STRATEGIES:
            prompt = get_verification_prompt("science", sample_question, "Reasoning.\nFINAL ANSWER: B", "neutral", strategy)
            if "is_correct" not in prompt or "JSON" not in prompt:
                fail(f"Science verification prompt for {strategy} does not clearly require JSON is_correct")
        ok("Science verification prompts generated for all strategies")

        parsed = parse_science_candidate_answer(
            "Reasoning here.\nFINAL ANSWER: B",
            {"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
        )
        if parsed.get("letter") != "B" or parsed.get("ambiguous"):
            fail(f"Science parser failed simple final-answer test: {parsed}")
        else:
            ok("Science parser passed simple final-answer test")

        return MODELS

    except Exception as e:
        fail(f"Repo import/prompt/parser check failed: {e}")
        return {}


def check_hf_gpqa():
    token = os.environ.get("HF_TOKEN")
    if not token:
        return

    try:
        from datasets import load_dataset

        ds = load_dataset("Idavidrein/gpqa", "gpqa_diamond", split="train", token=token)
        ok(f"Hugging Face GPQA access works; loaded {len(ds)} rows")

        if len(ds) < 150:
            fail(f"GPQA train split has only {len(ds)} rows; actual science run needs 150")

        required_cols = {
            "Question",
            "Correct Answer",
            "Incorrect Answer 1",
            "Incorrect Answer 2",
            "Incorrect Answer 3",
        }
        missing = required_cols - set(ds.column_names)
        if missing:
            fail(f"GPQA missing expected columns: {sorted(missing)}")
        else:
            ok("GPQA columns look correct")

    except Exception as e:
        fail(f"Hugging Face GPQA access failed: {e}")


def check_science_raw(mode):
    from science_utils import validate_option_map

    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    expected_count = 10 if mode == "pilot" else 150
    path = REPO_ROOT / "data" / "raw" / f"science{suffix}"

    if not path.exists():
        warn(f"{path} does not exist yet. Run data loading before the paid generation step.")
        return set()

    rows = read_jsonl(path)
    if len(rows) != expected_count:
        fail(f"{path} has {len(rows)} rows; expected {expected_count}")
    else:
        ok(f"Raw science file has expected {expected_count} rows")

    ids = [row.get("item_id") for row in rows]
    duplicate_ids = [item_id for item_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        fail(f"Duplicate science item_ids found: {duplicate_ids[:10]}")

    for row in rows:
        item_id = row.get("item_id", "<missing item_id>")
        option_map = row.get("option_map")
        if not isinstance(option_map, dict):
            fail(f"{item_id}: option_map missing or not a dict")
            continue

        issues = validate_option_map(option_map)
        if issues:
            fail(f"{item_id}: invalid option_map: {issues}")

        gt = str(row.get("ground_truth", "")).upper()
        if gt not in {"A", "B", "C", "D"}:
            fail(f"{item_id}: ground_truth is not A-D: {gt!r}")
        elif gt not in option_map:
            fail(f"{item_id}: ground_truth {gt} not present in option_map")

        if not row.get("question"):
            fail(f"{item_id}: question is empty")

    if not duplicate_ids:
        ok("Raw science rows passed structural checks")

    return set(ids)


def check_science_generated(mode, model_aliases):
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    path = REPO_ROOT / "data" / "generated" / f"science{suffix}"

    if not path.exists():
        warn(f"{path} does not exist yet. This is normal before generation.")
        return set()

    rows = read_jsonl(path)
    ids = [row.get("item_id") for row in rows]
    duplicate_ids = [item_id for item_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        fail(f"Generated science file has duplicate item_ids: {duplicate_ids[:10]}")

    incomplete = []
    for row in rows:
        candidates = row.get("candidates", {})
        missing = [alias for alias in model_aliases if not candidates.get(alias)]
        if missing:
            incomplete.append((row.get("item_id"), missing))

    if incomplete:
        fail(
            "Generated science file has rows with missing/empty candidates. "
            f"Resume will skip these item_ids. First examples: {incomplete[:5]}"
        )
    else:
        ok(f"Generated science file has {len(rows)} complete rows")

    return set(ids)


def check_science_verified(mode, model_aliases, generated_ids):
    suffix = "_pilot.jsonl" if mode == "pilot" else ".jsonl"
    path = REPO_ROOT / "data" / "verified" / f"science{suffix}"

    if not path.exists():
        warn(f"{path} does not exist yet. This is normal before verification.")
        return

    rows = read_jsonl(path)
    keys = [
        (
            row.get("item_id"),
            row.get("generator_model"),
            row.get("verifier_model"),
            row.get("frame"),
            row.get("strategy"),
        )
        for row in rows
    ]

    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    if duplicate_keys:
        fail(f"Verified science file has duplicate verification combos. First examples: {duplicate_keys[:5]}")

    stale_rows = [row.get("item_id") for row in rows if "candidate_answer_letter" not in row]
    if stale_rows:
        fail(
            "Verified science rows are missing candidate_answer_* parser fields. "
            "This means they were produced before the robust science verify.py change. "
            f"First affected item_ids: {stale_rows[:5]}"
        )

    bad_frames = [row for row in rows if row.get("frame") not in FRAMES]
    bad_strategies = [row for row in rows if row.get("strategy") not in STRATEGIES]
    if bad_frames:
        fail(f"Verified science file contains invalid frames. Count: {len(bad_frames)}")
    if bad_strategies:
        fail(f"Verified science file contains invalid strategies. Count: {len(bad_strategies)}")

    if generated_ids:
        expected = len(generated_ids) * len(model_aliases) * len(model_aliases) * len(FRAMES) * len(STRATEGIES)
        if len(keys) < expected:
            warn(f"Verified science has {len(keys)} combos; expected {expected}. Resume should continue missing combos.")
        elif len(keys) == expected:
            ok(f"Verified science has all expected {expected} combos")
        else:
            fail(f"Verified science has {len(keys)} combos, more than expected {expected}")

    ok(f"Verified science file is readable with {len(rows)} rows")


async def check_deepinfra_models(models, skip_api):
    if skip_api:
        warn("Skipping DeepInfra live API checks because --skip-api was passed")
        return

    api_key = os.environ.get("DEEPINFRA_API_KEY")
    if not api_key or not models:
        return

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai",
        )

        for alias, model_id in models.items():
            try:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": "Reply with exactly: ok"}],
                        temperature=0.0,
                        max_tokens=5,
                    ),
                    timeout=60,
                )
                text = (resp.choices[0].message.content or "").strip()
                ok(f"DeepInfra model reachable: {alias} -> {model_id}; response={text!r}")
            except Exception as e:
                fail(f"DeepInfra check failed for {alias} -> {model_id}: {e}")

    except Exception as e:
        fail(f"DeepInfra client setup failed: {e}")


def finish():
    print("\n================ Preflight Summary ================")
    print(f"Failures: {len(FAILURES)}")
    print(f"Warnings: {len(WARNINGS)}")

    if FAILURES:
        print("\nDo not start the paid run yet. Fix the failures above first.")
        sys.exit(1)

    if WARNINGS:
        print("\nPreflight passed with warnings. Read them once before launching the paid run.")
    else:
        print("\nPreflight passed cleanly. You can launch the science run.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pilot", "actual"], default="actual")
    parser.add_argument("--skip-api", action="store_true", help="Skip tiny DeepInfra live model checks")
    args = parser.parse_args()

    check_env()
    check_required_files()
    check_packages()
    models = check_repo_imports_and_prompts()
    check_hf_gpqa()

    raw_ids = check_science_raw(args.mode)
    generated_ids = check_science_generated(args.mode, models.keys() if models else EXPECTED_MODEL_ALIASES)

    if raw_ids and generated_ids:
        missing_generated = sorted(raw_ids - generated_ids)
        if missing_generated:
            warn(f"{len(missing_generated)} raw science items do not have generated candidates yet")

    check_science_verified(args.mode, models.keys() if models else EXPECTED_MODEL_ALIASES, generated_ids)

    asyncio.run(check_deepinfra_models(models, args.skip_api))
    finish()


if __name__ == "__main__":
    main()