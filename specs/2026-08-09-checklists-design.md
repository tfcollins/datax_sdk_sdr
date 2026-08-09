# Design: Phase-Gate and Release Checklists Page (sub-project 2 of 3)

Date: 2026-08-09
Status: approved design, pre-implementation
Location note: specs live at repo root (`specs/`) — `docs/` is Sphinx
source and `-W` rejects orphan pages.

## Series context

Sub-project 2 of the "keep the SDK on track" series. Sub-project 1
shipped `docs/requirements-process.md` (REQ-PROC-001..011).
Sub-project 3 (CI groundwork) follows.

## Problem

REQ-PROC-007 requires phase gates to review evidence item-by-item;
REQ-PROC-009 requires a release checklist "executed and archived for
every release". Neither artifact exists — the process page carries
only an outline. This page is the artifact: reference checklists
plus the convention that makes them executable and archivable.

## Decisions (user-confirmed)

- Mechanism: a docs page with checklist tables (not GitHub issue
  templates, not repo-root files).
- Execution/archival convention: per gate review or release, the
  table is copied into a record in the test-artifacts store
  (REQ-HW-022), filled in, and archived with the evidence — that
  archive satisfies REQ-PROC-009.

## The page

- **File:** `docs/checklists.md`
- **Title:** `# Phase-Gate and Release Checklists`
- **Quadrant:** *reference* (declared in the lede, REQ-DOC-002 —
  the site's first reference-quadrant page).
- **Toctree:** Requirements & Plan, between `requirements-process`
  and `roadmap`.
- **Length:** ~110–140 lines; site conventions (MyST, `{doc}` only,
  GFM tables, single H1, hard wrap ~72–76). No mermaid diagram —
  two tables need no flowchart. No new REQ IDs — this page is the
  artifact existing requirements demanded.

### Structure

1. **Lede** (~6 lines): what these are (the artifacts REQ-PROC-007
   and REQ-PROC-009 require — {doc}`requirements-process`); the
   execution convention (copy table into a test-artifacts-store
   record, fill in, archive with the evidence — REQ-HW-022); links
   {doc}`roadmap` and {doc}`requirements-test`.
2. **`## Phase-gate checklist`** — short intro (phase-specific exit
   criteria live in {doc}`roadmap`; this table is the generic
   review procedure — link, never duplicate, REQ-DOC-009), then one
   GFM table with columns **Item | Verifies | Evidence recorded**:
   - Exit criteria walked item-by-item against cited REQ-TEST IDs |
     REQ-PROC-007, REQ-TEST-023 | artifact links per criterion
   - Evidence artifacts present and linked | REQ-PROC-011,
     REQ-DOC-003 | one-click resolution spot-check
   - Next-phase REQ-HW entry criteria verified | REQ-PROC-008 |
     per-item check results
   - Entering P3: ZU11EG Vivado license entitlement confirmed |
     REQ-PROC-008, REQ-HW-010 | entitlement confirmation
   - Risks re-read; roadmap updated same day | REQ-PROC-007 (gate
     procedure), {doc}`roadmap` | roadmap commit sha
   - Gate record archived in the test-artifacts store | REQ-HW-022
     | record location
3. **`## Release checklist`** — same table shape:
   - Version pinning recorded: HDL release, Vivado version, kernel
     commit, bitstream hash (the REQ-TEST-024 fields) plus library
     versions | REQ-TEST-024 | manifest link
   - Runbooks current on every shipped platform | REQ-DOC-004 |
     runbook revision links
   - Newcomer walkthrough executed on real hardware; time recorded
     against the ≤ 15 min bar | REQ-OOBE-006, REQ-OOBE-007 |
     measured time + stumble list (defects filed)
   - Capability-matrix audit: nothing above its evidence level |
     REQ-DOC-003 | audit note per flipped capability
   - Changelog complete for user-visible changes | REQ-DOC-008 |
     changelog diff link
   - Examples gallery green in CI | REQ-OOBE-008 | CI run link
   - Completed checklist archived with the release artifacts |
     REQ-PROC-009 | archive location
4. **`## Using these tables`** (~8 lines): the copy-fill-archive
   procedure spelled out once; a completed checklist is evidence,
   subject to the same linking rule as everything else
   (REQ-PROC-011).

## Touch to requirements-process.md (same commit)

Three word-level edits, clearing the spec addendum in
`specs/2026-08-08-process-requirements-design.md`:
1. The "Every release" intro sentence "the executable checklist is
   its own deliverable, derived from this page" becomes "the
   executable checklists live in {doc}`checklists`".
2. Line ~56: "library versions, bitstream hash (the REQ-TEST-024
   fields)" → "bitstream hash (the REQ-TEST-024 fields) plus
   library versions" (fixes the field attribution; requires
   reordering the list so the parenthetical follows "bitstream
   hash").
3. Line ~136 (REQ-PROC-010): "from the first `libdatax` release" →
   "once `libdatax` code exists".

## Integration

- `docs/index.rst`: add `checklists` between `requirements-process`
  and `roadmap` in the Requirements & Plan toctree.

## Verification

1. `cd docs && python3 -m sphinx -W -b html . _build/html` passes.
2. Linkcheck clean; greps for `:doc:` and `:::` empty on both
   touched .md files.
3. Light + dark screenshots read — both tables render styled and
   legible in both themes (tables are the risk surface).
4. Sidebar order: Process Requirements → Checklists → Roadmap.
5. Ship: commit -s, push, CI deploys site + PDF; deployed page and
   PDF verified with attempt-history disclosure.

## Out of scope

- CI workflows and evidence-store tooling (sub-project 3).
- Phase-specific exit-criteria content (stays in the roadmap).
- GitHub issue templates (mechanism not chosen).
