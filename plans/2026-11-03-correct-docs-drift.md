# Correct Docs Drift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every status claim on the SDK site match what tick, vrt49, libiio (`feature/daqiri-udp`) and hopcap prove today, add a per-repo support matrix page, and re-baseline the roadmap — sub-project A of the spec.

**Architecture:** Hand edits to six existing MyST/RST pages plus one new reference page, `docs/support-matrix.md`, that holds the per-repo hardware/feature/coverage table. Every "validated" cell links to a durable public page (tick docs site, hopcap docs site, committed reports); vrt49 and libiio claims link to GitHub source pages until their docs sites serve. No generated content yet; sub-project B replaces the hand-written matrix with a rendered one.

**Tech Stack:** Sphinx 9 / MyST / sphinxcontrib-mermaid / adi_doctools cosmic theme (all installed locally; `python3 -m sphinx -W` passes on the current tree).

**Spec:** `specs/2026-11-03-support-matrix-and-planning-hub-design.md` (sub-project A, "What the repos actually prove today", "Pages that change", "Roadmap re-baseline").

## Global Constraints

- Cross-references in `.md` use `` {doc}`page` `` only; in `index.rst` use `:doc:`.
- Build gate after every task: `cd docs && python3 -m sphinx -W -b html . _build/html` exits 0.
- Status vocabulary is exactly *validated* / *integration artifacts* / *planned* (REQ-DOC-003). Two axes everywhere a platform status appears: **infrastructure** (what the four repos prove) and **SDK API** (`libdatax`, which is *planned* on every platform).
- Nothing is described above its evidence level. Facts come from the spec table; do not add claims the spec table does not carry.
- Evidence links: tick → `https://tfcollins.github.io/tick/<page>.html`; hopcap → `https://tfcollins.github.io/hopcap/<page>.html`; vrt49 → `https://github.com/tfcollins/vrt49/blob/main/<path>`; libiio → `https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/<path>`. Never link workflow runs or artifacts.
- Prose hard-wrapped at ~72–76 columns (table rows may exceed); single H1 per page; MyST pages declare their Diátaxis quadrant in the lede (REQ-DOC-002).
- Commits: `git commit -s`, one per task, on `main`. Push at the end with `GH_ACCOUNT_AUTOSWITCH=0 git push origin main`. Never poll CI in the foreground.
- Lab names allowed on this site: labgrid place names (`tron`, `mini2`, `nemo`) already appear in the tick docs; host IPs and host names do not appear.

## Review Focus

1. A reader clicking any *validated* cell must land on a page that shows the evidence, not a repo root or a 404 — Task 7's linkcheck pins every link on the new page.
2. The Z7035 must not read as "timed hopping validated": control/transport qualified, RF settle unresolved — Task 4's grep asserts the phrase "RF-measured" is present and "validated" does not appear in the Z7035 Tick row.
3. The capability matrix must still show the SDK API as unshipped on every platform; the infrastructure annotation must not be mistaken for an SDK capability flip — Task 6's grep asserts the matrix cells still carry `P2`…`P6` and the new note names both axes.
4. The roadmap's dropped gates must not leave dangling references on other pages — Task 5's grep asserts no page still says "coherency regression" is open or "fix in flight".
5. The "Documentation-first" admonition on the index must remain true (no `libdatax` code exists) — Task 1 keeps it.

---

### Task 1: Index page — two-axis supported-targets table

**Files:**
- Modify: `docs/index.rst:5-13` (lede: name the four building blocks), `docs/index.rst:39-63` (table + vocabulary), `docs/index.rst` Platforms toctree (add `support-matrix`)

**Interfaces:**
- Produces: doc target `support-matrix` is referenced from the toctree; Task 2 creates the page. Run Task 2 before building, or add the toctree line in Task 2 instead (either order is fine as long as the build at the end of Task 2 passes).

- [ ] **Step 1: Rewrite the lede's building-block sentence**

Replace "wraps three proven building blocks — **libiio** … **Tick** … **Corundum** …" with four: **libiio** (transport and control, with the DAQIRI high-rate receive backend on the `feature/daqiri-udp` branch), **Tick** (FPGA-resident timed commands), **vrt49** (VITA 49.2 framing, IP, daemon and host backend over Corundum or direct Ethernet), and name **hopcap** as the first composite application that proves the stack on the ADRV9009-ZU11EG. Keep the "streaming radiohead" sentence and the Status admonition unchanged.

- [ ] **Step 2: Replace the Supported targets list-table with this content**

```rst
.. list-table::
   :header-rows: 1
   :widths: 24 20 18 38

   * - Target
     - Infrastructure
     - SDK API
     - Notes
   * - ADRV9009-ZU11EG on ADRV2CRR-FMC (``tron``)
     - **Validated**
     - Planned
     - Tick scheduler and timed Talise FHM hop validated on silicon;
       vrt49 Corundum 10G VITA 49.2 path; hopcap runs the timed hop
       with hardware-gated capture end to end, nightly. See
       :doc:`platform-adrv9009-zu11eg` and :doc:`support-matrix`.
   * - ADRV9361-Z7035 on ADRV1CRR-FMC
     - Integration artifacts
     - Planned
     - vrt49 1G SFP design with the vendored Tick scheduler and a
       fastlock hop controller; control and transport qualified on
       hardware, RF-measured hop settling unresolved. See
       :doc:`platform-adrv9361-z7035`.
   * - AD9081-FMCA-EBZ on ZCU102 (``mini2``)
     - Validated (Tick)
     - Not an SDK target
     - Tick's primary validated base (58/58 hardware suite); vrt49
       reference design. Listed because the SDK's Tier 1 contract
       tests inherit from it. See :doc:`support-matrix`.
```

- [ ] **Step 3: Replace the vocabulary paragraph**

Keep the three-term definition sentence. Append one sentence: "*Infrastructure* is what the tick, vrt49, libiio and hopcap repositories prove on hardware; *SDK API* is `libdatax`, which exists on no platform yet. The per-repository view is :doc:`support-matrix`."

- [ ] **Step 4: Add `support-matrix` to the Platforms toctree after `platform-adrv9009-zu11eg`**

- [ ] **Step 5: Verify stale phrases are gone**

Run: `grep -n 'not hardware-validated\|No Tick port\|three proven' docs/index.rst`
Expected: no output.

- [ ] **Step 6: Commit (build is verified at the end of Task 2)**

```bash
git add docs/index.rst
git commit -s -m "docs: index shows infrastructure and SDK-API status per target"
```

---

### Task 2: New page `docs/support-matrix.md`

**Files:**
- Create: `docs/support-matrix.md`

**Interfaces:**
- Produces: doc target `support-matrix`; section anchors `#tick`, `#vrt49`, `#libiio-daqiri-branch`, `#hopcap` (MyST auto-slugs of the H2 titles `Tick`, `vrt49`, `libiio (daqiri branch)`, `hopcap`). Tasks 3–6 link to the page, not to anchors.

- [ ] **Step 1: Write the page**

Structure, in order:

1. H1 `# Support Matrix`.
2. Lede (≤ 8 lines): this page is *reference*; it lists, per repository, the platforms each supports, which features, at which test tier of {doc}`requirements-test`, with evidence; status vocabulary per {doc}`requirements-documentation`; hand-maintained today and replaced by a generated table in the next sub-project (link the spec by filename in plain text, not `{doc}`, since specs are outside `docs/`).
3. One H2 per repo with a one-sentence role line and one GFM table with columns **Platform | Feature | Status | Tier | Evidence**. Rows, exactly these facts (from the spec table; the Evidence column is a Markdown link):

   **Tick**
   - AD9081-FMCA-EBZ / ZCU102 (`mini2`) | timed GPIO, timed capture, NCO FFH hop PoC | validated | 2 | tick site `index.html` (supported-targets table) and `example-timed-gpio-staircase.html`
   - ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | scheduler | validated | 2 | tick site `adrv9009-zu11eg-bringup.html`
   - ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timed Talise FHM hop | validated | 3 | tick site `adrv9009-fhm-hop.html`
   - ADRV9009 / ZC706 (`nemo`) | scheduler | validated | 2 | tick site `adrv9009-zc706-hop.html`
   - ADRV9009 / ZC706 | FHM hop | planned | — | same page
   - ADALM-Pluto | scheduler, fastlock hop | integration artifacts | 1 | tick site `pluto-fastlock-hop.html`

   **vrt49**
   - ADRV9009-ZU11EG, Corundum 10G SFP+/QSFP+ | VITA 49.2 RX framing over UDP, iiod-vrt49, host backend | validated | 2 | vrt49 blob `doc/source/projects/adrv9009zu11eg.md`
   - ADRV9361-Z7035, 1G SFP | VITA 49.2 RX over 1G, vendored Tick, fastlock hop controller | integration artifacts (control and transport qualified; RF settle unresolved) | 2 | vrt49 blob `doc/source/tutorials/adrv9361-tick-examples.md`
   - ADRV9361-Z7035, CCFMC LVDS | VITA 49.2 framing to host DMA | integration artifacts | 1 | vrt49 blob `doc/source/projects/adrv9361z7035_ccfmc.md`
   - ADRV9002 / ZCU102 | 4x10G striped UDP | integration artifacts (exact-boot HIL exists, last run failed) | 2 | vrt49 blob `doc/source/how-to/adrv9002-zcu102-4x10g.md`
   - AD9081 / ZCU102 | VITA 49.2 framing | integration artifacts | 1 | vrt49 blob `doc/source/projects/ad9081_zcu102.md`
   - AD-FMCOMMS2 / ZCU102 | full-duplex framer/deframer over AXI DMA | integration artifacts | 1 | vrt49 blob `doc/source/projects/fmcomms2_zcu102.md`
   - VCU118 + FMCDAQ3 | 100G RoCEv2 full rate (39.5 Gb/s, 600 s soak) | validated | 2 | vrt49 blob `doc/source/how-to/vcu118-rocev2.md`
   - VCU118 + FMCDAQ3 | 100G UDP to DAQIRI receiver | integration artifacts | 1 | vrt49 blob `doc/source/how-to/daqiri-receiver.md`

   **libiio (daqiri branch)**
   - host, any NIC | `daqiri:` backend, UDP sample mode, socket engine | validated (software: unit, emulator, loopback in CI) | 1 | libiio blob `doc/source/daqiri-backend.md`
   - host, ConnectX-5 | raw DPDK / ibverbs queues | integration artifacts (implemented, not carrying sample mode; lab-host-only tier) | 1 | libiio blob `tests/daqiri/README.md`
   - any sender | `IIOD_OP_UDP_STREAM_SETUP`, `iiod-emu --udp` | validated (software) | 1 | same page

   **hopcap**
   - ADRV9009-ZU11EG (`tron`) | Tick-timed FHM hop + hardware-gated VRT49 capture over QSFP, Context with hop frequency, sample-exact VRT timestamps, SigMF export | validated | 3 | hopcap site `reports/2026-10-23-tron-first-run.html` and `reports/2026-10-25-tron-vrt-timestamps.html`
   - ADRV9009-ZU11EG | measured Talise settle time | planned (settle is a configured knob) | — | hopcap site `example.html`

4. Closing H2 `## What "validated" means here`: three sentences restating the tiers, that a software-only validation is marked as such, and that cells go stale: this table was checked on 2026-11-03 and sub-project B makes it generated.

- [ ] **Step 2: Build**

Run: `cd docs && python3 -m sphinx -W -b html . _build/html`
Expected: exit 0, no warnings.

- [ ] **Step 3: Commit**

```bash
git add docs/support-matrix.md docs/index.rst
git commit -s -m "docs: add per-repository support matrix page"
```

---

### Task 3: ADRV9009-ZU11EG platform page

**Files:**
- Modify: `docs/platform-adrv9009-zu11eg.md:1-5` (intro), `:22-37` (What exists today), `:39-50` (release fork), `:52-59` (New work 1), `:61-76` (New work 2 and 3), `:84-90` (Capability profile)

- [ ] **Step 1: Intro**

Replace "the only board with an upstream Corundum variant today" with: the board on which the whole stack is proven: Tick, vrt49's Corundum 10G VITA 49.2 path, and the hopcap application.

- [ ] **Step 2: "What exists today" becomes four bullets**

- Stock ADI HDL + Linux (unchanged bullet).
- **Tick, validated on `tron`** (`hdl_2026_r1`, Vivado 2025.1): scheduler at `0x8600_0000`, measured 99.9989 MHz tick rate, JTAG production boot with the Tick PL before Linux and the dual-Talise JESD stack healthy; timed Talise FHM hop validated closed-loop, 5/5 edges, 0-tick skew, exact PLL readback via the internal `TAL_GPIO_0` route. Link both tick pages.
- **vrt49 Corundum 10G path**: `adrv9009zu11eg_vrt49_corundum` reference design, framer between `util_cpack2` and `axi_dmac`, VITA 49.2 over UDP on QSFP lane 0, `iiod-vrt49` and the `vrt49://` host backend; nightly software HIL over labgrid; Corundum-image tests opt-in. Link the vrt49 project page.
- **hopcap, end to end**: Tick fires the FHM GPIO, `vrt49_fhm_hop_ctrl` gates capture after a settle delay and stamps hop frequency and epoch into a hardware-emitted Context packet, data leaves over QSFP, host writes SigMF; sample-exact VRT timestamps verified; nightly HIL. Link both hopcap reports.
- Keep the `mqnic` bullet, reworded to say the SDK plans against that driver for the NIC-as-control-plane use; the sample path does not depend on it.

- [ ] **Step 3: Release fork section becomes "The release fork (resolved)"**

Three sentences: Tick's validated base on this board is `hdl_2026_r1` / Vivado 2025.1 with one deliberate deviation from stock (cache-coherency configuration, documented in tick's README release note); the regression gate in the roadmap is closed; both Tick and the vrt49 Corundum design build from the same release.

- [ ] **Step 4: "New work 1" becomes "Tick hardware validation (done)"**

Two sentences pointing at the tick evidence and stating what remains for the SDK: exposing it through `libdatax` (P3 as re-baselined in {doc}`roadmap`), and the scope-evidence staircase against PPS (REQ-TEST-023) that tick's `tron` suite does not yet produce.

- [ ] **Step 5: "New work 2" and "New work 3" collapse into one section "Network and sample plane (delivered by vrt49, exercised by hopcap)"**

Content: coexistence of Tick, the vrt49 framer and Corundum is a built, timing-clean bitstream in hopcap (`system_bd_fabric_hop.tcl`); the packetizer the old text described is vrt49's `axi_vrt49_framer`; what remains for P5/P6 on this board is the `libdatax` surface and TX (vrt49 deframer exists in HDL, not exercised by hopcap). Link hopcap's `example.html`.

- [ ] **Step 6: Capability profile**

Keep the sentence structure; add after it: "Infrastructure status for each row is in {doc}`support-matrix`; every P3 capability's infrastructure is validated, so P3 is an SDK-API phase on this board."

- [ ] **Step 7: Verify and build**

Run: `grep -n 'not validated\|none of it has run\|open cache-coherency\|hardware-unconfirmed' docs/platform-adrv9009-zu11eg.md`
Expected: no output.
Run: `cd docs && python3 -m sphinx -W -b html . _build/html`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add docs/platform-adrv9009-zu11eg.md
git commit -s -m "docs: ZU11EG page reflects validated Tick, vrt49 and hopcap state"
```

---

### Task 4: ADRV9361-Z7035 platform page

**Files:**
- Modify: `docs/platform-adrv9361-z7035.md:3-6` (intro), `:23-32` (What exists today), `:34-55` (New work 1), `:57-69` (New work 2), `:71-77` (Capability profile)

- [ ] **Step 1: Intro**

Replace "every SDK capability beyond plain streaming is new work" with: the smaller target, where Tick and a 1G VITA 49.2 path exist in vrt49 and the remaining work is RF qualification and the SDK surface.

- [ ] **Step 2: "What exists today" becomes four bullets**

- Stock ADI HDL + Linux (unchanged).
- **Tick in the vrt49 1G SFP design** (`adrv9361z7035_vrt49_sfp`): vendored `axi_timed_command_scheduler`, `vrt49_ad9361_hop_ctrl` at `0x44AB0000` driving AD9361 `fastlock_select` from `gpio_out` and gating the framer's sample admission, hop metadata (frequency, epoch) into Context packets; `adrv9361_tick_hop.py` preloads a fastlock bank of at most eight frequencies and submits absolute-time GPIO events; `pps_in` tied low (reset-relative time only). Link the vrt49 tutorial.
- **Evidence boundary, stated by vrt49**: control and Context/IQ transport passed qualification on hardware; an independent RF-measured hop settle has **not** been established. Status: *integration artifacts*.
- **1G SFP network path** (1000BASE-X, `vrt49_frame_throttle` for 61.44 MSPS on 1G, GPSDO 1PPS timestamping) and a CCFMC LVDS variant to host DMA. No Corundum wrapper and no 10G path. Link the project page.

- [ ] **Step 3: "New work 1 — Tick port" becomes "Remaining Tick work (roadmap P4)"**

Replace the four-item HDL list with what is left: (1) RF-measured fastlock settle (REQ-TEST-031) with scope or spectrum evidence; (2) `tick_stream_timestamp_tag` and `sync_ext` wiring into `data_offload` so the DMA path has the same `RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS` semantics as the ZU11EG, or a decision that the VRT framer path is the SDK's streaming path on this board; (3) an external PPS route for `pps_in`; (4) the runbook (REQ-DOC-004). Keep the four acceptance criteria unchanged.

- [ ] **Step 4: "New work 2" retitled "10G offload path (roadmap P5, still highest-risk)"**

Keep the GTX-wrapper paragraph; replace "nothing is shipped" with: the 1G SFP path is shipped and bounded to 61.44 MSPS throttled; 10G on the FMC carrier's GTX lanes is the unshipped part. Keep the MVP fallback paragraph.

- [ ] **Step 5: Capability profile**

Append: "Infrastructure status per row is in {doc}`support-matrix`: `TIMED_COMMANDS` and `FASTLOCK_HOP` infrastructure is at *integration artifacts*; the DMA-path gate/timestamp rows have no infrastructure yet."

- [ ] **Step 6: Verify and build**

Run: `grep -n 'No Tick support\|No Corundum wrapper\|nothing is shipped' docs/platform-adrv9361-z7035.md`
Expected: no output.
Run: `grep -c 'RF-measured' docs/platform-adrv9361-z7035.md`
Expected: ≥ 1.
Run: `cd docs && python3 -m sphinx -W -b html . _build/html`
Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add docs/platform-adrv9361-z7035.md
git commit -s -m "docs: Z7035 page reflects vrt49's Tick and 1G SFP design"
```

---

### Task 5: Roadmap re-baseline

**Files:**
- Modify: `docs/roadmap.md` (whole page; keep the seven-phase structure and REQ-TEST exit criteria)

- [ ] **Step 1: Mermaid diagram**

Remove gates G1 and G2 (both resolved). Keep G3 retitled "gate: Z7035 10G GTX wrapper feasibility — may slip alone". Add a node `I[infrastructure delivered:<br/>tick · vrt49 · hopcap on ZU11EG]` with dotted edges into P3, P5 and P6.

- [ ] **Step 2: Phase sections, edits only**

- P0: add "**Status: done.**"
- P1: unchanged; add "**Status: not started.** First code task."
- P2: add one sentence: vrt49's `vrt49://` libiio backend is a candidate transport alongside AXI-DMAC.
- P3: replace "Gated on" list with: "Both gates are satisfied: Tick is validated on `tron` and the `hdl_2026_r1` regression is resolved ({doc}`platform-adrv9009-zu11eg`). P3 is now the phase that exposes through `libdatax` what tick and hopcap already prove." Keep the Exit line.
- P4: replace the scope sentence with the "Remaining Tick work" list from the Z7035 page (link, do not duplicate — REQ-DOC-009).
- P5: retitle "P5 — Network plane through vrt49". ZU11EG side delivered (link ZU11EG page); Z7035 side is the 1G SFP design with the 10G wrapper as the open risk. Exit unchanged.
- P6: ZU11EG side delivered by vrt49 and exercised by hopcap; remaining: `libdatax` surface, TX via the deframer, Z7035 subsets, 100G VCU118+DAQ3 tier with DAQIRI as receiver. Exit unchanged.

- [ ] **Step 3: External dependencies table**

Drop the two ZU11EG gate rows. Add: libiio daqiri branch upstreaming (owner: libiio fork; phases P6); VCU118+DAQ3 UDP bitstream for the DAQIRI path (vrt49; P6); labgrid place for the 100G host NIC (infra; P6); hopcap upstream PRs `VRT_FABRIC_HOP_ENABLE` to vrt49 and `--system-top` to tick (hopcap; P3). Keep the `mqnic` and Corundum pin rows.

- [ ] **Step 4: Verify and build**

Run: `grep -rn 'coherency regression\|fix in flight\|hardware-unconfirmed\|Tick ZU11EG hardware validation' docs/`
Expected: output only from `docs/architecture-proposal.md` (fixed in Task 6).
Run: `cd docs && python3 -m sphinx -W -b html . _build/html`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add docs/roadmap.md
git commit -s -m "docs: re-baseline roadmap on delivered tick, vrt49 and hopcap infrastructure"
```

---

### Task 6: Capability matrix annotation and the two concept pages

**Files:**
- Modify: `docs/api-object-model.md:136-157` (matrix + explanation)
- Modify: `docs/architecture-proposal.md:36-50`, `:94-104`, `:155-175`
- Modify: `docs/streaming-model.md:111-150`

- [ ] **Step 1: Capability matrix**

Keep the table cells. Change the paragraph under it to: "P*n*" = the capability turns on in `libdatax` when that phase exits on that platform; "—" = structurally not applicable. The **infrastructure** behind each cell (what tick, vrt49 and hopcap prove today) is tracked per repository in {doc}`support-matrix`; on the ZU11EG every P3, P5 and P6 row has validated infrastructure, on the Z7035 the P4 rows are at integration artifacts. A cell flips only when both the infrastructure row and the SDK suite (REQ-TEST-042) are green.

- [ ] **Step 2: architecture-proposal.md**

- Lines 39–41: replace with "Tick is validated end-to-end on AD9081/ZCU102 and on the ADRV9009-ZU11EG (scheduler and timed FHM hop); on the ADRV9361-Z7035 it ships inside vrt49's 1G SFP design at integration-artifacts maturity."
- Lines 42–45: replace with one sentence: the `hdl_2026_r1` coherency regression is resolved; Tick and the ZU11EG Corundum variant share that release.
- Lines 46–47: append "vrt49 adds the VITA 49.2 framer in front of it, so on the ZU11EG the NIC *is* a sample transport today."
- Lines 101–103: "The future VITA-49 packetizer … roadmap, not MVP" → "The VITA 49.2 packetizer is vrt49's `axi_vrt49_framer` (and deframer for TX); it is dashed in the figure because the SDK does not expose it yet."
- Lines 155–175: retitle "## Data Plane (delivered infrastructure, SDK surface on the roadmap)". Keep the arithmetic paragraph. Replace "This is deliberately **not** in the MVP" with: the packetizer, the 10G path and a host receiver (libiio `daqiri:`, DAQIRI socket engine, with raw engines for 100G in progress) exist; the SDK's data-plane work is the API surface. Keep the last paragraph.

- [ ] **Step 3: streaming-model.md**

- Retitle `## Roadmap: Corundum RF-sample offload` → `## RF-sample offload (vrt49 today, SDK surface on the roadmap)`.
- First paragraph: state that vrt49's framer implements this on the ZU11EG and hopcap exercises it; the SVG and the datapath pages remain the block-level description.
- Bullet 3 ("Z7035 … no shipped Corundum wrapper at all"): replace with the 1G SFP path at 61.44 MSPS throttled; no 10G.
- Last paragraph: "Sample data stays on the DMA path until the packetizer phase clears its gates" → "Sample data moves on either path; the SDK's P6 exit is the `libdatax` surface over the vrt49 path."

- [ ] **Step 4: Verify and build**

Run: `grep -rn 'coherency regression\|fix in flight\|hardware-unconfirmed\|no Tick support\|not in the MVP' docs/`
Expected: no output.
Run: `grep -c 'P[2-6]' docs/api-object-model.md`
Expected: unchanged from before the edit (the cells are untouched).
Run: `cd docs && python3 -m sphinx -W -b html . _build/html`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add docs/api-object-model.md docs/architecture-proposal.md docs/streaming-model.md
git commit -s -m "docs: concept pages name vrt49 and DAQIRI as delivered infrastructure"
```

---

### Task 7: Linkcheck, push, and record

**Files:**
- Modify: `specs/2026-11-03-support-matrix-and-planning-hub-design.md` (status line only)

- [ ] **Step 1: Linkcheck the new page's external links**

Run: `cd docs && python3 -m sphinx -b linkcheck . _build/linkcheck && grep -E 'broken|redirect' _build/linkcheck/output.txt`
Expected: no `broken` lines for `tfcollins.github.io/tick`, `tfcollins.github.io/hopcap`, `github.com/tfcollins/libiio`. Lines for `github.com/tfcollins/vrt49` may report 404 because the repo is private; record them in the commit message, do not change the links (spec open question 1 and 3).

- [ ] **Step 2: Mark the spec**

Change `Status: draft for approval` to `Status: approved; sub-project A implemented YYYY-MM-DD`.

- [ ] **Step 3: Commit and push**

```bash
git add specs/2026-11-03-support-matrix-and-planning-hub-design.md plans/2026-11-03-correct-docs-drift.md
git commit -s -m "docs: record sub-project A of the support-matrix design as implemented"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```

- [ ] **Step 4: Report the Pages deploy**

Use the watch-build skill on the `docs.yml` run for the pushed commit; report the run URL and whether the site at `https://tfcollins.github.io/datax_sdk_sdr/support-matrix.html` serves.
