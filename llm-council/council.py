#!/usr/bin/env python3
"""
LLM Council: multi-model ensemble for research synthesis.
Routes a question to a panel of models in parallel, then synthesizes via a chairman.
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

import httpx

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

DEFAULT_PANEL = [
    "google/gemini-2.5-flash",       # breadth, speed, low cost
    "x-ai/grok-3-mini",              # recency, X/Twitter training data
    "anthropic/claude-sonnet-4-5",   # reasoning depth
]

DEFAULT_CHAIRMAN = "anthropic/claude-sonnet-4-5"

CHAIRMAN_SYSTEM = """You are a chairman synthesizing responses from a panel of AI models.
Each model brings different strengths: Gemini for breadth and factual coverage, Grok for
recency and social signals, Claude for reasoning depth.

Your job:
1. Identify where models agree, disagree, or surface unique insights
2. Weigh evidence quality and reasoning soundness
3. Produce a unified, concise answer that captures the best of all responses
4. Note significant disagreements when they affect the conclusion
5. Attribute a key insight to its source model when it adds value

Lead with the synthesis, not meta-commentary about the process."""


async def call_model(
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    question: str,
    system_prompt: Optional[str] = None,
) -> tuple[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": "LLM Council",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})

    resp = await client.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers=headers,
        json={"model": model, "messages": messages, "max_tokens": 2048, "temperature": 0.7},
        timeout=90.0,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return model, text


async def run_council(
    question: str,
    panel: list[str],
    chairman: str,
    api_key: str,
    verbose: bool = False,
) -> str:
    if verbose:
        print(f"[council] panel: {', '.join(panel)}", file=sys.stderr)
        print(f"[council] chairman: {chairman}", file=sys.stderr)

    async with httpx.AsyncClient() as client:
        tasks = [call_model(client, api_key, m, question) for m in panel]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build chairman prompt from panel results
    panel_block = ""
    for i, result in enumerate(results):
        short = panel[i].split("/")[-1]
        if isinstance(result, Exception):
            panel_block += f"\n\n### {short}\n\n*(error: {result})*"
        else:
            _, text = result
            panel_block += f"\n\n### {short}\n\n{text}"

    chairman_prompt = (
        f"Question: {question}\n\nPanel responses:{panel_block}\n\n"
        "Please synthesize these into a single, high-quality answer."
    )

    async with httpx.AsyncClient() as client:
        _, synthesis = await call_model(
            client, api_key, chairman, chairman_prompt, system_prompt=CHAIRMAN_SYSTEM
        )

    # Format output
    out = f"## Council Synthesis\n\n{synthesis}\n\n---\n\n### Panel Responses\n"
    for i, result in enumerate(results):
        short = panel[i].split("/")[-1]
        if isinstance(result, Exception):
            out += f"\n**{short}:** *(error)*\n"
        else:
            _, text = result
            out += f"\n**{short}:**\n{text}\n"

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM Council: multi-model research ensemble")
    parser.add_argument("question", nargs="?", help="Research question")
    parser.add_argument("--question", "-q", dest="q2", help="Question (alternative flag)")
    parser.add_argument("--models", "-m", help=f"Comma-separated panel models (default: {','.join(DEFAULT_PANEL)})")
    parser.add_argument("--chairman", "-c", default=DEFAULT_CHAIRMAN, help="Chairman model")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    question = args.question or args.q2 or sys.stdin.read().strip()
    if not question:
        parser.error("no question provided")

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("OPENROUTER_API_KEY not set. Get a key at https://openrouter.ai", file=sys.stderr)
        sys.exit(1)

    panel = args.models.split(",") if args.models else DEFAULT_PANEL

    print(asyncio.run(run_council(question, panel, args.chairman, api_key, args.verbose)))


if __name__ == "__main__":
    main()
