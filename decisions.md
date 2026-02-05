# Architectural Decisions Log (ADR)

This document records **explicit architectural and design decisions**.
No decision should be changed without adding a new entry.

---

## ADR-001 – Modular Architecture
**Decision:** Core logic is fully decoupled from UI and monitoring integrations.

**Reason:** Enable reuse across different organizations and future extensibility.

**Implications:** All integrations must go through the Integration Layer.

**Date:** 2026-02-01

---

## ADR-002 – Rule-Based Anomaly Detection (Phase 1)
**Decision:** Use rule-based thresholds instead of ML/AI for Phase 1.

**Reason:** Deterministic behavior and faster validation.

**Implications:** Future AI-based detection must be pluggable.

**Date:** 2026-02-01

---

## Instructions for Cursor Agents
- Never modify an existing ADR
- Add new ADRs sequentially

