---
procedure_id: EVA-PREP-001
title: EMU Suit Checkout and Airlock Egress
domain: space
system: EMU / Quest Airlock
summary: >-
  Don and check out the EMU spacesuit, verify comms and pre-breathe, then
  depressurize the airlock and egress for a spacewalk.
estimated_minutes: 75
required_tools: [SAFETY-TETHER]
required_parts: []
sensors_watched: [suit_pressure_psia, suit_o2_pct, suit_co2_mmHg, suit_battery_pct, airlock_pressure_psia]
related_diagrams: [emu-dcm-controls, emu-suit-callouts, airlock-valves, state-verification]
entry_conditions:
  - part: SAFETY-TETHER
    check: available
    qty: 1
  - sensor: suit_battery_pct
    check: greater_than
    value: 40.0
steps:
  - id: 1
    title: Power on EMU and verify battery
    safety_tier: routine
    instruction: "Power on the EMU at the DCM. Confirm the battery state of charge is above 40 percent."
    preconditions:
      - sensor: suit_battery_pct
        check: greater_than
        value: 40.0
    verify:
      method: sensor
      sensor: suit_battery_pct
      check: greater_than
      value: 40.0
    on_failure:
      action: block
      note: "Battery below 40 percent. Swap or recharge before proceeding."
    risk_if_skipped: "EVA started on low battery can force early termination mid-task."

  - id: 2
    title: Verify comms link
    safety_tier: routine
    instruction: "Establish and confirm two-way comms. Say 'comm check' and confirm you hear the loopback tone."
    verify:
      method: verbal
      prompt: "Say 'confirm' once you have clear two-way comms."
    on_failure:
      action: block
      note: "No comms. Do not egress without a verified comm link."

  - id: 3
    title: Regulator and O2 concentration check
    safety_tier: caution
    instruction: "Open the O2 actuator. Confirm suit oxygen concentration reads in the nominal band and pressure is holding at operating pressure."
    preconditions:
      - sensor: suit_o2_pct
        check: greater_than
        value: 95.0
    specs:
      pressure: { sensor: suit_pressure_psia, nominal_psia: 4.3 }
    verify:
      method: sensor
      sensor: suit_pressure_psia
      check: in_range
    warnings:
      - "Low O2 concentration means unsafe breathing gas. Do not continue below 95 percent."
    on_failure:
      action: block
      note: "O2 out of range. Recheck regulator and actuator."

  - id: 4
    title: CO2 scrubber baseline
    safety_tier: caution
    instruction: "Confirm suit CO2 partial pressure is in the nominal band before you seal up for pre-breathe."
    preconditions:
      - sensor: suit_co2_mmHg
        check: less_than
        value: 4.0
    verify:
      method: sensor
      sensor: suit_co2_mmHg
      check: in_range
    warnings:
      - "A high CO2 baseline before egress will only get worse under workload."
    branches:
      - symptom: "suit CO2 already rising fast"
        action: escalate
        note: "Possible scrubber fault. Escalate before committing to EVA."

  - id: 5
    title: Pre-breathe protocol
    safety_tier: caution
    instruction: "Begin the pure-O2 pre-breathe. Hold for the specified duration to purge nitrogen and prevent decompression sickness."
    specs:
      duration_s: 2700
    verify:
      method: verbal
      prompt: "Say 'confirm' when the pre-breathe timer has fully elapsed."
    warnings:
      - "Skipping or shortening pre-breathe risks decompression sickness (the bends)."
    risk_if_skipped: "Insufficient pre-breathe is a serious, silent risk that only manifests after depress."
    on_failure:
      action: block
      note: "Pre-breathe incomplete. Do not depressurize the airlock."

  - id: 6
    title: Clip safety tether
    safety_tier: critical
    instruction: "Clip the safety tether to the structural hard point. Verify the hook is locked and load-tested."
    preconditions:
      - part: SAFETY-TETHER
        check: available
        qty: 1
    verify:
      method: visual
      visual_ref: emu-suit-callouts
      expect_state: "tether hook closed and locked onto the structural hard point ring"
    warnings:
      - "An unclipped or unlocked tether means no fall protection outside. This is critical."
    risk_if_skipped: "Egress without a locked tether is a loss-of-crew risk."
    on_failure:
      action: block
      note: "Tether not verified locked. Do not open the hatch."

  - id: 7
    title: Depressurize airlock below 2 psia BEFORE hatch open
    safety_tier: critical
    instruction: >-
      Depressurize the airlock. Do NOT open the hatch until pressure is confirmed
      below 2.0 psia. Read the gauge and cross-check against the live sensor.
    preconditions:
      - sensor: airlock_pressure_psia
        check: less_than
        value: 2.0
    verify:
      method: visual
      visual_ref: airlock-valves
      expect_state: "airlock gauge reads below 2 psia and the equalization valve handle is vertical (closed)"
    warnings:
      - "Opening the hatch above 2 psia risks explosive decompression. This is critical."
      - "If the gauge and the sensor disagree, trust the lower-risk assumption and stop."
    risk_if_skipped: "Hatch open above 2 psia is catastrophic."
    on_failure:
      action: emergency
      note: "Do NOT open hatch. Repressurize, recheck seal and depress valve, and re-verify."

  - id: 8
    title: Open hatch and egress
    safety_tier: critical
    instruction: "With pressure confirmed below 2 psia and tether locked, open the hatch and egress feet-first."
    preconditions:
      - sensor: airlock_pressure_psia
        check: less_than
        value: 2.0
      - sensor: suit_pressure_psia
        check: in_range
    verify:
      method: verbal
      prompt: "Say 'egress complete' once you are outside and the tether is confirmed running free."
    warnings:
      - "Re-confirm suit pressure is holding immediately after egress."
    on_failure:
      action: emergency
      note: "If suit pressure drops after egress, execute suit-leak response and ingress."
---

# EMU Suit Checkout and Airlock Egress (EVA-PREP-001)

Hands-free voice walkthrough for donning and checking out the EMU spacesuit and
egressing the Quest airlock for a spacewalk. This is the hero procedure: it exercises
procedure-state tracking, safety tiering, a live sensor-versus-assumption cross-check,
visual verification, and emergency mode.

> Synthetic hackathon data (RAISE Summit 2026). Not real NASA flight documentation.

## Before you start

Confirm a safety tether is staged and the suit battery is above 40 percent
(`entry_conditions`). If either fails, the agent will not start the walkthrough.

## Step 1 - Power on EMU and verify battery (routine)

Power on the EMU at the Display and Control Module (DCM). The agent reads
`suit_battery_pct` and confirms it is above 40 percent. Starting an EVA on a low battery
can force an early, task-interrupting return.

## Step 2 - Verify comms link (routine)

Establish two-way comms and confirm the loopback. No egress happens without a verified
comm link.

## Step 3 - Regulator and O2 concentration check (caution)

Open the O2 actuator. The agent confirms `suit_o2_pct` is above 95 percent and
`suit_pressure_psia` is holding around the 4.3 psia operating point. Below 95 percent the
breathing gas is unsafe and the step is blocked.

## Step 4 - CO2 scrubber baseline (caution)

Confirm `suit_co2_mmHg` is in the nominal band (below 4.0 mmHg) before sealing up. If CO2
is already climbing fast, the agent escalates rather than committing to the EVA - a
possible scrubber fault.

## Step 5 - Pre-breathe protocol (caution)

Breathe pure O2 for the full pre-breathe duration to purge nitrogen. Shortening this is a
**silent risk**: nothing feels wrong until after depress, when decompression sickness can
set in. The agent logs any shortfall and will not let you depressurize until the timer
fully elapses.

## Step 6 - Clip safety tether (critical)

Clip the tether to the structural hard point and verify the hook is closed and locked.
The agent asks you to show the hook (visual verification against `emu-suit-callouts`).
An unlocked tether means no fall protection outside.

## Step 7 - Depressurize airlock below 2 psia (critical, sensor cross-check)

This is the key cross-check. The manual assumption is that the airlock must be **below
2.0 psia** before the hatch opens. The agent reads `airlock_pressure_psia` live and also
asks you to read the physical gauge (`airlock-valves`). If the live sensor says pressure
is still high while you believe you can open the hatch, the agent **blocks the step and
enters emergency guidance** - opening above 2 psia risks explosive decompression. If
gauge and sensor disagree, it trusts the safer assumption and stops.

## Step 8 - Open hatch and egress (critical)

With pressure confirmed below 2 psia, tether locked, and suit pressure holding, open the
hatch and egress feet-first. Immediately after egress, the agent re-confirms suit
pressure. Any drop triggers the suit-leak emergency response (see `fault-trees.yaml`,
`suit_leak`).

## Emergency mode

At any point, a rapid `suit_pressure_psia` drop toward 3.7 psia or a CO2 spike above
7.6 mmHg halts the walkthrough, the agent speaks the safety instruction (terminate and
ingress), and queues a ground alert for when connectivity returns (handles Loss Of
Signal).
