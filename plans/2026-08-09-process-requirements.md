# Process Requirements Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `docs/requirements-process.md` — the four-cadence operating rhythm with REQ-PROC-001..011 — per `specs/2026-08-08-process-requirements-design.md` (sub-project 1 of 3).

**Architecture:** One new MyST page in the Requirements & Plan section (between `requirements-support` and `roadmap`), one mermaid cadence diagram, an eleven-item REQ-PROC block, plus two integrations: an `index.rst` toctree line and one sentence in `roadmap.md`'s lede.

**Tech Stack:** Sphinx 7+ / MyST / sphinxcontrib-mermaid / adi_doctools cosmic theme; headless `google-chrome` for visual verification.

## Global Constraints

- Cross-references in `.md` use `` {doc}`page-name` `` ONLY — bare `:doc:` renders as literal text silently. In `index.rst` (RST), `:doc:` is correct.
- Build gate: `python3 -m sphinx -W -b html . _build/html` from `docs/` must pass (use `python3`; bare `python` is not on PATH).
- Mermaid: no subgraphs needed here; `deterministicIds` already configured in `conf.py` — do not touch.
- Prose hard-wrapped at ~72–76 columns; single H1; bold run-in labels, no admonitions.
- Commits: `git commit -s`. Push with `GH_ACCOUNT_AUTOSWITCH=0 git push origin main`. Never poll CI in foreground.

---

### Task 1: Author the page, integrate it, verify the build

**Files:**
- Create: `docs/requirements-process.md`
- Modify: `docs/index.rst` (Requirements & Plan toctree — insert between `requirements-support` and `roadmap`)
- Modify: `docs/roadmap.md` (lede — one sentence added)

**Interfaces:**
- Consumes: existing doc targets `requirements-test`, `requirements-hardware`, `requirements-documentation`, `requirements-support`, `roadmap`, `out-of-box-experience`, `api-c-core`, `api-python` (all exist).
- Produces: doc target `requirements-process` referenced by `index.rst` and `roadmap.md`.

- [ ] **Step 1: Write `docs/requirements-process.md` with exactly this content**

````markdown
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

The release checklist, in outline — the executable checklist is
its own deliverable, derived from this page:

- version pinning recorded: HDL release, Vivado version, kernel
  commit, library versions, bitstream hash (the REQ-TEST-024
  fields);
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
  and example execution run in CI from the first `libdatax`
  release (REQ-DOC-001, REQ-DOC-006).
- **REQ-PROC-011 — Evidence linking.** Every *validated* label
  resolves to linked evidence within one click (REQ-DOC-003,
  REQ-TEST-023, REQ-HW-022).

## What runs when

The cadences own REQ-PROC-001..009 — every change: 001–003; every
night: 004–006; every phase: 007–008; every release: 009. Evidence
discipline owns 011; drift prevention owns 010. A rule with no
requirement, or a requirement with no rule, is a spec bug — the
spec changes first (REQ-DOC-001).
````

- [ ] **Step 2: Add the page to the Requirements & Plan toctree**

In `docs/index.rst`, the Requirements & Plan toctree currently
ends:

```rst
   requirements-support
   roadmap
```

Change to:

```rst
   requirements-support
   requirements-process
   roadmap
```

- [ ] **Step 3: Add the roadmap back-link**

In `docs/roadmap.md`, the lede currently reads:

```markdown
Seven phases. Each exits on acceptance criteria traced to
{doc}`requirements-test` IDs; capabilities flip in the
{doc}`api-object-model` matrix only at phase exit (REQ-TEST-042).
```

Change to:

```markdown
Seven phases. Each exits on acceptance criteria traced to
{doc}`requirements-test` IDs; capabilities flip in the
{doc}`api-object-model` matrix only at phase exit (REQ-TEST-042).
The operating rhythm that runs these gates — per change, nightly,
per phase, per release — is {doc}`requirements-process`.
```

- [ ] **Step 4: Build and run regression checks**

```bash
cd docs && python3 -m sphinx -W -b html . _build/html
python3 -m sphinx -b linkcheck . _build/linkcheck
grep -n ':doc:' requirements-process.md   # must print nothing
grep -n ':::' requirements-process.md     # must print nothing
```

Expected: both sphinx runs report `build succeeded`; both greps
empty; no `broken` lines in `_build/linkcheck/output.txt`.

- [ ] **Step 5: Commit (local)**

```bash
git add docs/requirements-process.md docs/index.rst docs/roadmap.md
git commit -s -m "Process requirements: four-cadence operating rhythm, REQ-PROC-001..011"
```

### Task 2: Visual verification, light and dark

**Files:**
- No source changes expected; fixes (if any) amend Task 1's files.

**Interfaces:**
- Consumes: `docs/_build/html/requirements-process.html` from Task 1.
- Produces: verified screenshots; go/no-go for Task 3.

- [ ] **Step 1: Capture light and dark screenshots**

```bash
cd docs/_build/html
SCRATCH=<session scratchpad dir>
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata \
  --window-size=1280,4400 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/proc-light.png "file://$PWD/requirements-process.html"
sed 's|<head>|<head><script>localStorage.setItem("theme","dark");</script>|' \
  requirements-process.html > __dark-check.html
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata2 \
  --window-size=1280,4400 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/proc-dark.png "file://$PWD/__dark-check.html"
rm __dark-check.html
```

- [ ] **Step 2: Read both screenshots and check**

Read the images with the Read tool — claims come from pixels.
Check: styled rendering in both themes; the mermaid diagram shows
four cadence nodes, four gate nodes, and the dashed frequency
chain with no label overlap; no literal `:doc:` text; the REQ-PROC
list renders styled. If gate-node labels collide, split the
offending label with `<br/>` and re-run Task 1 steps 4–5 (amend
the commit).

- [ ] **Step 3: Check sidebar order and the roadmap back-link**

```bash
grep -o 'href="requirements-process.html"[^>]*>[^<]*' index.html | head -3
grep -c 'requirements-process.html' roadmap.html
```

Expected: index.html shows the page titled "Process Requirements"
between Support Requirements and Roadmap (confirm order visually
in a light screenshot of index.html); roadmap.html count ≥ 1.

### Task 3: Ship and verify deployed

**Files:**
- No new changes; pushes Task 1's commit.

**Interfaces:**
- Consumes: the local commit from Task 1.
- Produces: live page at
  `https://tfcollins.github.io/datax_sdk_sdr/requirements-process.html`.

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

Run via background Bash; report the conclusion once. One rerun is
permitted for a transient deploy failure; a second failure is
BLOCKED. A billing-error failure is immediately BLOCKED, no rerun.
If the run record later shows more attempts than you triggered,
disclose the full attempt history in your report rather than
asserting a count you did not verify.

- [ ] **Step 3: Verify the deployed page**

Screenshot
`https://tfcollins.github.io/datax_sdk_sdr/requirements-process.html`,
read it, confirm the cadence diagram renders. Confirm the PDF
picked the page up:

```bash
curl -s https://tfcollins.github.io/datax_sdk_sdr/datax-sdr-sdk.pdf \
  -o /tmp/proc-deployed.pdf && pdftotext /tmp/proc-deployed.pdf - \
  | grep -c "REQ-PROC-001"
```

Expected: count ≥ 1.
