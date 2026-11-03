# Design: Support Matrix and Planning Hub

Date: 2026-11-03
Status: approved; sub-project A implemented 2026-11-03
Location note: specs live at repo root (`specs/`); `docs/` is Sphinx
source and `-W` rejects orphan pages.

## Intent

`datax_sdk_sdr` is the planning point for a four-repo SDR stack:
**tick** (timed command scheduler), **vrt49** (VITA 49.2 over Ethernet),
**libiio** `feature/daqiri-udp` (high-rate host receiver), and
**hopcap** (the first composite application that proves the stack on
the ADRV9009-ZU11EG). The SDK site should say what each repo supports,
on which hardware, with what test coverage, and should hold the task
list that feeds work back into those repos.

Today the site says things the repos contradict. It still calls Tick
on the ZU11EG "not hardware-validated", says the Z7035 has "no Tick
support", lists VITA 49 offload as a future phase, and never mentions
vrt49, DAQIRI, or hopcap. The owner's bar: **information on the SDK
site must be correct**, and it must stay correct through CI rather
than through someone remembering to edit it.

## Goals

1. The SDK site states each repo's hardware support, features, and
   test coverage accurately, with every "validated" claim linked to
   evidence (existing REQ-DOC-003 / REQ-PROC-011).
2. Those claims are owned by the repos and checked by CI, so the SDK
   can render them but cannot invent them.
3. The roadmap is re-baselined on the four repos as they stand.
4. A GitHub project on `datax_sdk_sdr` holds the tasks, each linked to
   the repo where the work lands.

## Non-goals

- Writing any `libdatax` code. The SDK API layer stays at P1 "not
  started"; this work corrects what the site says about the
  infrastructure underneath it.
- Changing the REQ-ID scheme, the Diátaxis layout, or the status
  vocabulary (*validated* / *integration artifacts* / *planned*).
- Replacing the repos' own docs, status files, or CI. The manifest is
  an additional small file, not a rewrite.
- Automating the GitHub project beyond its initial seed.

## Anti-goals

- A table that looks authoritative but is hand-maintained and drifts
  again within a month. If the pipeline is too heavy to keep green,
  it has failed even if the first render is perfect.
- Letting a claim become "validated" on the SDK site without a
  passing hardware job behind it (REQ-TEST-042).
- Describing the Z7035 or any platform above its evidence level to
  make the matrix look symmetric.

## Constraints

- SDK docs are MyST + Sphinx, built with `-W` and linkcheck on every
  push (REQ-TEST-040). Generated content must not produce warnings.
- Sub-repo conventions hold: `git commit -s`, SPDX headers, MIT in
  tick/hopcap/SDK, LGPL in vrt49, upstream licences in libiio.
- libiio's daqiri branch is a fork of ADI libiio. Its manifest and
  check must be small and self-contained so they do not complicate an
  eventual upstream PR; docs there use host placeholders, never lab
  host names.
- Lab facts (places, hosts, IPs) come from `~/dev/infra/HOSTS.md`,
  not from this document.
- `gh` on the owner's machine now carries the `project` scope for the
  `tfcollins` account.

## Sub-project A: Correct the drift now

A one-time rewrite of the SDK pages against the repos' current state.
Done by hand with links to existing evidence, because the pipeline in
sub-project B does not exist yet and the site should be honest before
it does.

### What the repos actually prove today

Gathered 2026-11-03 from each repo's README, `STATUS.md`, workflows,
and docs. Items marked **verify** need a run log or report checked
before the page says "validated".

| Repo | Platform | What is true | Backing |
|---|---|---|---|
| tick | AD9081-FMCA-EBZ / ZCU102 (`mini2`) | Validated end-to-end, 58/58 HIL, `hdl_2026_r1` and `hdl_2023_r2`, FFH NCO hop PoC | `hardware.yml`, evidence verifier |
| tick | ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Scheduler and timed Talise FHM hop validated closed-loop (5/5 edges, 0-tick skew), `hdl_2026_r1` | `tron-repeat-hil.yml`, STATUS 2026-08-04 |
| tick | ADRV9009 / ZC706 | Scheduler validated on silicon, `hdl_2023_r2`; FHM hop is a follow-up | README |
| tick | ADALM-Pluto | Integration artifacts, AD9361 fastlock hop | README |
| tick | `hdl_2026_r1` coherency regression | **Resolved**: validated with one deliberate deviation from stock | README release note |
| vrt49 | ADRV9009-ZU11EG, Corundum 10G SFP+/QSFP+ | Reference design builds in CI; software HIL suite nightly over labgrid; Corundum-image tests opt-in | `hdl-corundum.yml`, `hw-test.yml` |
| vrt49 | ADRV9361-Z7035, 1G SFP | Reference design with vendored Tick scheduler, `vrt49_ad9361_hop_ctrl` driving AD9361 `fastlock_select` and gating the framer's sample admission; `adrv9361_tick_hop.py`; kernel modules and bitstream built in CI; software HIL covers the board. Control and Context/IQ transport passed qualification on hardware; **RF-measured hop settling is unresolved** (vrt49 tutorial says so explicitly). No `tick_stream_timestamp_tag`: timestamps come from the VRT framer. | `hdl-adrv9361-sfp.yml`, `system_bd.tcl`, `adrv9361-tick-examples.md` |
| vrt49 | ADRV9361-Z7035, CCFMC LVDS | Reference design checked in; no HIL evidence found | projects page |
| vrt49 | ADRV9002 / ZCU102, 4x10G striped | Reference design, exact-boot HIL twice weekly on `mini2` with receiver on nemo; the only recent run is a failure | `hdl-adrv9002-zcu102.yml` |
| vrt49 | AD9081 / ZCU102 | Reference design; software HIL covers the board | projects page |
| vrt49 | FMCOMMS2 / ZCU102 | AXI DMA framer/deframer design; no HIL evidence found | projects page |
| vrt49 | VCU118 + FMCDAQ3, 100G | RoCEv2 full-rate hardware evidence (39.5 Gb/s, 600 s soak, zero protocol errors); DAQIRI receiver tool for the UDP path | `vcu118-rocev2.md`, PR #66 |
| libiio | host side, any sender | `daqiri:` backend with UDP sample mode over the socket engine; unit, emulator, and loopback tiers in GitHub CI; raw DPDK/ibverbs queues implemented, not yet carrying sample mode; receive only | `daqiri.yml`, `tests/daqiri/README.md` |
| libiio | 100G host NIC | `daqiri-hw` tier runs only on the lab host, not in GitHub CI; labgrid place for the NIC planned, not registered | phase 2 plan |
| hopcap | ADRV9009-ZU11EG (`tron`) | End-to-end Tick-timed FHM hop with hardware-gated VRT49 capture over QSFP and sample-exact VRT timestamps; nightly HIL | STATUS 2026-10-26, run 7 report, `hw-test.yml` |
| hopcap | open items | Talise settle time is a knob not a measurement; upstream PRs to vrt49 and tick pending; priming-hop spacing excess unexplained | STATUS "Not done" |

### Pages that change

- `docs/index.rst` supported-targets table: ZU11EG becomes
  *validated (infrastructure)*, with the three repos and evidence
  links; Z7035 becomes *integration artifacts* for Tick and the 1G SFP
  path. A third status line states that the SDK API layer is *planned*
  on every platform, so the reader sees both axes.
- `docs/platform-adrv9009-zu11eg.md`: "What exists today" rewritten;
  the release-fork risk section becomes a resolved note; "New work 1"
  (Tick validation) is done and points at tick and hopcap evidence;
  Corundum section cites the vrt49 design and hopcap's QSFP run.
- `docs/platform-adrv9361-z7035.md`: "No Tick support" and "No
  Corundum wrapper" replaced by the vrt49 1G SFP design with vendored
  Tick and fastlock hop controller. Of the four P4 HDL items, 1
  (scheduler instantiated), 2 (`gpio_out` to fastlock select via the
  hop controller), and 4 (devicetree) exist; item 3 is half done
  (sample gating through the hop controller and the VRT framer, no
  Tick timestamp tagger, no `sync_ext` wiring to `data_offload`). The
  remaining P4 work is the RF-measured hop settling (REQ-TEST-031),
  the stream-gate and timestamp semantics the SDK API needs on the DMA
  path, and the runbook (REQ-DOC-004).
- `docs/roadmap.md`: re-baselined (next section).
- `docs/api-object-model.md` capability matrix: unchanged in shape,
  but each cell gains an "infrastructure" annotation and the
  explanatory text states that a phase exit needs both the
  infrastructure row and the `libdatax` suite.
- New page `docs/support-matrix.md` (reference quadrant): the
  per-repo hardware, feature, and coverage table. In sub-project A it
  is hand-written from the table above; in sub-project B it becomes
  generated.
- `docs/architecture-proposal.md` and `docs/streaming-model.md`:
  mention vrt49 as the existing VITA 49 implementation and DAQIRI as
  the host receiver where they currently describe those as future.
  Minimal edits, not rewrites.

### Roadmap re-baseline (decided: re-baseline, not just re-status)

Keep seven phases and the REQ-TEST exit criteria. Change what each
phase means given what exists:

- **P0** done.
- **P1** SDK skeleton: unchanged, not started.
- **P2** streaming MVP: unchanged; note that vrt49's `vrt49://` libiio
  backend is a candidate transport in addition to AXI-DMAC.
- **P3** timed control ZU11EG: the gates are satisfied (Tick validated
  on `tron`, coherency resolved). The phase now means "expose through
  `libdatax` what tick and hopcap already prove". The external
  dependency table drops both ZU11EG gates.
- **P4** Z7035 parity: scope reduced to the gap between vrt49's
  existing Tick-on-Z7035 design and the full timed API; the Pluto
  analogue is no longer the starting point.
- **P5** network plane: rename from "Corundum integration" to "network
  plane through vrt49"; ZU11EG side is delivered infrastructure;
  Z7035 side is the 1G SFP design (GTX wrapper risk retired for 1G;
  10G on the FMC carrier stays open).
- **P6** RF-sample offload: ZU11EG side is delivered by vrt49 and
  exercised by hopcap; remaining work is the `libdatax` surface, the
  Z7035 subset, and the 100G VCU118 tier with DAQIRI as receiver.
- New external dependencies: libiio daqiri branch upstreaming;
  VCU118 bitstream; a labgrid place for the 100G host NIC.

## Sub-project B: Manifest pipeline (CI-driven correctness)

Decided by the owner: the table is driven from CI. The mechanism below
is the builder's proposal and the owner's calls are marked.

### Each repo declares, CI checks

Each of tick, vrt49, libiio, and hopcap gains one file, `support.json`
at the repo root. Hand-written, because a person decides what a
feature is; CI-checked, so a claim cannot exceed its evidence.

Shape (my call; the schema file is the authority):

```json
{
  "schema": 1,
  "project": "tick",
  "platforms": {
    "adrv9009-zu11eg": {
      "carrier": "adrv2crr-fmc",
      "labgrid_place": "tron",
      "hdl_release": "hdl_2026_r1",
      "features": {
        "timed-gpio": {
          "status": "validated",
          "tier": 2,
          "workflow": "tron-repeat-hil.yml",
          "evidence": "https://..."
        },
        "fhm-hop": { "status": "validated", "tier": 3, "workflow": "...", "evidence": "..." }
      }
    }
  }
}
```

Vocabulary is owned by the SDK repo so columns line up across repos:

- platform slugs: `ad9081-zcu102`, `adrv9009-zu11eg`, `adrv9009-zc706`,
  `adrv9361-z7035`, `adrv9002-zcu102`, `fmcomms2-zcu102`,
  `vcu118-daq3`, `pluto`, and `host` for host-side-only features;
- feature slugs: start from the capability matrix names
  (`streaming-rx`, `streaming-tx`, `timed-gpio`, `timed-capture`,
  `stream-gate`, `timestamps`, `fhm-hop`, `fastlock-hop`, `mcs`) plus
  transport features (`vrt-udp-1g`, `vrt-udp-10g`, `vrt-udp-100g`,
  `corundum-nic`, `daqiri-rx-socket`, `daqiri-rx-raw`);
- status: `planned` | `integration-artifacts` | `validated`;
- tier: 1, 2, 3 as in `requirements-test`.

Rules enforced by the check (fail-closed):

1. File validates against the schema; unknown slugs are errors.
2. `validated` requires `tier >= 2`, a non-empty `evidence` URL, and a
   `workflow` that exists under `.github/workflows/` in that repo.
3. `integration-artifacts` requires `evidence` pointing at the
   artifact (a project TCL, an overlay, a docs page).
4. Evidence URLs are link-checked in nightly runs only, not on push,
   so flaky hosts do not block merges.

What `evidence` may point to (my call, after the builder check):
a **durable, publicly readable page**: a docs-site page, a committed
report such as hopcap's `docs/reports/2026-10-23-tron-first-run.md`,
or a release asset. Never a workflow-run or artifact URL: tick's HIL
artifacts expire after 14 days and run logs after 90, and three of
the five repos are private so run URLs are 404 for every reader but
the owner. The run that produced the evidence goes in a separate
optional `last_run` field that the nightly reads but never
link-checks. Each repo's `branch` is a field in `sources.json`
(libiio's work is on `feature/daqiri-udp`, not its default branch).

The check is a small Python module living in the SDK repo under
`tools/datax_support/` with a CLI (`check`, `render`). Repos run it
pinned: `pipx run --spec
git+https://github.com/tfcollins/datax_sdk_sdr@<rev> datax-support
check support.json` in their existing `ci.yml` (or `tests.yml` for
libiio). My call: one shared tool rather than four copies; the pin is
bumped like any other.

### The SDK renders, never authors

- `sources.json` at the SDK root pins each repo to a revision (same
  pattern as hopcap's `pins.json`), with a `why` field.
- `datax-support render` fetches `support.json` from each pinned
  revision, validates, and writes `docs/_generated/support-*.md`
  fragments. `docs/support-matrix.md` includes them.
- **Generated fragments are committed** (my call). CI regenerates and
  fails on diff, so PRs show the table change and the docs build
  needs no network. Local workflow: run `render`, commit both.
- The capability matrix in `api-object-model.md` stays hand-written
  for the SDK-API axis; a second generated fragment next to it shows
  the infrastructure axis per cell, so the two cannot disagree
  silently.

### Nightly re-check

A new SDK workflow `support-nightly.yml`:

1. fetches `support.json` from each repo's **default branch tip** (not
   the pin), renders, and diffs against the committed fragments;
2. queries the GitHub API for the latest completed run of every
   `workflow` named by a `validated` row on that repo's default branch;
3. link-checks every `evidence` URL;
4. on any drift, red workflow, or dead link, opens or updates a single
   tracking issue titled "support matrix: drift/red" with the details.
   A red nightly freezes capability-matrix edits (REQ-TEST-042), which
   is now a visible issue rather than a rule in prose.

Red semantics (my call, after the builder check). The nightly is
**advisory**: it opens the issue; it is not a merge gate. "Red" for a
`validated` row means the most recent run of its `workflow` on the
tracked branch whose conclusion is `success` or `failure` concluded
`failure`, or no such run exists in the last 30 days (stale).
`cancelled` and `skipped` runs are ignored. A `success` whose job
skipped the hardware leg counts as success; that gap is closed at
phase-gate review, not by the tool. The freeze rule applies to
flipping a cell **to** `validated` while its row is red; it never
blocks corrections downward or the sub-project A rewrite. Several of
today's workflows would be red on day one (hopcap nightly cancelled,
ADRV9002 last run failed, tick `hardware.yml` is dispatch-only): the
first nightly's issue is the honest starting backlog, not a failure
of the design.

Pin bumps are ordinary PRs that update `sources.json` and the
fragments together.

### What this does not check

The pipeline proves that a claim names a workflow that passed and
points at an evidence URL that resolves. It does not read the
evidence, and it does not know whether the workflow tested the feature
the row claims. The gap is closed at phase-gate review (REQ-PROC-007),
not by the tool.

## Sub-project C: GitHub project seed

- One project, **"DataX SDR"**, owner `tfcollins`, linked to all five
  repos. Board and table views.
- Fields (my call): Status (Todo / In progress / Blocked / Done),
  Repo (sdk / tick / vrt49 / libiio / hopcap), Platform (slug list
  above, plus `all`), Phase (P0 to P6), Requirement (text, REQ IDs),
  Priority (P1 / P2 / P3).
- Planning issues live in `datax_sdk_sdr`. When work lands in another
  repo, the implementing issue or PR is opened there and added to the
  same project, linked from the planning issue. The board is the one
  place to look; the repos stay the places where code and evidence
  live.
- The existing SDK issue #1 ("application scenarios") is added as-is.

### Initial backlog

Sub-project A (each one issue):

1. Rewrite `index.rst` supported targets with the two-axis status.
2. Rewrite `platform-adrv9009-zu11eg.md` against tick, vrt49, hopcap.
3. Rewrite `platform-adrv9361-z7035.md` against vrt49's 1G SFP design.
4. Re-baseline `roadmap.md` and its dependency table.
5. Add `support-matrix.md` (hand-written first version).
6. Annotate the capability matrix with the infrastructure axis.
7. Touch `architecture-proposal.md` and `streaming-model.md` for
   vrt49 and DAQIRI.
8. Verify items: Z7035 hop-on-hardware, CCFMC and FMCOMMS2 HIL,
   VCU118 bitstream status (one issue each; outcome feeds 3 and 5).

Sub-project B:

9. Schema and vocabulary file in the SDK repo.
10. `datax_support` tool: `check` and `render`.
11. `sources.json` and the committed-fragment CI check in the SDK.
12. `support-nightly.yml`.
13. to 16. `support.json` plus CI check in tick, vrt49, libiio, hopcap
    (one issue per repo, opened in that repo).

Gaps the re-baseline exposes (planning issues; implementation elsewhere):

17. hopcap: measure Talise settle time instead of configuring it
    (feeds REQ-TEST-031).
18. hopcap: upstream `VRT_FABRIC_HOP_ENABLE` to vrt49 and
    `--system-top` to tick so `overlays/patches/` stops being empty.
19. tick: ZC706 FHM hop follow-up.
20. vrt49: VCU118 + DAQ3 bitstream delivery.
21. libiio: raw engines carrying UDP sample mode; labgrid place for
    the 100G NIC; upstream PR plan for the daqiri branch.
22. SDK: P1 `libdatax` skeleton (unchanged, now the first real code
    task on the board).

## Order and sizing

A, then B, then C's seed, as agreed. A is a documentation change set
in one repo; B is a small tool plus five CI edits across five repos;
C is a one-time `gh` session. Each is its own plan under `plans/`.

## Decisions from the builder check (owner, 2026-11-03)

1. **Repo visibility.** `datax_sdk_sdr` becomes public (it is
   docs-only and its site already is). `tick` and `vrt49` stay
   private; `libiio` and `hopcap` are already public. Consequences
   for sub-project B: the shared checker can be fetched from the
   public SDK repo with no token; the SDK nightly needs a read token
   for `tick` and `vrt49` (one fine-grained PAT stored as an SDK
   secret, contents read-only on those two repos); evidence for tick
   claims points at the public tick docs site; evidence for vrt49
   claims points at GitHub source pages and is a 404 for anonymous
   readers until decided otherwise. The vrt49 rows on the public SDK
   site therefore say "evidence in a private repository" next to the
   link. Flipping the SDK repo public is a sub-project B task.
2. **libiio manifest intent.** Branch-only. The file lives at
   `CI/daqiri/support.json`, the check runs in `daqiri.yml`, nothing
   is intended for the upstream PR. `sources.json` pins the
   `feature/daqiri-udp` branch for libiio.
3. **vrt49 docs site.** Left as is (404 at the root). Links to vrt49
   stay as GitHub source pages.

## Left to the builder

- Exact Sphinx mechanics for including generated fragments without
  `-W` warnings (literalinclude vs. MyST include).
- Whether `datax_support` ships as a `pyproject` package or a single
  script with `uv run`; either is fine if the pin is a git revision.
- Table layout of `support-matrix.md` (per-repo sections vs. one wide
  table), as long as every validated cell links to evidence.
- GitHub project view configuration beyond the fields listed.
- Whether libiio's check runs in `tests.yml` or `daqiri.yml`.
