---
procedure_id: COOL-JMP-002
title: External Ammonia Coolant Jumper Remove & Replace
domain: space
system: External Active Thermal Control (ETCS) / QD jumper
summary: >-
  Remove and replace a leaking ammonia quick-disconnect (QD) coolant jumper on the
  truss, using torque specs and verifying no ammonia release.
estimated_minutes: 120
required_tools: [PGT, SOCKET-7-16, QD-COLLAR-TOOL, AMMONIA-DECON-BRUSH]
required_parts: [QD-JMP-14, QD-JMP-14-CAP]
sensors_watched: [coolant_loop_pressure_psia, coolant_loop_temp_c, suit_co2_mmHg]
related_diagrams: [coolant-jumper-qd, pgt-display, state-verification]
entry_conditions:
  - part: QD-JMP-14
    check: available
    qty: 1
  - part: PGT
    check: available
    qty: 1
steps:
  - id: 1
    title: Confirm tool kit staged
    safety_tier: routine
    instruction: "Confirm the PGT, 7/16 socket, and QD collar tool are in your caddy."
    preconditions:
      - part: PGT
        check: available
        qty: 1
      - part: SOCKET-7-16
        check: available
        qty: 1
      - part: QD-COLLAR-TOOL
        check: available
        qty: 1
    verify:
      method: verbal
      prompt: "Say 'confirm' when all three tools are in the caddy."
    on_failure:
      action: replan
      note: "Missing a tool. Retrieve from QUEST-A2 before proceeding."

  - id: 2
    title: Confirm replacement jumper and cap available
    safety_tier: routine
    instruction: "Confirm the replacement jumper QD-JMP-14 and its cap set are staged."
    preconditions:
      - part: QD-JMP-14
        check: available
        qty: 1
      - part: QD-JMP-14-CAP
        check: available
        qty: 1
    verify:
      method: manual
      note: "Agent calls check_inventory for both parts."
    on_failure:
      action: replan
      note: >-
        QD-JMP-14-CAP is out of stock. Replan: substitute contingency cap CAP-GENERIC-2
        (approved) and continue, or escalate if no cap is available.
    branches:
      - symptom: "cap QD-JMP-14-CAP unavailable but CAP-GENERIC-2 available"
        action: replan
        note: "Use CAP-GENERIC-2 as approved substitute; log the substitution."
      - symptom: "no cap of any kind available"
        action: escalate
        note: "Do not leave an uncapped ammonia line. Escalate to ground."

  - id: 3
    title: Inspect the leak and classify
    safety_tier: caution
    instruction: "Inspect the leaking QD. Describe what you see so the repair path can be set."
    verify:
      method: visual
      visual_ref: coolant-jumper-qd
      expect_state: "identify QD-JMP-14 locking collar and alignment stripe"
    branches:
      - symptom: "white frost only, no flakes"
        goto_step: 5
      - symptom: "white flakes or snow (ammonia crystals)"
        action: emergency
        note: "Active ammonia release. Execute decon; do not ingress contaminated. Queue ground alert."
      - symptom: "no visible frost but pressure still dropping"
        action: escalate
        note: "Leak is not at the QD. Halt R&R and escalate for loop isolation."

  - id: 4
    title: Vent loop below 5 psia before demate
    safety_tier: critical
    instruction: >-
      Confirm the coolant loop is vented BELOW 5.0 psia before demating the QD.
      Read coolant_loop_pressure_psia and cross-check.
    preconditions:
      - sensor: coolant_loop_pressure_psia
        check: less_than
        value: 5.0
    verify:
      method: sensor
      sensor: coolant_loop_pressure_psia
      check: less_than
      value: 5.0
    warnings:
      - "Demating a pressurized ammonia loop causes an ammonia release. This is critical."
    risk_if_skipped: "Demate under pressure sprays ammonia; contamination and vision hazard."
    on_failure:
      action: emergency
      note: "Loop still pressurized. Do NOT demate. Vent and re-verify."

  - id: 5
    title: Demate the QD locking collar
    safety_tier: caution
    instruction: "Using the QD collar tool, rotate the locking collar counter-clockwise to demate."
    specs:
      torque:
        fastener_id: QD-COLLAR-14
        direction: ccw
    verify:
      method: visual
      visual_ref: coolant-jumper-qd
      expect_state: "collar rotated to unlocked position; alignment stripe offset"
    warnings:
      - "Keep the demated line pointed away from you."

  - id: 6
    title: Cap the demated line
    safety_tier: caution
    instruction: "Cap the demated line immediately using the cap set (or approved substitute)."
    required_parts: [QD-JMP-14-CAP]
    verify:
      method: visual
      visual_ref: state-verification
      expect_state: "cap fully seated on the open QD port"
    on_failure:
      action: replan
      note: "If QD-JMP-14-CAP missing, use CAP-GENERIC-2 and log substitution."

  - id: 7
    title: Install replacement jumper
    safety_tier: caution
    instruction: "Hand-mate the replacement QD-JMP-14. Verify the alignment stripe lines up before torquing."
    required_parts: [QD-JMP-14]
    verify:
      method: visual
      visual_ref: coolant-jumper-qd
      expect_state: "alignment stripe continuous across the joint before collar torque"

  - id: 8
    title: Torque the QD locking collar
    safety_tier: caution
    instruction: "Set the PGT and torque the QD locking collar to spec."
    specs:
      torque:
        fastener_id: QD-COLLAR-14
    verify:
      method: visual
      visual_ref: pgt-display
      expect_state: "PGT display shows torque within spec and a good-torque indication"
    warnings:
      - "Do not exceed the collar torque; over-torque damages the seal."

  - id: 9
    title: Torque structural capture bolts A and B
    safety_tier: caution
    instruction: "Torque capture bolts A then B in two alternating passes to spec."
    specs:
      torque_sequence: [HX-M6-COOL-A, HX-M6-COOL-B]
      passes: 2
    verify:
      method: visual
      visual_ref: pgt-display
      expect_state: "PGT shows in-spec torque for both bolts across two passes"
    risk_if_skipped: "Uneven or missing bolt torque lets the jumper shift under thermal cycling."

  - id: 10
    title: Repressurize and leak check
    safety_tier: critical
    instruction: "Repressurize the loop and confirm pressure returns to nominal with no renewed frost or flakes."
    preconditions:
      - sensor: coolant_loop_pressure_psia
        check: in_range
    verify:
      method: sensor
      sensor: coolant_loop_pressure_psia
      check: in_range
    warnings:
      - "If frost or flakes reappear, stop and treat as an active ammonia release."
    on_failure:
      action: emergency
      note: "Renewed leak. Vent, cap, and escalate."

  - id: 12
    title: Reseat and torque (minor frost branch)
    safety_tier: caution
    instruction: >-
      Minor frost only: reseat the QD, verify the alignment stripe, and re-torque the
      collar to spec. Then proceed to leak check.
    specs:
      torque:
        fastener_id: QD-COLLAR-14
    verify:
      method: visual
      visual_ref: coolant-jumper-qd
      expect_state: "alignment stripe continuous; collar torqued to spec"
    on_failure:
      action: escalate
      note: "If frost persists after reseat, treat as a real leak and escalate."
---

# External Ammonia Coolant Jumper Remove & Replace (COOL-JMP-002)

Hands-free walkthrough for replacing a leaking ammonia QD coolant jumper on the truss.
Exercises exact torque-spec lookup, inventory-driven replanning, dynamic diagnostic
branching on leak symptoms, and ammonia-release emergency handling.

> Synthetic hackathon data (RAISE Summit 2026). Not real NASA flight documentation.

## Step 1 - Confirm tool kit staged (routine)

The agent calls `check_inventory` for the PGT, 7/16 socket, and QD collar tool. Any
missing tool triggers a replan (retrieve from QUEST-A2).

## Step 2 - Confirm replacement jumper and cap (routine, inventory replan)

The replacement `QD-JMP-14` is in stock, but `QD-JMP-14-CAP` is **out of stock** (see
`inventory.yaml`). The agent detects this and replans: it proposes the approved
contingency cap `CAP-GENERIC-2` and logs the substitution, or escalates if no cap exists.
This is the natural "replan if part missing" behavior.

## Step 3 - Inspect the leak and classify (caution, diagnostic branching)

The repair path depends on what you see:

- **White frost only** -> minor seep, branch to Step 12 (reseat and re-torque).
- **White flakes / snow** -> active ammonia release, enter **emergency** (decon, queue
  ground alert).
- **No frost but pressure still dropping** -> leak is not at the QD; **escalate** for loop
  isolation, because a jumper R&R will not fix it.

## Step 4 - Vent loop below 5 psia before demate (critical, sensor cross-check)

The agent reads `coolant_loop_pressure_psia` and blocks the demate until it is below
5.0 psia. Demating a pressurized ammonia loop sprays ammonia - an emergency-tier hazard.

## Step 5 - Demate the QD locking collar (caution)

Rotate the collar counter-clockwise with the collar tool. Keep the open line pointed away.

## Step 6 - Cap the demated line (caution, replan)

Cap the open port immediately. If the correct cap is missing, the agent substitutes
`CAP-GENERIC-2` and logs it.

## Step 7 - Install replacement jumper (caution)

Hand-mate `QD-JMP-14` and verify the alignment stripe is continuous before torque
(visual check against `coolant-jumper-qd`).

## Step 8 - Torque the QD locking collar (caution, torque lookup)

The agent calls `get_torque_spec(QD-COLLAR-14)` and reads back the exact PGT setting and
torque. It verifies the good-torque indication on the PGT display (`pgt-display`).

## Step 9 - Torque structural capture bolts A and B (caution, torque sequence)

Torque `HX-M6-COOL-A` then `HX-M6-COOL-B` in two alternating passes. Missing or uneven
torque is logged as a risk.

## Step 10 - Repressurize and leak check (critical)

Repressurize and confirm `coolant_loop_pressure_psia` returns to nominal with no renewed
frost. Any renewed leak re-enters emergency handling.

## Step 12 - Reseat and torque (minor frost branch)

Reached only from the Step 3 "frost only" branch: reseat, verify the alignment stripe,
re-torque the collar, then go to the leak check. If frost persists, escalate.
