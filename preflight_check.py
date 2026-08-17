import os
import sys
import asyncio
from dotenv import load_dotenv


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


async def check_deepinfra():
    from openai import AsyncOpenAI

    api_key = os.environ.get("DEEPINFRA_API_KEY")
    if not api_key:
        fail("DEEPINFRA_API_KEY is missing")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepinfra.com/v1/openai",
    )

    try:
        resp = await client.chat.completions.create(
            model="mistralai/Mistral-Nemo-Instruct-2407",
            messages=[{"role": "user", "content": "Reply with exactly: ok"}],
            temperature=0.0,
            max_tokens=5,
        )
        text = (resp.choices[0].message.content or "").strip()
        ok(f"DeepInfra reachable; sample response: {text!r}")
    except Exception as e:
        fail(f"DeepInfra check failed: {e}")


def check_hf():
    token = os.environ.get("HF_TOKEN")
    if not token:
        fail("HF_TOKEN is missing")

    try:
        from datasets import load_dataset
        ds = load_dataset(
            "Idavidrein/gpqa",
            "gpqa_diamond",
            split="train[:1]",
            token=token,
        )
        ok(f"Hugging Face GPQA access works; loaded {len(ds)} row")
    except Exception as e:
        fail(f"Hugging Face GPQA access failed: {e}")


def main():
    load_dotenv()

    check_hf()
    asyncio.run(check_deepinfra())

    ok("Preflight complete. You can launch the science run.")


if __name__ == "__main__":
    main()