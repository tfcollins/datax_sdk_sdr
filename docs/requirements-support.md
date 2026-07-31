# Support Requirements

What "supported" means here, so expectations are set before the first
issue arrives.

## Support tiers

- **REQ-SUP-001** — Everything public carries one of three statuses:
  **validated** (evidence-backed, runbook exists, CI-covered),
  **integration artifacts** (collateral exists, not proven on silicon),
  **planned** (documented intent). Same vocabulary as Tick and as
  REQ-DOC-003.
- **REQ-SUP-002** — Only *validated* items get fix-priority triage.
  Issues against *integration artifacts* are welcome but explicitly
  best-effort; issues against *planned* items become roadmap input.

## Toolchain support window

- **REQ-SUP-010** — Each release names its supported set: HDL release
  (`hdl_2023_r2` and/or `hdl_2026_r1` per the roadmap decision gate),
  Vivado version, ADI Linux branch, libiio version. Combinations
  outside the named set are unsupported, even if they happen to work.
- **REQ-SUP-011** — At most **two** HDL releases are supported at once;
  dropping one requires a deprecation note one release ahead.

## Explicitly unsupported (v1)

- **REQ-SUP-020** — Boards beyond ADRV9361-Z7035 and ADRV9009-ZU11EG
  (including boards Tick itself supports, e.g. Pluto and AD9081/ZCU102 —
  Tick's own support lives in Tick).
- **REQ-SUP-021** — Non-Linux hosts; direct register access workflows;
  UHD API compatibility ({doc}`non-goals`).

## Triage expectations

- **REQ-SUP-030** — Issue templates require: platform, HDL release +
  Vivado version, kernel/libiio versions, capability-probe output, and
  for timed-path issues the completion log. The SDK ships a
  `datax-report` dump tool to make that one command.
- **REQ-SUP-031** — Timed-path bug reports are triaged against evidence
  first: the completion record decides whether the schedule was met
  (hardware question) or never submittable (API-use question).
- **REQ-SUP-032** — Upstream boundaries are explicit: converter-driver
  bugs route to ADI Linux, scheduler-IP bugs to Tick, NIC bugs to
  Corundum/mqnic. The SDK tracks the cross-reference rather than
  absorbing the bug.
