# Process Requirements

The sibling requirements pages say *what* must be true —
{doc}`requirements-test`, {doc}`requirements-hardware`,
{doc}`requirements-documentation`, {doc}`requirements-support`, and
the out-of-box gates in {doc}`out-of-box-experience`. This page
says *when and how* it is enforced: the operating rhythm, at four
cadences, that keeps the SDK on track against the {doc}`roadmap`.

## Every change

An API change is a docs PR first. The diff touches
{doc}`api-c-core` / {doc}`api-python` before any implementation
lands — REQ-DOC-001 in practice, not aspiration. Every commit
carries a sign-off; every user-visible change carries a changelog
entry from the first tagged release (REQ-DOC-008). The merge gate
is already live: `sphinx -W` and linkcheck green on every push
(REQ-DOC-007). Once code exists, Tier 1 green joins the merge gate
(REQ-TEST-004) — under five minutes, every push, no exceptions.

## Every night

Tier 2 smoke runs nightly on both labgrid places (REQ-TEST-041).
Two rules give the nightly teeth:

- **A red nightly freezes the capability matrix** (REQ-TEST-042) —
  no capability flips to "available" while its suite fails — and
  gets a triage response by the next working day.
- **Rig health is a first-class result.** A rig that cannot run
  smoke at all — dead exporter, failed boot, missing PPS lock — is
  itself a red nightly, not a skipped one. Hardware test capacity
  degrades loudly or not at all.

## Every phase

A roadmap phase closes with a gate review, not a feeling:

- the phase's exit criteria are walked item by item against the
  REQ-TEST IDs they cite, with the evidence artifacts on the
  table — scope captures, completion logs, measured rates
  (REQ-TEST-023);
- the *next* phase's REQ-HW entry criteria are verified before it
  starts — explicitly including the ZU11EG Vivado license
  entitlement check before P3 (REQ-HW-010; a sibling project lost
  weeks to exactly this);
- risks are re-read, and the {doc}`roadmap` page is updated the
  same day the gate passes. The roadmap is a living document, not
  a prophecy.

## Every release

The release checklist, in outline — the executable checklists live
in {doc}`checklists`:

- version pinning recorded: HDL release, Vivado version, kernel
  commit, bitstream hash (the REQ-TEST-024 fields) plus library
  versions;
- runbooks current on every shipped platform (REQ-DOC-004);
- the newcomer walkthrough executed and timed on real hardware
  (REQ-OOBE-006/007, {doc}`out-of-box-experience`);
- capability-matrix audit: nothing described above its evidence
  level (REQ-DOC-003);
- changelog complete (REQ-DOC-008);
- examples gallery green in CI (REQ-OOBE-008).

The four loops and their gates:

```{mermaid}
graph LR
    C[every change] --> CG[docs-first diff ·<br/>sign-off · -W build ·<br/>Tier 1 green]
    N[every night] --> NG[Tier 2 smoke ·<br/>rig health ·<br/>red freezes matrix]
    P[every phase] --> PG[evidence review ·<br/>next-phase HW entry ·<br/>roadmap updated]
    R[every release] --> RG[checklist · walkthrough ·<br/>matrix audit · changelog]
    C -.-> N -.-> P -.-> R
```

## Evidence discipline

Evidence is an artifact, never a prose claim: a scope capture of a
marker against PPS, a completion log, a measured rate. Artifacts
land in the test-artifacts store automatically (REQ-HW-022) and
every timed claim ships with them (REQ-TEST-023). The linking rule
that keeps the site honest: anywhere the word *validated* appears
— index table, platform pages, capability matrix — it resolves to
its evidence within one click (REQ-DOC-003).

## Drift prevention

Once code exists, three CI checks catch documentation and
implementation drifting apart:

- **Symbol coverage** — every public symbol exported by `libdatax`
  appears in {doc}`api-c-core`; the check is a grep, and a missing
  symbol fails CI (REQ-DOC-001's enforcement arm).
- **Examples as canary** — every documented example executes in CI
  (REQ-DOC-006); the archetype gallery doubles as the acceptance
  suite (REQ-OOBE-008, {doc}`out-of-box-experience`).
- **Matrix gating** — capability flips ride suite status, never
  optimism (REQ-TEST-042).

## Requirements (REQ-PROC)

Each item pins a rule above and names the requirement it
operationalizes.

- **REQ-PROC-001 — Docs-PR-first.** A change to any public C or
  Python symbol merges only if the same PR (or an already-merged
  one) updates {doc}`api-c-core` / {doc}`api-python`
  (REQ-DOC-001).
- **REQ-PROC-002 — Sign-off and changelog gates.** Every commit is
  signed off; every user-visible change lands with its changelog
  entry (REQ-DOC-008) — checked at review, not after.
- **REQ-PROC-003 — Tier 1 joins the merge gate.** Once `libdatax`
  code exists, Tier 1 green (REQ-TEST-004) is required to merge,
  alongside the docs build (REQ-DOC-007).
- **REQ-PROC-004 — Nightly smoke cadence.** Tier 2 smoke runs
  nightly on both platforms (REQ-TEST-041); results are a visible
  history, not one-off runs.
- **REQ-PROC-005 — Red-nightly response.** A red nightly freezes
  capability-matrix changes (REQ-TEST-042) and receives triage by
  the next working day; the triage outcome is recorded with the
  run.
- **REQ-PROC-006 — Rig health is a result.** Exporter, boot, and
  reference-lock health are reported with every nightly; a rig
  unable to run smoke is a red result (REQ-HW-020, REQ-TEST-020).
- **REQ-PROC-007 — Phase gates review evidence.** A phase exits
  only through a review that walks its exit criteria against the
  cited REQ-TEST IDs with artifacts present (REQ-TEST-023).
- **REQ-PROC-008 — Next-phase hardware entry check.** Before a
  phase starts, its REQ-HW prerequisites are verified — including
  the ZU11EG Vivado license entitlement before P3 (REQ-HW-010).
- **REQ-PROC-009 — Release checklist executed and archived.**
  Every release runs the Every-release checklist; the completed
  checklist is archived with the release artifacts.
- **REQ-PROC-010 — Drift checks in CI.** The symbol-coverage grep
  and example execution run in CI once `libdatax` code exists
  (REQ-DOC-001, REQ-DOC-006).
- **REQ-PROC-011 — Evidence linking.** Every *validated* label
  resolves to linked evidence within one click (REQ-DOC-003,
  REQ-TEST-023, REQ-HW-022).

## What runs when

The cadences own REQ-PROC-001..009 — every change: 001–003; every
night: 004–006; every phase: 007–008; every release: 009. Evidence
discipline owns 011; drift prevention owns 010. A rule with no
requirement, or a requirement with no rule, is a spec bug — the
spec changes first (REQ-DOC-001).
