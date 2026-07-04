---
procedure_id: BATT-ORU-003
title: Truss Battery ORU Swap
domain: space
system: Truss / Battery Orbital Replacement Unit (ORU)
summary: >-
  Remove a degraded battery ORU and install a replacement, following the bolt torque
  sequence and enforcing correct step order.
estimated_minutes: 150
required_tools: [PGT, SOCKET-1-2]
required_parts: [BATT-ORU-B4, BATT-ORU-CONN-COVER]
sensors_watched: [battery_voltage_v, battery_temp_c]
related_diagrams: [battery-oru, pgt-display, state-verification]
entry_conditions:
  - part: BATT-ORU-B4
    check: available
    qty: 1
  - part: PGT
    check: available
    qty: 1
steps:
  - id: 1
    title: Confirm replacement ORU and tools
    safety_tier: routine
    instruction: "Confirm the replacement ORU BATT-ORU-B4, PGT, and 1/2 inch socket are staged."
    preconditions:
      - part: BATT-ORU-B4
        check: available
        qty: 1
      - part: PGT
        check: available
        qty: 1
      - part: SOCKET-1-2
        check: available
        qty: 1
    verify:
      method: manual
      note: "Agent calls check_inventory for all three."
    on_failure:
      action: replan
      note: "Retrieve missing item before proceeding."

  - id: 2
    title: Safe the battery bus (must precede demate)
    safety_tier: critical
    instruction: >-
      Command the battery bus to safe and confirm voltage is below 5.0 V before touching
      any power connector. This step MUST be completed before Step 3.
    preconditions:
      - sensor: battery_voltage_v
        check: less_than
        value: 5.0
    verify:
      method: sensor
      sensor: battery_voltage_v
      check: less_than
      value: 5.0
    warnings:
      - "Demating a live power connector risks arc flash and crew injury. This is critical."
    risk_if_skipped: "Handling a hot bus is a loss-of-crew electrical hazard."
    order_enforced: true
    must_precede: 3
    on_failure:
      action: block
      note: "Bus not safed / voltage above 5 V. Do NOT proceed to connector demate."

  - id: 3
    title: Demate power connectors and cover
    safety_tier: critical
    instruction: "With the bus safed, demate the power connectors and install protective covers."
    required_parts: [BATT-ORU-CONN-COVER]
    preconditions:
      - sensor: battery_voltage_v
        check: less_than
        value: 5.0
    verify:
      method: visual
      visual_ref: battery-oru
      expect_state: "connectors demated and protective covers seated"
    depends_on_step: 2
    on_failure:
      action: block
      note: "If Step 2 (safing) not confirmed, refuse and flag out-of-order attempt."

  - id: 4
    title: Loosen primary bolts in sequence
    safety_tier: caution
    instruction: "Loosen the four primary bolts in sequence H1, H2, H3, H4."
    specs:
      torque_sequence: [BOLT-BATT-H1, BOLT-BATT-H2, BOLT-BATT-H3, BOLT-BATT-H4]
      direction: ccw
    verify:
      method: visual
      visual_ref: pgt-display
      expect_state: "each bolt backed out; sequence followed"
    risk_if_skipped: "Loosening out of sequence can bind the ORU and preload the structure unevenly."

  - id: 5
    title: Remove degraded ORU
    safety_tier: caution
    instruction: "Slide the degraded ORU out along the guide rails and temporarily stow it."
    verify:
      method: verbal
      prompt: "Say 'ORU clear' when the old unit is out and tethered."

  - id: 6
    title: Install replacement ORU
    safety_tier: caution
    instruction: "Slide BATT-ORU-B4 in along the guide rails until seated."
    required_parts: [BATT-ORU-B4]
    verify:
      method: visual
      visual_ref: battery-oru
      expect_state: "replacement ORU fully seated against the hard stops"

  - id: 7
    title: Torque primary bolts in sequence, two passes
    safety_tier: caution
    instruction: >-
      Torque the four primary bolts to spec in sequence H1 -> H2 -> H3 -> H4, two passes.
      The agent reads the exact torque and PGT setting for each bolt.
    specs:
      torque_sequence: [BOLT-BATT-H1, BOLT-BATT-H2, BOLT-BATT-H3, BOLT-BATT-H4]
      passes: 2
      direction: cw
    verify:
      method: visual
      visual_ref: pgt-display
      expect_state: "PGT shows in-spec torque for all four bolts across two passes, in order"
    warnings:
      - "Out-of-sequence torque induces preload imbalance. Follow H1 to H4."
    risk_if_skipped: "Skipping a bolt or the second pass leaves the ORU under-secured."
    on_failure:
      action: repeat
      note: "If a bolt is out of sequence or under torque, redo the sequence from H1."

  - id: 8
    title: Reconnect power and verify voltage
    safety_tier: critical
    instruction: "Remove covers, remate the power connectors, command the bus live, and confirm voltage returns to nominal."
    verify:
      method: sensor
      sensor: battery_voltage_v
      check: in_range
    warnings:
      - "Confirm connectors fully mated before commanding the bus live."
    on_failure:
      action: escalate
      note: "Voltage not nominal after remate. Safe the bus and escalate."
---

# Truss Battery ORU Swap (BATT-ORU-003)

Hands-free walkthrough for swapping a degraded truss battery ORU. Exercises the bolt
torque sequence with exact-spec lookup, electrical safety tiering, and strict step-order
enforcement (skipped / out-of-order step detection).

> Synthetic hackathon data (RAISE Summit 2026). Not real NASA flight documentation.

## Step 1 - Confirm replacement ORU and tools (routine)

The agent calls `check_inventory` for `BATT-ORU-B4`, PGT, and the 1/2 inch socket.

## Step 2 - Safe the battery bus (critical, order-enforced)

Command the bus to safe and confirm `battery_voltage_v` is below 5.0 V. This step is
marked `order_enforced` and `must_precede: 3`. If the technician tries to jump ahead to
demating connectors (Step 3) without confirming safing, the agent **refuses and flags the
out-of-order attempt** - the core skipped-step detection behavior.

## Step 3 - Demate power connectors and cover (critical)

Only reachable after Step 2 is confirmed (`depends_on_step: 2`). Demate connectors and
seat protective covers.

## Step 4 - Loosen primary bolts in sequence (caution)

Loosen H1, H2, H3, H4 in order. Out-of-sequence loosening can bind the ORU.

## Step 5 - Remove degraded ORU (caution)

Slide the old unit out on the guide rails and tether it.

## Step 6 - Install replacement ORU (caution)

Slide `BATT-ORU-B4` in until seated against the hard stops (visual check).

## Step 7 - Torque primary bolts in sequence, two passes (caution, torque sequence)

The agent looks up `get_torque_spec` for each of `BOLT-BATT-H1..H4` and enforces the
`batt_primary` sequence from `torque-specs.yaml`: H1 -> H2 -> H3 -> H4, two passes. If a
bolt is torqued out of order or under spec, the agent has the technician redo the
sequence from H1.

## Step 8 - Reconnect power and verify voltage (critical)

Remate connectors, command the bus live, and confirm `battery_voltage_v` returns to
nominal. If not, safe the bus and escalate.
