# Backlog

Things consciously deferred or scoped-down to keep the core 3 modes shippable by
the deadline. Revisit **after** Quick Check → STR Reader → Methods Generator all
work end-to-end. (Broader v1 non-goals live in [PRD.md](PRD.md) §9 — this file is
for things we *started to build and cut*, not out-of-scope items.)

Each entry: **what it was · why we cut it · effort to add back.**

## Deferred features

_All previously-deferred features have been built (dark mode, loading skeletons,
byte-stable demo explanations via `DEMO_MODE` — see `services/demo_cache.py`)._

## Temporary decisions to revisit

### Groq (Llama) as LLM provider
- **What it is:** `LLM_PROVIDER=groq` fallback in `backend/services/llm_client.py`,
  used while Anthropic API key access is pending. Anthropic (`claude-sonnet-4-5`)
  is already the default.
- **Revisit:** Once the Anthropic key is available, confirm `LLM_PROVIDER=anthropic`
  and decide whether to keep Groq as an optional fallback or drop the `groq`
  dependency. **Effort: trivial (~15 min).**
