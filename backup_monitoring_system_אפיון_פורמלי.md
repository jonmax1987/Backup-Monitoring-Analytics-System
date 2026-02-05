# Backup Monitoring System – Formal Specification (English)

## 1. Overview

This document defines the **formal product and technical specification** for the Backup Monitoring System developed for **Shva**.
The document is intentionally written in **clear, structured English** to enable seamless execution by **Cursor AI agents** across multiple sessions and contributors.

The system is designed to ingest backup metadata from JSON sources, classify backup types, compute durations and aggregates, detect anomalies, and generate reports and dashboards.
The architecture is modular, extensible, and platform-agnostic.

---

## 2. Business Need

### 2.1 Problem Statement

Backup processes currently lack:

* Clear visibility into execution times
* Historical trend analysis
* Reliable anomaly detection
* Standardized reporting

Manual inspection is time-consuming and error-prone.

### 2.2 Business Goals

* Increase transparency of backup operations
* Detect abnormal or failing backups early
* Enable performance optimization
* Reduce manual operational effort

---

## 3. System Scope (Phase 1 – Mandatory)

### Included

* Automatic backup type classification
* Duration calculation per backup
* Daily aggregation
* Period-based averages (day / week / month)
* Historical comparison
* Anomaly detection (rule-based)
* Report generation (JSON, CSV, HTML)
* Modular architecture (UI & monitoring decoupled)

### Explicitly Excluded (Future Phases)

* Advanced AI/ML anomaly detection
* External alerting systems (Slack, Email, etc.)
* Authentication / authorization

---

## 4. High-Level Architecture

### 4.1 Architectural Principles

* Separation of concerns
* Pluggable components
* Stateless core logic
* Extensibility for future integrations

### 4.2 Core Components

#### 4.2.1 Data Loader

* Reads backup metadata from JSON files
* Validates schema
* Normalizes timestamps and identifiers

#### 4.2.2 Backup Classifier

* Dedicated classification layer
* Maps raw metadata → logical backup types
* Easily extensible via configuration

#### 4.2.3 Processing Engine

* Calculates:

  * Backup duration
  * Daily aggregates
  * Period averages (day / week / month)
* Supports period-to-period comparison

#### 4.2.4 Anomaly Detection Engine

* Detects outliers relative to historical behavior
* Rule-based thresholds (configurable)
* Designed to support future AI-based strategies

#### 4.2.5 Report Generator

* Generates reports in:

  * JSON
  * CSV
  * HTML
* Supports daily and period-based reports

#### 4.2.6 Integration Layer

* Exposes processed data via adapters
* Supports:

  * Internal UI
  * External monitoring systems (Prometheus, Grafana)
* No coupling to core logic

---

## 5. Data Model (Conceptual)

### Backup Record

* backup_id
* backup_type
* start_time
* end_time
* duration
* status (success / failure)
* source_system

### Aggregated Metrics

* date / period
* backup_type
* average_duration
* max_duration
* min_duration
* anomaly_flag

---

## 6. Reporting Requirements

### Mandatory Outputs

* Daily report per backup type
* Period summary (week / month)
* Historical comparison reports

### Formats

* JSON (machine-readable)
* CSV (analysis-friendly)
* HTML (human-readable, presentation-ready)

---

## 7. UI Requirements (Initial Phase)

* Dashboard displaying:

  * Backup durations over time
  * Anomalies
  * Period comparisons
* Filtering by:

  * Date range
  * Backup type
  * Status

UI must consume data **only via the Integration Layer**.

---

## 8. Non-Functional Requirements

* Deterministic output (same input → same result)
* Testable components
* Clear logging
* Configuration-driven behavior

---

## 9. Cursor Execution Model

This section defines **strict operational rules** for Cursor AI agents to ensure deterministic, safe, and auditable progress across multiple sessions and agents.

---

### 9.1 Golden Rules (Mandatory)

1. **Single Task Focus**
   Cursor must work on **exactly one task at a time**.

2. **No Implicit Assumptions**
   Cursor must rely **only** on this specification and task definitions.

3. **No Silent Changes**
   Any architectural or behavioral change must be explicitly documented.

4. **Test Before Progress**
   A task cannot be marked DONE unless tests pass.

5. **Persistent State Awareness**
   Cursor must assume that future agents will continue the work.

---

### 9.2 Task Lifecycle

Each task must follow this lifecycle:

* TODO → IN_PROGRESS → DONE

A task may return to TODO if validation fails.

---

### 9.3 Task Definition Format

Each task **must** include:

* Task ID (unique)
* Description
* Inputs
* Expected Outputs
* Validation Method
* Status

Example:

* **Task ID:** CORE-001
* **Description:** Implement JSON Data Loader
* **Input:** JSON backup metadata files
* **Output:** Normalized in-memory backup records
* **Validation:** Unit tests for schema validation and parsing
* **Status:** TODO

---

### 9.4 Validation & Testing Rules

For every task:

* Unit tests are mandatory
* Edge cases must be tested
* Output must be deterministic

Cursor must explicitly confirm:

* Tests executed
* Tests passed

---

### 9.5 Multi-Session & Multi-Agent Rules

Cursor must assume:

* The session may end at any time
* Another agent may resume work

Therefore:

* Task status must always be updated
* No hidden state is allowed
* Decisions must be recorded

---

### 9.6 Failure Handling

If Cursor encounters:

* Ambiguous requirements
* Missing data
* Conflicting logic

It must:

1. Stop execution
2. Document the blocker
3. Request clarification

---

### 9.7 Explicit Start Instruction for Cursor

When starting work, Cursor must:

1. Read this entire document
2. Generate a task list from Phase 1 scope
3. Select the **first TODO task only**
4. Begin implementation

---

## 10. Definition of Done (Phase 1)

Phase 1 is considered complete when:

* All core components are implemented
* Reports are generated correctly in all formats
* Monthly comparisons are supported
* UI can consume processed data
* System is demo-ready for Shva

---

## 11. Phase 1 – Task List (Cursor Execution)

This section is the **authoritative task list** for Phase 1 execution.
Cursor agents must follow task order and lifecycle strictly.

---

### CORE-001 – Project Skeleton & Configuration

* **Description:** Initialize project structure and configuration system
* **Input:** Specification document
* **Output:** Repository skeleton, config files, environment setup
* **Validation:** Project builds successfully, config loaded from file
* **Status:** TODO

---

### CORE-002 – JSON Data Loader

* **Description:** Implement loader for JSON backup metadata
* **Input:** JSON files
* **Output:** Normalized backup records in memory
* **Validation:** Unit tests for parsing, schema validation, edge cases
* **Status:** TODO

---

### CORE-003 – Backup Classification Layer

* **Description:** Dedicated layer for backup type identification
* **Input:** Raw backup metadata
* **Output:** Classified backup types
* **Validation:** Tests for multiple backup types and extensibility
* **Status:** TODO

---

### CORE-004 – Processing Engine

* **Description:** Compute durations, daily aggregates, period averages
* **Input:** Classified backup records
* **Output:** Aggregated metrics
* **Validation:** Tests for day/week/month calculations
* **Status:** TODO

---

### CORE-005 – Historical Comparison Module

* **Description:** Compare metrics across periods (week vs week, month vs month)
* **Input:** Aggregated metrics
* **Output:** Comparison results
* **Validation:** Tests for correct deltas and edge cases
* **Status:** TODO

---

### CORE-006 – Anomaly Detection Engine (Rule-Based)

* **Description:** Detect abnormal backup durations vs historical behavior
* **Input:** Historical metrics
* **Output:** Anomaly flags
* **Validation:** Tests for threshold breaches and false positives
* **Status:** TODO

---

### CORE-007 – Report Generator

* **Description:** Generate reports in JSON, CSV, HTML
* **Input:** Aggregated and anomaly data
* **Output:** Report files
* **Validation:** Format validation for all outputs
* **Status:** TODO

---

### CORE-008 – Integration Layer

* **Description:** Decouple core logic from UI and monitoring systems
* **Input:** Processed system data
* **Output:** Adapter interfaces
* **Validation:** Mock adapters for UI and monitoring
* **Status:** TODO

---

### CORE-009 – Basic Dashboard (UI)

* **Description:** Initial dashboard for visualization
* **Input:** Integration layer data
* **Output:** Visual dashboard
* **Validation:** Manual validation + data consistency checks
* **Status:** TODO

---

### CORE-010 – End-to-End Validation

* **Description:** Validate full system flow
* **Input:** Sample JSON datasets
* **Output:** Full reports + dashboard output
* **Validation:** End-to-end tests
* **Status:** TODO

---

## 12. Cursor Start Instruction

**Cursor Instruction:**

1. Read this entire document
2. Start with **CORE-001 only**
3. Do not proceed to next task until:

   * Tests pass
   * Task marked DONE
4. Persist task status updates

---

## 13. Final Note

This document is the single source of truth for Phase 1 execution.
