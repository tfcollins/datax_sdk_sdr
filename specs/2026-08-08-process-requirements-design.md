# Design: Process Requirements Page (sub-project 1 of 3)

Date: 2026-08-08
Status: approved design, pre-implementation
Location note: specs live at repo root (`specs/`) — `docs/` is Sphinx
source and `-W` rejects orphan pages.

## Series context

User goal: keep the SDK on track across testing, hardware testing,
documentation, and process. Decomposed (user-confirmed) into three
staged sub-projects, each with its own spec → plan cycle:

1. **This spec** — the development-process page: the operating
   rhythm connecting REQ-TEST / REQ-HW / REQ-DOC / REQ-OOBE.
2. Phase-gate + release checklists (living documents, derived from
   the process page).
3. CI groundwork (workflow skeletons for the tiers, evidence store).

## Problem

The requirements pages define *what* must be true (test tiers,
hardware inventory, docs discipline, OOBE gates) and the roadmap
traces exit criteria to REQ-TEST IDs — but nothing defines *when and
how* any of it is enforced: no per-PR flow, no standing cadence, no
phase-gate procedure, no release rhythm, no evidence-linking rule,
no drift checks. The requirements are a wall; this page makes them
a schedule.

## Decisions (user-confirmed)

- Framing: `docs/requirements-process.md` in Requirements & Plan,
  REQ-PROC numbered items (sibling-page pattern).
- Organization: the four cadences — every change / every night /
  every phase / every release — plus evidence-discipline and
  drift-prevention cross-cutting sections (Approach A).

## The page

- **File:** `docs/requirements-process.md`
- **Title:** `# Process Requirements`
- **Toctree:** Requirements & Plan, between `requirements-support`
  and `roadmap`.
- **Length:** ~150–180 lines; site conventions (MyST, `{doc}` roles
  only, bold run-in labels, hard wrap ~72–76, single H1).
- **Lede** (~5 lines): sibling pages say what must be true; this
  page says when and how it is enforced. Links
  {doc}`requirements-test`, {doc}`requirements-hardware`,
  {doc}`requirements-documentation`, {doc}`requirements-support`,
  {doc}`roadmap`, {doc}`out-of-box-experience`.

### Sections

1. **`## Every change`** — an API change is a docs PR first: the
   diff touches {doc}`api-c-core` / {doc}`api-python` before any
   implementation lands (REQ-DOC-001 in practice); sign-off
   required; changelog entry for user-visible changes
   (REQ-DOC-008); `sphinx -W` + linkcheck are the merge gate
   (REQ-DOC-007, already live); once code exists, Tier 1 green
   joins the merge gate (REQ-TEST-004).
2. **`## Every night`** — Tier 2 smoke nightly on both labgrid
   places (REQ-TEST-041); a red nightly freezes capability-matrix
   changes (REQ-TEST-042) and gets triage by the next working day;
   **rig health is a first-class result** — a rig that cannot run
   smoke (dead exporter, failed boot, missing PPS lock) is itself a
   red nightly, so hardware capacity degrades loudly.
3. **`## Every phase`** — roadmap exit criteria become a gate
   review: evidence walked item-by-item against the cited REQ-TEST
   IDs (artifacts, not assertions — REQ-TEST-023); the next phase's
   REQ-HW entry criteria verified before it starts, explicitly
   including the ZU11EG Vivado license-entitlement check before P3
   (REQ-HW-010); risks re-read; the {doc}`roadmap` page updated the
   same day the gate passes.
4. **`## Every release`** — the checklist in outline: version
   pinning recorded (REQ-TEST-024 fields), runbooks current
   (REQ-DOC-004), newcomer walkthrough executed and timed
   (REQ-OOBE-006/007), capability-matrix audit — no capability
   above its evidence level (REQ-DOC-003), changelog complete,
   examples gallery green (REQ-OOBE-008). Notes the executable
   checklists are the next deliverable in this series.
5. **`## Evidence discipline`** — what counts as evidence (scope
   captures, completion logs, measured rates — never prose), where
   it lives (test-artifacts store, REQ-HW-022), and the linking
   rule: every "validated" label resolves to evidence within one
   click (REQ-DOC-003, REQ-TEST-023).
6. **`## Drift prevention`** — CI checks that catch docs↔code
   divergence once code exists: every exported public symbol
   appears in {doc}`api-c-core` (a grep, REQ-DOC-001's enforcement
   arm); examples executed in CI as the docs' canary (REQ-DOC-006,
   REQ-OOBE-008); capability flips gated by suite status
   (REQ-TEST-042).
7. **Diagram** — one mermaid `graph` (flat, no subgraphs): the four
   loops at their frequencies, each annotated with its gate
   (change → merge gate; night → matrix freeze; phase → evidence
   review; release → checklist). Placed after the four cadence
   sections, before evidence discipline.
8. **`## Requirements (REQ-PROC)`** — eleven items,
   `- **REQ-PROC-NNN — Title.** Body.`:
   - 001 — Docs-PR-first merge rule for public API changes
     (operationalizes REQ-DOC-001).
   - 002 — Sign-off and changelog as merge requirements
     (REQ-DOC-008).
   - 003 — Tier 1 green joins the merge gate once code exists
     (REQ-TEST-004).
   - 004 — Nightly Tier-2 smoke on both platforms (REQ-TEST-041).
   - 005 — Red nightly: triage by next working day; capability
     matrix frozen until green (REQ-TEST-042).
   - 006 — Rig health reported as a nightly result; an unrunnable
     rig is a red result (REQ-HW-020, REQ-TEST-020).
   - 007 — Phase gates review evidence against the cited REQ-TEST
     IDs; artifacts required (REQ-TEST-023).
   - 008 — Next-phase REQ-HW entry criteria verified before the
     phase starts; the P3 Vivado license entitlement check is named
     (REQ-HW-010).
   - 009 — The release checklist is executed and archived for every
     release (fields per the Every-release section).
   - 010 — Drift checks run in CI: public-symbol coverage grep and
     example execution (REQ-DOC-001, REQ-DOC-006).
   - 011 — Evidence linking: every "validated" label resolves to
     linked evidence within one click (REQ-DOC-003, REQ-TEST-023,
     REQ-HW-022) — the evidence-discipline section's rule, pinned.
9. **Closing trace** (~4 lines): each section names its REQ-PROC
   items (cadences → 001..009; evidence discipline → 011; drift
   prevention → 010); a section with no requirement, or a
   requirement with no section, is a spec bug (REQ-DOC-001).

## Integration

- `docs/index.rst`: add `requirements-process` to the Requirements
  & Plan toctree between `requirements-support` and `roadmap`.
- `docs/roadmap.md`: one sentence in the lede pointing at the
  process page ("the operating rhythm that runs these gates:
  {doc}`requirements-process`"). Only existing-page edit.

## Verification

1. `cd docs && python3 -m sphinx -W -b html . _build/html` passes.
2. `python3 -m sphinx -b linkcheck . _build/linkcheck` clean.
3. `grep -n ':doc:' docs/requirements-process.md` and grep `:::` —
   both empty.
4. Light + dark screenshots read; diagram contained and legible.
5. Sidebar shows the page between Support Requirements and Roadmap.
6. Ship: commit -s, push, CI deploys site + PDF.

## Out of scope

- The checklists themselves (sub-project 2) and any CI workflow
  files (sub-project 3).
- Edits to the existing requirements pages (REQ-PROC cites them).
- REQ prefix registry changes beyond introducing REQ-PROC.
