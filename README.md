# ZeroDelay

ZeroDelay is a hands-free offline maintenance agent for technicians working in disconnected, high-risk environments.

It guides repairs step by step using local Gemma, voice input/output, live sensor monitoring, procedure state tracking, inventory checks, and safety validation.

## Problem

Technicians in space habitats, mines, offshore platforms, ships, remote industrial sites, and emergency zones often work without reliable internet access.

When equipment fails, they cannot depend on cloud tools, search engines, or remote experts. In critical situations, delays can damage equipment, endanger workers, or stop operations entirely.

## Solution

ZeroDelay runs locally on a laptop or tablet and acts as an offline repair copilot.

A technician can describe a fault by voice, receive spoken guidance, confirm each step hands-free, and continue working without touching a screen.

The system tracks the repair procedure, monitors simulated sensor readings, checks safety conditions before risky steps, verifies required tools and parts, and switches into emergency mode if conditions become unsafe.

## Core Capabilities

* Local Gemma-powered repair guidance
* Voice-to-text technician input
* Text-to-speech step-by-step instructions
* Procedure state tracking
* Step confirmation before progression
* Skipped-step and out-of-order-step detection
* Dynamic diagnostic branching when symptoms change
* Live sensor monitoring and drift alerts
* Torque and pressure specification lookup
* Inventory and parts availability checks
* Safety tiering for routine, risky, and emergency actions
* Safety gate before hazardous steps
* Emergency mode with immediate safety instructions
* Offline escalation queue for later connectivity
* Silent risk logging surfaced when unresolved
* Final session report generation

## System Flow

1. Technician reports a fault by voice.
2. ZeroDelay interprets the symptom and current equipment state.
3. The diagnostic engine identifies the likely fault path.
4. The procedure engine starts the correct repair sequence.
5. The safety gate checks sensor readings, tools, parts, and risk level.
6. The technician receives spoken instructions one step at a time.
7. Each step must be confirmed before the system advances.
8. Live sensor readings are monitored during the repair.
9. If risk increases, ZeroDelay pauses the walkthrough and enters emergency mode.
10. At the end, the system generates a session report for later review.

## Demo Scenario

A technician is repairing a water recycler in an offline Mars habitat simulation.

The system detects a pressure fault, checks the required tools, guides the technician through a filter replacement, monitors pressure drift during the repair, blocks an unsafe step when pressure remains too high, and generates a final maintenance report.

## Why It Matters

ZeroDelay is built for environments where cloud AI is unavailable, hands are occupied, and mistakes are expensive.

It gives field workers a local, voice-driven, safety-aware assistant that can guide procedures, monitor risk, and preserve an audit trail without requiring connectivity.

## Tech Stack

* Next.js
* React
* TypeScript
* Local Gemma
* Browser or local speech-to-text
* Browser or local text-to-speech
* Simulated equipment telemetry
* Structured repair procedures
* Local safety validation engine

## Built During the Hackathon

* Offline repair assistant interface
* Voice-guided procedure flow
* Local Gemma agent integration
* Sensor simulation
* Safety gate
* Procedure state engine
* Inventory and parts checker
* Emergency mode
* Risk log
* Session report generation
