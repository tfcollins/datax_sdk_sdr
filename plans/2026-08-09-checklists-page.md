# Checklists Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `docs/checklists.md` — the phase-gate and release checklist tables with their copy-fill-archive convention — per `specs/2026-08-09-checklists-design.md` (sub-project 2 of 3), and apply three word-level fixes to `requirements-process.md`.

**Architecture:** One new MyST reference page in Requirements & Plan (between `requirements-process` and `roadmap`), two GFM tables, no diagram, no new REQ IDs; plus a toctree line and three anchored edits in `requirements-process.md`.

**Tech Stack:** Sphinx 7+ / MyST / adi_doctools cosmic theme; headless `google-chrome` for visual verification.

## Global Constraints

- Cross-references in `.md` use `` {doc}`page-name` `` ONLY — bare `:doc:` renders as literal text silently. In `index.rst` (RST), `:doc:` is correct.
- Build gate: `python3 -m sphinx -W -b html . _build/html` from `docs/` must pass (use `python3`; bare `python` is not on PATH).
- Prose hard-wrapped at ~72–76 columns (table rows may exceed — tables are code-like); single H1; no admonitions.
- Commits: `git commit -s`. Push with `GH_ACCOUNT_AUTOSWITCH=0 git push origin main`. Never poll CI in foreground; disclose full run-attempt history in ship reports.

---

### Task 1: Author the page, apply the process-page fixes, verify the build

**Files:**
- Create: `docs/checklists.md`
- Modify: `docs/index.rst` (Requirements & Plan toctree — insert between `requirements-process` and `roadmap`)
- Modify: `docs/requirements-process.md` (three anchored word-level edits)

**Interfaces:**
- Consumes: existing doc targets `requirements-process`, `roadmap`, `requirements-test`, `out-of-box-experience` (all exist).
- Produces: doc target `checklists` referenced by `index.rst` and `requirements-process.md`.

- [ ] **Step 1: Write `docs/checklists.md` with exactly this content**

````markdown
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
````

- [ ] **Step 2: Add the page to the Requirements & Plan toctree**

In `docs/index.rst`, the Requirements & Plan toctree currently
contains:

```rst
   requirements-support
   requirements-process
   roadmap
```

Change to:

```rst
   requirements-support
   requirements-process
   checklists
   roadmap
```

- [ ] **Step 3: Apply three anchored edits to `docs/requirements-process.md`**

Edit A — lines 52–53 currently read:

```markdown
The release checklist, in outline — the executable checklist is
its own deliverable, derived from this page:
```

Change to:

```markdown
The release checklist, in outline — the executable checklists live
in {doc}`checklists`:
```

Edit B — lines 55–57 currently read:

```markdown
- version pinning recorded: HDL release, Vivado version, kernel
  commit, library versions, bitstream hash (the REQ-TEST-024
  fields);
```

Change to:

```markdown
- version pinning recorded: HDL release, Vivado version, kernel
  commit, bitstream hash (the REQ-TEST-024 fields) plus library
  versions;
```

Edit C — lines 135–137 currently read:

```markdown
- **REQ-PROC-010 — Drift checks in CI.** The symbol-coverage grep
  and example execution run in CI from the first `libdatax`
  release (REQ-DOC-001, REQ-DOC-006).
```

Change to:

```markdown
- **REQ-PROC-010 — Drift checks in CI.** The symbol-coverage grep
  and example execution run in CI once `libdatax` code exists
  (REQ-DOC-001, REQ-DOC-006).
```

- [ ] **Step 4: Build and run regression checks**

```bash
cd docs && python3 -m sphinx -W -b html . _build/html
python3 -m sphinx -b linkcheck . _build/linkcheck
grep -n ':doc:' checklists.md requirements-process.md   # must print nothing
grep -n ':::' checklists.md requirements-process.md     # must print nothing
```

Expected: both sphinx runs report `build succeeded`; both greps
empty; no `broken` lines in `_build/linkcheck/output.txt`.

- [ ] **Step 5: Commit (local)**

```bash
git add docs/checklists.md docs/index.rst docs/requirements-process.md
git commit -s -m "Checklists page: phase-gate and release tables; process-page follow-up fixes"
```

### Task 2: Visual verification, light and dark

**Files:**
- No source changes expected; fixes (if any) amend Task 1's files.

**Interfaces:**
- Consumes: `docs/_build/html/checklists.html` from Task 1.
- Produces: verified screenshots; go/no-go for Task 3.

- [ ] **Step 1: Capture light and dark screenshots**

```bash
cd docs/_build/html
SCRATCH=<session scratchpad dir>
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata \
  --window-size=1280,3200 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/ckl-light.png "file://$PWD/checklists.html"
sed 's|<head>|<head><script>localStorage.setItem("theme","dark");</script>|' \
  checklists.html > __dark-check.html
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata2 \
  --window-size=1280,3200 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/ckl-dark.png "file://$PWD/__dark-check.html"
rm __dark-check.html
```

- [ ] **Step 2: Read both screenshots and check**

Read the images with the Read tool — claims come from pixels.
Check: both tables render as styled tables with all three columns
legible in BOTH themes (tables are this page's risk surface —
check header contrast and row borders in dark mode specifically);
long Item cells wrap inside their column without breaking the
table; no literal `:doc:` text. If a table overflows the content
column, wrap the offending cell text shorter and re-run Task 1
steps 4–5 (amend the commit).

- [ ] **Step 3: Check sidebar order and the process-page link**

```bash
grep -o 'href="checklists.html"[^>]*>[^<]*' index.html | head -3
grep -c 'checklists.html' requirements-process.html
```

Expected: index.html shows "Phase-Gate and Release Checklists"
between Process Requirements and Roadmap (confirm order visually in
a light screenshot of index.html); requirements-process.html count
≥ 1.

### Task 3: Ship and verify deployed

**Files:**
- No new changes; pushes Task 1's commit.

**Interfaces:**
- Consumes: the local commit from Task 1.
- Produces: live page at
  `https://tfcollins.github.io/datax_sdk_sdr/checklists.html`.

- [ ] **Step 1: Push**

```bash
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```

- [ ] **Step 2: Watch the Publish Docs workflow in the background**

```bash
RUN=$(GH_ACCOUNT_AUTOSWITCH=0 gh run list --limit 1 \
  --json databaseId,headSha \
  --jq '.[0] | select(.headSha[0:7]=="<pushed sha>") | .databaseId')
GH_ACCOUNT_AUTOSWITCH=0 gh run watch $RUN --exit-status --interval 20
```

One rerun permitted for a transient deploy failure; a second
failure is BLOCKED. Billing errors: immediately BLOCKED, no rerun.
Before writing the report, pull
`gh api repos/tfcollins/datax_sdk_sdr/actions/runs/<RUN_ID> --jq '.run_attempt'`
and disclose the full attempt history with per-attempt outcomes.

- [ ] **Step 3: Verify the deployed page**

Screenshot
`https://tfcollins.github.io/datax_sdk_sdr/checklists.html`, read
it, confirm both tables render. Confirm the PDF picked the page up:

```bash
curl -s https://tfcollins.github.io/datax_sdk_sdr/datax-sdr-sdk.pdf \
  -o /tmp/ckl-deployed.pdf && pdftotext /tmp/ckl-deployed.pdf - \
  | grep -c "Phase-Gate and Release Checklists"
```

Expected: count ≥ 1.
