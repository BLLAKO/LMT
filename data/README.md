# Space Ops Synthetic Data Corpus

This folder is the offline knowledge base for a **hands-free voice agent** that guides
technicians through manual work step by step. The current domain is **space / EVA
(spacewalk) and ISS maintenance**, but the schema is intentionally generalizable to
mining, offshore, and shipboard work.

Everything here is **synthetic** and authored for the RAISE Summit Hackathon 2026
(Gemma / Google DeepMind Edge & On-Device track). It is not real NASA flight
documentation and must not be used for actual operations.

## Why this is not "basic RAG"

Retrieval only decides **which procedure** applies. Execution is a **typed state
machine**: the agent runs a `plan -> act -> verify -> escalate` loop over structured
steps, and grounds every factual claim in **tool-callable reference tables** instead of
fuzzy text chunks.

```
Voice in -> intent + retrieve procedure -> load typed steps
   -> for each step: check preconditions (read_sensor / check_inventory / get_torque_spec)
   -> gate by safety_tier -> speak step -> verify (sensor | visual | verbal)
   -> log risk silently -> advance OR branch / escalate / emergency
   -> session report
```

## Folder layout

| Path | Purpose |
| --- | --- |
| `manifest.yaml` | Index of every document for retrieval (id, title, system, tags, diagrams). |
| `schema/procedure.schema.md` | The typed step front-matter schema every procedure follows. |
| `procedures/` | The step-by-step manuals (hybrid prose + YAML front-matter). |
| `reference/` | Machine-readable facts: telemetry ranges, torque specs, inventory, fault trees, glossary. |
| `diagrams/` | Generated PNG schematics (filenames match the diagram ids). The multimodal model reads these images directly. |

## How the agent consumes this

1. **Retrieve**: match the user's spoken intent against `manifest.yaml` to select a
   procedure file.
2. **Load**: parse that file's YAML front-matter into a step list.
3. **Execute**: for each step, resolve `preconditions` by calling the reference tables as
   tools (`read_sensor`, `check_inventory`, `get_torque_spec`). Sensor names, `part_id`s,
   and `fastener_id`s are a shared vocabulary that must match across files.
4. **Gate**: apply `safety_tier` (routine = normal confirm, caution = warning + confirm,
   critical = strong warning + explicit confirm).
5. **Verify**: confirm the step via `sensor`, `visual` (vision model reads the diagram
   PNG directly), or `verbal` methods before advancing.
6. **Branch / escalate**: on `on_failure`, follow the branch target, escalate, or enter
   emergency mode (halt, safety instruction, queue alert for when connectivity returns).
7. **Report**: emit a session report of completed steps, risks logged, and queued alerts.

## Shared vocabulary contract

To make cross-checks resolve deterministically, these identifiers are consistent across
the whole corpus:

- **Sensor names** (e.g. `airlock_pressure_psia`) -> defined in
  `reference/telemetry-nominal-ranges.yaml`, referenced by step `preconditions`.
- **`part_id`** (e.g. `QD-JMP-14`) -> defined in `reference/inventory.yaml`, referenced
  by step `required_parts`.
- **`fastener_id`** (e.g. `HX-M6-COOL-A`) -> defined in `reference/torque-specs.yaml`,
  referenced by step `specs.torque`.
- **Diagram ids** (e.g. `airlock-valves`) -> PNG at `diagrams/<id>.png`, referenced by
  step `verify.visual_ref` and read directly by the vision model.
