# SECIDS-CNN Black-Box Design Roadmap

## Scope and Assumptions
- Objective: build a production-grade black-box design and test architecture for SECIDS-CNN (WebUI, APIs, capture, model inference, countermeasures, scheduler, and data pipelines).
- Constraint: it is not possible to exhaust *all* global sources; this roadmap is based on authoritative/publicly available sources and is structured so new sources can be continuously added.

## Source Acquisition Summary (Public)
1. Wireshark User Guide (Preferences + Capture + Display filter references)
   - https://www.wireshark.org/docs/wsug_html_chunked/ChCustPreferencesSection.html
   - https://www.wireshark.org/docs/wsug_html_chunked/ChCapCaptureOptions.html
   - https://www.wireshark.org/docs/wsug_html_chunked/ChWorkBuildDisplayFilterSection.html
2. NIST testing and control frameworks
   - NIST SP 800-115 (Technical Guide to Information Security Testing and Assessment)
   - NIST SP 800-53 Rev.5 (security/privacy controls catalog)
3. OWASP testing references
   - OWASP WSTG
   - OWASP Top 10
4. Black-box design technique references
   - Black-box testing method and test design techniques (equivalence partitioning, boundary value, decision tables, state transitions, pairwise)

## Black-Box Design Target for SECIDS-CNN
Treat SECIDS-CNN as an external system with these observable interfaces only:
- UI surface: Web pages, settings/task panels, user role workflows.
- API surface: `/api/*` endpoints.
- CLI/task surface: launcher scripts, scheduler jobs, terminal-triggered actions.
- Data I/O surface: input PCAP/CSV feeds and output reports/artifacts.
- Security surface: auth, role authorization, token/session behavior, sudo-gated operations.
- Runtime behavior: queueing, retries, cancellation, passive/active capture mode transitions.

## Roadmap

### Phase 0 — Baseline Inventory (Week 1)
Deliverables
- External interface catalog (UI pages, endpoints, command actions, input/output files).
- Black-box requirement matrix (expected behavior, constraints, and negative cases).
- Risk-ranked test domains (critical, high, medium).

SECIDS-CNN tasks
- Enumerate and freeze API contracts from `WebUI/app.py`.
- Build panel/flow inventory from `WebUI/templates/index.html` and `WebUI/static/app.js`.
- Create black-box asset map for `Tools/`, `Scripts/`, `SecIDS-CNN/`, `Countermeasures/`.

### Phase 1 — Test Design Architecture (Weeks 2–3)
Deliverables
- Technique mapping per interface:
  - Equivalence partitions for API payload fields.
  - Boundary values for durations, limits, intervals, counters, pagination.
  - Decision tables for role/permission/action combinations.
  - State transition models for capture lifecycle and job lifecycle.
  - Pairwise combinations for settings and mode combinations.
- Oracle strategy (expected status code, schema, state effects, artifacts).

SECIDS-CNN tasks
- Define state models:
  - Packet capture: `stopped -> running -> paused -> running -> stopped`.
  - Job queue: `queued -> running -> completed|failed|timeout|cancelled`.
- Define authorization decision table for `guest/viewer/operator/admin` across endpoints.

### Phase 2 — Data Strategy (Weeks 3–5)
Deliverables
- Black-box data catalog:
  - Benign traffic samples.
  - DDoS-like synthetic/mixed attack traffic.
  - Corrupted/malformed packet and CSV samples.
  - Large-volume stress datasets.
- Data quality and provenance checks.

SECIDS-CNN tasks
- Use existing project datasets (`Archives/`, `SecIDS-CNN/datasets/`, `Captures/`).
- Add external threat-intel enrichment workflow (KEV/NVD snapshots already present in project pipeline).
- Build controlled synthetic generators for edge-case payloads and invalid inputs.

### Phase 3 — Harness and Automation (Weeks 5–8)
Deliverables
- Black-box runner with modular suites:
  - `ui_blackbox_suite`
  - `api_blackbox_suite`
  - `pipeline_blackbox_suite`
  - `security_blackbox_suite`
- Deterministic fixtures and reproducible environment profile.
- CI-ready report format (JSON + markdown summary).

SECIDS-CNN tasks
- Reuse existing validation scripts and stress harness as base (debug scanners, stress tests).
- Add schema assertions for all API responses.
- Add idempotency/retry verification for action endpoints.

### Phase 4 — Security and Abuse-Case Validation (Weeks 8–10)
Deliverables
- OWASP/NIST-aligned black-box abuse case pack.
- Authentication/session/authorization attack simulations.
- Misconfiguration and privilege escalation negative tests.

SECIDS-CNN tasks
- Validate session timeout, forced password change, role gates, and sudo-gated execution behavior.
- Validate server-backed model registry paths and no leakage into non-server paths.
- Validate data-retention/TrashDump lifecycle as externally observable behavior.

### Phase 5 — Observability and Quality Gates (Weeks 10–12)
Deliverables
- Release gating policy:
  - blocking tests for critical interfaces,
  - warning-only tests for non-critical drift.
- KPI dashboard:
  - requirement coverage,
  - interface pass rate,
  - defect escape rate,
  - MTTR for failed suites.
- Operational runbook for black-box regressions.

SECIDS-CNN tasks
- Add acceptance thresholds per risk tier.
- Integrate suite execution into scheduled/triggered project validation flow.
- Add nightly full black-box run and per-change smoke gate.

## Initial Test Pack (Start Immediately)
1. API contract tests for all `GET/POST/PUT/DELETE` endpoints with role matrix.
2. Capture state-transition tests (manual + passive auto behavior).
3. Model registry path integrity tests (`ServerDB/modelDB/*` expected).
4. Settings persistence tests for Wireshark-style section keys.
5. Queue resilience tests (pause/resume/clear/cancel/retry).
6. Dataset pipeline tests (conversion/import/export/sync idempotency).

## Governance Model
- Weekly black-box design review (engineering + security + QA).
- Monthly source refresh (NIST/OWASP/Wireshark updates, CVE/KEV feed relevance).
- Versioned baseline of expected external behavior for each release.

## Definition of Done for Black-Box Program
- 100% critical interface coverage (as externally observable requirements).
- Role-based abuse-case pack in CI.
- Deterministic reproduction artifacts for every failed black-box run.
- Signed release checklist with black-box gate results attached.
