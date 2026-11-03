# GitHub Project Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One GitHub project, "DataX SDR", on `tfcollins`, linked to the five repositories, with the fields the spec names and an initial backlog of planning issues in `datax_sdk_sdr` — sub-project C.

**Architecture:** A single idempotent script, `tools/seed_project.py`, drives `gh project` and `gh issue`: it creates the project if no project of that title exists, creates missing fields and options, creates each backlog issue if no open issue with that title exists, adds it to the project, and sets its field values. Re-running changes nothing.

**Tech Stack:** `gh` CLI (project scope present), Python 3.12 stdlib (`subprocess`, `json`).

**Spec:** `specs/2026-11-03-support-matrix-and-planning-hub-design.md`, "Sub-project C: GitHub project seed".

## Global Constraints

- Project title `DataX SDR`, owner `tfcollins`; linked repos `datax_sdk_sdr`, `tick`, `vrt49`, `libiio`, `hopcap`.
- Fields: `Codebase` (single select; GitHub reserves the name `Repo`: sdk, tick, vrt49, libiio, hopcap), `Platform` (single select: the nine slugs plus `all`), `Phase` (single select: P0..P6), `Priority` (single select: P1, P2, P3), `Requirement` (text). `Status` is the built-in field.
- Planning issues live in `datax_sdk_sdr`; implementing-repo issues are opened there later by whoever takes the item and added to the same project (not in this plan).
- Issue bodies name the spec section or evidence they come from and link the implementing repo.
- Existing SDK issue #1 is added as-is.
- Items already delivered by sub-projects A and B are not created as issues.

## Review Focus

1. Re-running the script must not duplicate the project, fields, options or issues — Task 1 runs it twice and diffs the counts.
2. Every issue must land on the board with all four single-select fields set, so the table view filters work — Task 1 checks the item list for empty cells.

---

### Task 1: Seed script, run twice, verify

**Files:**
- Create: `tools/seed_project.py`

**Backlog (title | repo | platform | phase | priority | requirement):**

1. Support matrix: add `SUPPORT_READ_TOKEN` and dispatch the first nightly | sdk | all | P0 | P1 | REQ-TEST-042
2. Support matrix: merge the four `support.json` PRs and re-pin `sources.json` | sdk | all | P0 | P1 | REQ-DOC-003
3. datax-support: deferred minors from the final review | sdk | all | P0 | P3 | —
4. Docs: capability-matrix cell annotations and "three building blocks" wording are stale after the roadmap re-baseline | sdk | all | P0 | P3 | REQ-DOC-003
5. P1: `libdatax` skeleton — context/device over libiio, Python bindings, capability framework | sdk | all | P1 | P1 | REQ-TEST-001, REQ-TEST-002
6. ZU11EG: timed-GPIO staircase with scope evidence against PPS | tick | adrv9009-zu11eg | P3 | P2 | REQ-TEST-022, REQ-TEST-023
7. ZU11EG: MCS and phase-coherence infrastructure row | tick | adrv9009-zu11eg | P3 | P2 | REQ-TEST-032
8. hopcap: measure Talise settle time instead of configuring it | hopcap | adrv9009-zu11eg | P3 | P2 | REQ-TEST-031
9. hopcap: upstream `VRT_FABRIC_HOP_ENABLE` to vrt49 and `--system-top` to tick | hopcap | adrv9009-zu11eg | P3 | P2 | —
10. tick: ZC706 FHM hop follow-up and a CI workflow that targets the ZC706 | tick | adrv9009-zc706 | P3 | P3 | REQ-TEST-022
11. Z7035: RF-measured fastlock settle | vrt49 | adrv9361-z7035 | P4 | P2 | REQ-TEST-031
12. Z7035: DMA-path timestamp tagger and `sync_ext` wiring, or decide the VRT path is the SDK streaming path | vrt49 | adrv9361-z7035 | P4 | P3 | REQ-TEST-022
13. Z7035: external PPS route for Tick `pps_in` | vrt49 | adrv9361-z7035 | P4 | P3 | REQ-HW-002
14. Z7035: runbook | sdk | adrv9361-z7035 | P4 | P3 | REQ-DOC-004
15. vrt49: ADRV9002/ZCU102 4x10G exact-boot HIL last run failed; triage | vrt49 | adrv9002-zcu102 | P5 | P2 | REQ-TEST-033
16. ZU11EG: TX through the vrt49 deframer exercised end to end | vrt49 | adrv9009-zu11eg | P6 | P3 | REQ-TEST-033
17. vrt49: VCU118 + DAQ3 UDP bitstream for the DAQIRI path | vrt49 | vcu118-daq3 | P6 | P2 | REQ-TEST-033
18. libiio: raw DPDK/ibverbs engines carrying UDP sample mode; labgrid place for the 100G NIC | libiio | host | P6 | P2 | REQ-TEST-033
19. libiio: upstream PR plan for the daqiri branch | libiio | host | P6 | P3 | —

- [ ] **Step 1: Write `tools/seed_project.py`** — functions `ensure_project() -> (number, id)`, `ensure_field(name, options) -> field`, `ensure_issue(title, body) -> issue_url`, `add_and_set(issue_url, values)`; a `BACKLOG` list of dicts with the table above and a body per item (two to four sentences, with the source: spec section, STATUS.md, or review ledger). Uses `gh project list/create/field-list/field-create/link/item-add/item-list/item-edit --format json` and `gh issue list/create`.

- [ ] **Step 2: Run it**

Run: `python3 tools/seed_project.py --owner tfcollins`
Expected: prints the project URL, `fields: 5`, `issues created: 19`, `items on board: 20` (19 + issue #1).

- [ ] **Step 3: Run it again**

Run: `python3 tools/seed_project.py --owner tfcollins`
Expected: `issues created: 0`, `items on board: 20`, exit 0.

- [ ] **Step 4: Verify no empty cells**

Run: `gh project item-list <number> --owner tfcollins --format json --limit 50 | python3 -c "import json,sys; items=json.load(sys.stdin)['items']; bad=[i['title'] for i in items if any(k not in i for k in ('repo','platform','phase','priority'))]; print('missing:', bad)"`
Expected: `missing: []` (issue #1 may be the one exception; set its fields by hand in the script).

- [ ] **Step 5: Commit**

```bash
git add tools/seed_project.py
git commit -s -m "tools: idempotent seed of the DataX SDR GitHub project"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```
