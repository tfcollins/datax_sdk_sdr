# Phase-Gate and Release Checklists

The executable artifacts that {doc}`requirements-process` requires:
REQ-PROC-007 makes a phase gate an item-by-item evidence review,
and REQ-PROC-009 makes the release checklist something "executed
and archived", not read. This page is *reference*. The convention:
for each gate review or release, copy the table into a record in
the test-artifacts store (REQ-HW-022), fill it in, and archive it
with the evidence. Phase-specific exit criteria live in
{doc}`roadmap`; test tiers in {doc}`requirements-test`.

## Phase-gate checklist

The generic review procedure for closing any roadmap phase. The
phase's own exit criteria are listed in {doc}`roadmap` — this table
governs *how* they are reviewed, and links rather than repeats
them.

| Item | Verifies | Evidence recorded |
|---|---|---|
| Exit criteria walked item-by-item against the REQ-TEST IDs they cite | REQ-PROC-007, REQ-TEST-023 | artifact link per criterion |
| Evidence artifacts present and one-click resolvable | REQ-PROC-011, REQ-DOC-003 | spot-check note |
| Next phase's REQ-HW entry criteria verified | REQ-PROC-008 | per-item check results |
| Entering P3 only: ZU11EG Vivado license entitlement confirmed | REQ-PROC-008, REQ-HW-010 | entitlement confirmation |
| Risks re-read; {doc}`roadmap` updated the same day | REQ-PROC-007 | roadmap commit sha |
| Gate record archived in the test-artifacts store | REQ-HW-022 | record location |

## Release checklist

| Item | Verifies | Evidence recorded |
|---|---|---|
| Version pinning recorded: HDL release, Vivado version, kernel commit, bitstream hash (the REQ-TEST-024 fields) plus library versions | REQ-TEST-024 | manifest link |
| Runbooks current on every shipped platform | REQ-DOC-004 | runbook revision links |
| Newcomer walkthrough executed on real hardware; time measured against the ≤ 15 min bar | REQ-OOBE-006, REQ-OOBE-007 | measured time; stumble list with filed defects |
| Capability-matrix audit: nothing above its evidence level | REQ-DOC-003 | audit note per flipped capability |
| Changelog complete for user-visible changes | REQ-DOC-008 | changelog diff link |
| Examples gallery green in CI | REQ-OOBE-008 | CI run link |
| Completed checklist archived with the release artifacts | REQ-PROC-009 | archive location |

## Using these tables

Copy the table into the gate or release record, fill every Evidence
cell with a link or a written value — an empty cell is an
unfinished review — and archive the completed copy with the rest of
the evidence. A completed checklist is itself evidence, subject to
the same one-click linking rule as everything else (REQ-PROC-011,
{doc}`requirements-process`).
