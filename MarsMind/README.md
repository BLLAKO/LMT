# Astronaut Manual Copilot - dataset

## Files

- `manual_water_recycler.md` - fake water recycler manual with 4 sections
- `manual_oxygen_system.md` - fake oxygen system manual with 4 sections
- `scenarios.json` - 4 test queries an astronaut might ask, at different
  confidence levels, designed to show real reasoning rather than simple
  keyword lookup
- `rulebook.md` - the rules to include in every prompt sent to Gemma

## The four scenarios at a glance

| ID | Type | Correct behavior |
|----|------|-------------------|
| A  | High confidence, safety threshold applies | Give steps, but only after stating the pressure must be confirmed safe first |
| B  | Vague/ambiguous | Ask one clarifying question, do not guess |
| C  | High confidence but safety-critical | Stop, give immediate safety action, escalate to Earth, do not give repair steps |
| D  | Likely benign | Reassure, give a clear threshold for when it becomes a real problem |

This mix is deliberate. It proves the AI is doing real judgment (matching,
questioning, escalating, reassuring) rather than one-shot document lookup,
which is what the hackathon rules explicitly warn against ("a single
retrieve-then-answer call is not enough").

## How to use this tomorrow

1. Write a Python script that:
   - Loads both manual files as plain text
   - Loads `scenarios.json`
   - Loads `rulebook.md` as the system instructions
2. For each scenario, build a prompt containing:
   - the rulebook text
   - both manual files (or just the relevant one, to keep prompts shorter)
   - the astronaut's query
3. Send it to Gemma via Ollama and print the response.
4. Compare the response shape against `expected_behavior` in each scenario
   to check whether Gemma reasoned correctly (asked a question when it
   should, escalated when it should, gave steps only when safe to).
5. For scenario B (the ambiguous one), you can optionally do a second
   round: after Gemma asks its clarifying question, feed it a fake
   astronaut answer (for example, "there's a knocking sound") and show it
   then correctly resolving to Section 3.2. This second round is a strong
   demo moment since it shows genuine back-and-forth reasoning, not a
   single call.

## Demo narration tip

For each scenario, explicitly say out loud what a basic keyword-search
tool would have done wrong (see the `what_basic_rag_would_do` field in
each scenario) right before showing what your agent actually did. That
contrast is the clearest way to prove this is not "basic RAG."
