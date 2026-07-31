# Platform: ADRV9009-ZU11EG

ZU11EG SOM + dual ADRV9009 on the ADRV2CRR-FMC carrier. The full-featured
reference target: JESD204B, HMC7044 clocking, QSFP+, and the only board
with an upstream Corundum variant today.

## Board summary

- **SoC**: Xilinx Zynq UltraScale+ XCZU11EG.
- **RF**: 2× ADRV9009 — 4R4T total, up to 245.76 MSPS, JESD204B, behind
  an HMC7044 for MCS-capable clock/SYSREF distribution.
- **Carrier**: ADRV2CRR-FMC — QSFP+ cage, the substrate for the Corundum
  NIC variant.
- **Timed-tune mechanism**: Talise FHM, hop-triggered by an ARM GPIO
  ({doc}`timing-synchronization`).

```{eval-rst}
.. raw:: html
   :file: _static/images/platform-zu11eg.svg
```

## What exists today

- Stock ADI HDL reference design + Linux (JESD204-FSM) support — P2
  streaming needs nothing new.
- **Corundum NIC, upstream**: `make CORUNDUM=1` on
  `projects/adrv9009zu11eg/adrv2crr_fmc` (`hdl_2026_r1`) builds a QSFP+
  10 Gb/s NIC (CSR at `0xA000_0000`, dedicated DTS) parallel to the JESD
  datapath. Built from a pinned sibling clone of upstream Corundum.
- **Tick integration artifacts, not validated**: project TCL dropping the
  scheduler at BD `0x4600_0000` (PS-physical `0x8600_0000`), FHM-pin
  XDC, and a devicetree overlay exist in the Tick repo — none of it has
  run on silicon. Tick's validated base is AD9081/ZCU102.
- Related, in progress elsewhere: mainlining-quality `mqnic` driver work
  (netdev/NAPI/devlink/PTP) in the corundum-zcu102-fmcomms2 effort —
  this SDK plans against that driver landing, not against the private
  raw-MMIO interface.

## The release fork (named risk)

Tick's hardware validation lives on `hdl_2023_r2` / Vivado 2023.2; the
Corundum variant lives on `hdl_2026_r1` / Vivado 2025.1 — which currently
carries an **open cache-coherency regression** (ZCU102-diagnosed:
`CACHE_COHERENCY`/`dma-coherent`/FSBL AFIFM mismatch; fix in flight,
hardware-unconfirmed). Decision gate in the {doc}`roadmap`:

- regression fixed → single `hdl_2026_r1` design carries Tick + Corundum;
- regression persists → P3 ships timed control on `hdl_2023_r2` *without*
  Corundum, and P5 waits. Timed control does not hostage the NIC, nor
  vice versa.

## New work 1 — Tick hardware validation (roadmap P3)

Bring-up of the existing artifacts on the lab unit (labgrid place
`tron`): build the chosen HDL base with the Tick TCL, boot, driver
probe, then the acceptance ladder — timed-GPIO staircase with scope
evidence, timed capture with tick-exact timestamps, Talise FHM hop
triggered by the scheduler with settling measurement
({doc}`requirements-test`).

## New work 2 — Tick + Corundum coexistence (roadmap P5)

One design fitting both: address-map audit (Tick at `0x8600_0000`, mqnic
CSR at `0xA000_0000` — no conflict on paper; IRQ routing to be
re-verified), fabric resource budget with the NIC's BRAM/logic appetite,
and clock-domain review (Corundum's 250 MHz datapath vs Tick's 100 MHz
tick clock vs JESD device clocks).

## New work 3 — VITA-49 packetizer (roadmap P6)

The Corundum application-section packetizer specified in
{doc}`streaming-model`, with the full block-level datapath and
control-plane walk in {doc}`hdl-datapath-corundum`. The ZU11EG is its
lead platform: the QSFP+ cage's
lane headroom is the only credible path to native-rate subsets beyond
10 G.

## MCS

Dual-chip phase coherence is this platform's defining capability; the
procedure and the SDK contract (`run_mcs()`, live `PHASE_COHERENT` state,
coherence-gated streams) are specified in {doc}`timing-synchronization`.

## Capability profile

See the canonical matrix in {doc}`api-object-model`. Summary: streaming
at P2; `TIMED_COMMANDS`/`RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS`/
`FHM_HOP`/`MCS`/`PHASE_COHERENT` at P3; `NET_OFFLOAD_NIC` at P5 (upstream
variant + coexistence); `NET_OFFLOAD_SAMPLES` at P6. `FASTLOCK_HOP` is
n/a (no AD936x).
