---
procedure_id: CDRA-FAULT-004
title: CDRA CO2 Scrubber Fault Response
domain: space
system: ECLSS / Carbon Dioxide Removal Assembly (CDRA)
summary: >-
  Diagnose and respond to a rising cabin CO2 fault, branching on symptoms and
  replanning if a spare bed or valve is unavailable.
estimated_minutes: 90
required_tools: [PGT, SOCKET-3-8]
required_parts: []
sensors_watched: [cabin_co2_mmHg, cabin_pressure_psia, cdra_bed_temp_c, cdra_valve_state]
related_diagrams: [cdra-schematic, state-verification]
entry_conditions:
  - sensor: cabin_co2_mmHg
    check: greater_than
    value: 3.0
steps:
  - id: 1
    title: Acknowledge rising CO2 alert
    safety_tier: caution
    instruction: >-
      Cabin CO2 is above nominal and trending up. Acknowledge the alert. The agent will
      monitor cabin_co2_mmHg continuously during this procedure.
    preconditions:
      - sensor: cabin_co2_mmHg
        check: greater_than
        value: 3.0
    verify:
      method: verbal
      prompt: "Say 'acknowledged' to begin fault isolation."
    warnings:
      - "If cabin CO2 crosses 5.3 mmHg at any point, this escalates to emergency."

  - id: 2
    title: Clarify recent changes (clarifying questions)
    safety_tier: routine
    instruction: >-
      Before touching hardware, answer a few questions so the agent does not guess:
      did crew count change, was a payload vented, or did CO2 rise on its own?
    verify:
      method: verbal
      prompt: "Answer the agent's clarifying questions about recent cabin changes."
    branches:
      - symptom: "crew count increased recently"
        action: clarify
        note: "Higher metabolic load can raise CO2 without a hardware fault; keep monitoring."
      - symptom: "no obvious cause"
        goto_step: 3

  - id: 3
    title: Read the selector valve state (diagnostic branch)
    safety_tier: caution
    instruction: "Read cdra_valve_state and branch on the result."
    verify:
      method: sensor
      sensor: cdra_valve_state
      check: not_equals
      value: fault
    branches:
      - symptom: "valve_state is fault or transition"
        goto_step: 8
      - symptom: "valve_state normal but a bed is cold during desorb"
        goto_step: 14
      - symptom: "valve_state normal and bed temps normal"
        action: clarify
        note: "Likely sensor drift or upstream cause. Re-verify CO2 sensor and reassess."

  - id: 8
    title: Selector valve reset (stuck-valve branch)
    safety_tier: caution
    instruction: >-
      Valve is stuck. Open the CDRA access panel and command a selector valve reset
      cycle. Confirm the valve reaches a nominal adsorb/desorb state.
    specs:
      torque:
        fastener_id: PNL-CDRA-Q
    verify:
      method: sensor
      sensor: cdra_valve_state
      check: not_equals
      value: fault
    on_failure:
      action: replan
      goto_step: 20
      note: "Reset failed. Check spare valve inventory and consider bypass."

  - id: 14
    title: Isolate failed desorb heater (cold-bed branch)
    safety_tier: caution
    instruction: >-
      One bed is cold during desorb, indicating a heater failure. Isolate that bed and
      run the remaining bed on a reduced-capacity single-bed cycle.
    verify:
      method: sensor
      sensor: cdra_bed_temp_c
      check: in_range
    warnings:
      - "Single-bed operation has reduced CO2 capacity; watch cabin_co2_mmHg closely."
    on_failure:
      action: escalate
      note: "If the remaining bed cannot hold CO2, escalate and prep contingency scrubbers."

  - id: 15
    title: Verify CO2 trending down
    safety_tier: caution
    instruction: "Confirm cabin CO2 is trending back toward nominal after the corrective action."
    verify:
      method: sensor
      sensor: cabin_co2_mmHg
      check: less_than
      value: 3.0
    on_failure:
      action: escalate
      note: "CO2 not recovering. Escalate and consider crew relocation to a clear module."

  - id: 20
    title: Replan - no spare bed, bypass and resupply (inventory replan)
    safety_tier: caution
    instruction: >-
      No spare sorbent bed is aboard. Replan: place CDRA in bypass on the good path,
      run reduced capacity, and queue a resupply request for CDRA-SORBENT-BED.
    required_parts: [CDRA-SORBENT-BED]
    verify:
      method: manual
      note: "Agent confirms check_inventory(CDRA-SORBENT-BED) is unavailable, then logs the replan."
    on_failure:
      action: escalate
      note: "If bypass cannot hold CO2 below limit, escalate to ground for contingency plan."

  - id: 25
    title: Emergency - CO2 crossed hard limit
    safety_tier: critical
    instruction: >-
      Cabin CO2 has crossed 5.3 mmHg. Halt diagnosis. Don a contingency scrubber / mask,
      move crew to the clearest module, and queue a priority ground alert.
    preconditions:
      - sensor: cabin_co2_mmHg
        check: greater_than
        value: 5.3
    verify:
      method: verbal
      prompt: "Say 'crew safe' once everyone is on contingency scrubbing in a clear module."
    warnings:
      - "This is an emergency. Life safety takes priority over repair."
    on_failure:
      action: emergency
      note: "Maintain contingency scrubbing; keep the ground alert queued until link returns."
---

# CDRA CO2 Scrubber Fault Response (CDRA-FAULT-004)

Hands-free walkthrough for diagnosing and responding to a rising cabin CO2 fault.
Exercises dynamic diagnostic branching, sensor-drift alerting, clarifying questions, and
inventory-driven replanning, with an emergency path if CO2 crosses the hard limit.

> Synthetic hackathon data (RAISE Summit 2026). Not real NASA flight documentation.

## Step 1 - Acknowledge rising CO2 alert (caution, live monitoring)

Entry requires `cabin_co2_mmHg` above 3.0 mmHg. The agent monitors CO2 continuously; a
crossing of 5.3 mmHg jumps straight to the emergency step (Step 25).

## Step 2 - Clarify recent changes (routine, clarifying questions)

Instead of guessing, the agent asks whether crew count changed or a payload was vented.
A recent crew increase can raise CO2 metabolically without any hardware fault - the agent
keeps monitoring rather than tearing into hardware.

## Step 3 - Read the selector valve state (caution, diagnostic branch)

The repair path forks on `cdra_valve_state`:

- **fault / transition** -> Step 8 (valve reset).
- **normal but a bed cold during desorb** -> Step 14 (heater isolation).
- **normal and bed temps normal** -> likely sensor drift; re-verify and reassess.

## Step 8 - Selector valve reset (stuck-valve branch)

Open the access panel (`get_torque_spec(PNL-CDRA-Q)`) and command a reset cycle. If the
reset fails, replan to Step 20.

## Step 14 - Isolate failed desorb heater (cold-bed branch)

Isolate the cold bed and run single-bed reduced capacity, watching CO2 closely.

## Step 15 - Verify CO2 trending down (caution)

Confirm `cabin_co2_mmHg` is recovering toward nominal. If not, escalate.

## Step 20 - Replan: no spare bed (inventory replan)

`CDRA-SORBENT-BED` has **zero** stock (see `inventory.yaml`), so bed replacement is
impossible. The agent replans to bypass on the good path, runs reduced capacity, and
queues a resupply request - a concrete "replan if part missing" outcome.

## Step 25 - Emergency: CO2 crossed hard limit (critical)

If `cabin_co2_mmHg` crosses 5.3 mmHg at any time, the walkthrough halts, the agent gives
the life-safety instruction (contingency scrubbing, move to a clear module), and queues a
priority ground alert that persists through Loss Of Signal.
