# ZeroDelay
Hands-free offline repair agent for technicians working without internet.

## Problem
Technicians in space, mines, ships, offshore platforms, or remote sites cannot rely on cloud tools while doing critical repairs.

## Solution
FieldFix uses local Gemma, voice input/output, sensor simulation, procedure tracking, and safety validation to guide technicians step by step.

## Why It Is Not Simple RAG
- Tracks procedure state
- Confirms each step before moving on
- Detects skipped/out-of-order steps
- Branches dynamically when symptoms change
- Cross-checks live sensor data against repair assumptions
- Blocks risky actions through a safety gate
- Replans when tools/parts are missing
- Runs hands-free with voice-to-text and text-to-voice

## Core Features
- Local Gemma agent
- Voice-to-text input
- Text-to-voice repair guidance
- Live sensor monitoring
- Real-time drift alerts
- Torque/pressure spec lookup
- Inventory and parts checker
- Safety tiering
- Emergency mode
- Silent risk logging
- Optional final session report

## Demo Flow
1. Technician reports a warning by voice.
2. Agent diagnoses likely fault.
3. Sensors begin drifting out of range.
4. Agent pauses the repair and warns the technician.
5. Technician confirms each step hands-free.
6. Missing tool/part triggers replanning.
7. Emergency mode halts the walkthrough if risk becomes critical.
8. Session log is generated for later review.

## Tech Stack
- Next.js / React
- TypeScript
- Local Gemma
- Browser speech recognition or local STT
- Browser/local TTS
- Fake equipment manuals
- Simulated sensors
