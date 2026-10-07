---
name: llm-council
description: "Multi-model LLM Council for research synthesis. Routes a research question to a panel of 3 models (Gemini Flash for breadth, Grok for recency, Claude for reasoning) in parallel, then synthesizes via a chairman model. Use in research jobs to get adversarial multi-perspective analysis instead of single-model answers."
---

# LLM Council

Multi-model ensemble for research synthesis. Based on the LLM Council concept (Karpathy / @omarsar0).
Requires an OpenRouter API key, a single endpoint that routes to 100+ models.

## Setup

```bash
export OPENROUTER_API_KEY=sk-or-...
```

Get a key at https://openrouter.ai.
Needs `httpx` available in uv: `uv add httpx` if missing.

## Usage

```bash
# Default panel (gemini-flash + grok-3-mini + claude-sonnet), claude-sonnet chairman
uv run python ~/.claude/skills/llm-council/council.py "Your research question"

# Custom panel + chairman
uv run python ~/.claude/skills/llm-council/council.py \
  --models "google/gemini-2.5-flash,x-ai/grok-3-mini,anthropic/claude-sonnet-4-5" \
  --chairman "anthropic/claude-opus-4" \
  "What are the main risks of running SQLite in production?"

# Pipe from stdin
echo "Are perpetual futures funding rates a reliable sentiment signal?" | \
  uv run python ~/.claude/skills/llm-council/council.py --verbose
```

## Default Panel

| Slot | Model | Strength | Cost (in/out per M tokens) |
|------|-------|----------|---------------------------|
| Breadth | google/gemini-2.5-flash | Factual coverage, speed | ~$0.15 / $0.60 |
| Recency | x-ai/grok-3-mini | X/Twitter training, current events | ~$0.30 / $0.50 |
| Reasoning | anthropic/claude-sonnet-4-5 | Depth, instruction following | ~$3 / $15 |
| **Chairman** | **anthropic/claude-sonnet-4-5** | **Synthesis** | ~$3 / $15 |

Typical cost per research question: **$0.05–0.15** (Sonnet chairman).
Upgrade chairman to `claude-opus-4` for ~$0.50–1.00 per question when quality matters most.

## Use in a scheduled job

```bash
TOPIC="Multi-model LLM ensembles"
uv run python ~/.claude/skills/llm-council/council.py \
  "Analyze '$TOPIC': what is it, why does it matter, and what does it mean for AI agent workflows?" \
  >> research/$(date +%F)-council.md
```

## Output Format

```
## Council Synthesis

[Chairman's synthesized, attributed answer]

---

### Panel Responses

**gemini-2.5-flash:**
[Gemini's raw response]

**grok-3-mini:**
[Grok's raw response]

**claude-sonnet-4-5:**
[Claude's raw response]
```

## Cost Control

- Use `grok-3-mini` (not `grok-3`) for cost-effective recency
- Use `gemini-2.5-flash` (not `pro`) for breadth when synthesis quality is the bottleneck
- Keep chairman as Sonnet unless the topic needs Opus-level synthesis
- For high-volume jobs (20+ topics per run), batch selectively — only run council on topics rated "high relevance"
