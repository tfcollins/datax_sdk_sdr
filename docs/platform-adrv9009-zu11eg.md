# Platform: ADRV9009-ZU11EG

ZU11EG SOM + dual ADRV9009 on the ADRV2CRR-FMC carrier. The full-featured
reference target: JESD204B, HMC7044 clocking, QSFP+, and the board on
which the whole stack is proven: Tick, vrt49's Corundum 10G VITA 49.2
path, and the hopcap application.

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
  streaming needs nothing new. **P2 streaming proven on hardware
  2026-11-05** (matrix: integration artifacts until `hw-test.yml` runs) on `tron` (12/12). The PL was **not** stock 2023_R2: it was
  the recovery bitstream (sha256 `a22f4cf6…`, `hdl_system_id` HDL `main`
  `085a6ed7`, 2026-06-09), with the stock 2023_R2 Kuiper kernel and DTB
  and stock `iiod` 0.26. On this image `axi-adrv9009-tx-hpc` names its
  scan channels `voltage0..7` (interleaved I/Q), while RX uses
  `voltage{n}_i/_q`. Digital loopback needs `bist_framer_a_loopback`=1 on
  both phys (register 0x1532 bit 7). It is bit-exact on all four channels
  with I and Q exchanged and unit gain; an RF loopback would confirm the
  TX I/Q orientation independently (REQ-TEST-030 RF part). RX streams at
  about 53 MB/s for one channel (recorded). Evidence:
  [libdatax docs/evidence/p2](https://github.com/tfcollins/libdatax/tree/main/docs/evidence/p2).
- **P3a timed control proven on hardware 2026-11-06** (matrix: integration
  artifacts until `hw-test.yml` runs) on `tron`, on hopcap's SFP image with
  the Tick PPS selector. Through `libdatax`: a GPIO staircase on exact ticks,
  a late command dropped without executing, FHM timed tunes on chip A (hop
  schedule with the priming edge onto `fhmInitFrequency`, dense hops, exact
  PLL readback across 2.4-2.5 GHz), PPS-aligned device time with nothing on
  the external PPS input (Corundum's PTP PPS is the fallback), and MCS
  verification. The first timed tune must be at least now + 20 ms ahead on
  this board. On this image TX DMA feeds vrt49's deframer, so the P2 TX tests
  skip and P2 RX runs as the regression. Evidence:
  [libdatax docs/evidence/p3a](https://github.com/tfcollins/libdatax/tree/main/docs/evidence/p3a).
- **Tick, validated on `tron`** (`hdl_2026_r1`, Vivado 2025.1):
  scheduler at PS-physical `0x8600_0000`, measured 99.9989 MHz tick
  rate, JTAG production boot with the Tick PL in place before Linux
  and the dual-Talise JESD stack healthy alongside it; timed Talise FHM
  hop validated closed-loop — 5/5 edges, 0-tick skew, exact PLL
  readback — via the internal `TAL_GPIO_0` route. Evidence:
  [ZU11EG bring-up](https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html),
  [FHM hop](https://tfcollins.github.io/tick/adrv9009-fhm-hop.html).
- **vrt49 Corundum 10G path**: the `adrv9009zu11eg_vrt49_corundum`
  reference design places the VITA 49.2 framer between `util_cpack2`
  and `axi_dmac`, streams IF Data over UDP on the 10G SFP+ port (QSFP
  lane 0 supported for bring-up), and pairs with `iiod-vrt49` on the
  target and the `vrt49://` libiio backend on the host. The software
  path runs nightly over labgrid; the Corundum image passed its 9/9
  qualification on `tron`. Evidence:
  [hardware results](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/hw-results-zu11eg.md),
  [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9009zu11eg.md)
  (private repository).
- **hopcap, end to end**: Tick fires the FHM GPIO; `vrt49_fhm_hop_ctrl`
  closes sample admission, waits a settle delay, emits a hardware
  Context packet carrying the hop frequency and epoch, then opens a
  capture window; data leaves over QSFP lane 0 and the host writes
  SigMF with sample-exact VRT timestamps. Runs nightly. Evidence:
  [first tron run](https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html),
  [VRT timestamps](https://tfcollins.github.io/hopcap/reports/2026-10-25-tron-vrt-timestamps.html).
- Related, in progress elsewhere: mainlining-quality `mqnic` driver work
  (netdev/NAPI/devlink/PTP) in the corundum-zcu102-fmcomms2 effort. The
  SDK plans against that driver for the NIC-as-control-plane use; the
  sample path above does not depend on it.

## The release fork (resolved)

Tick's validated base on this board is `hdl_2026_r1` / Vivado 2025.1,
built stock. The one deliberate cache-coherency deviation Tick carries
is in its ZCU102 flow (`prepare_adi_hdl.py` pins `CACHE_COHERENCY`
off there), documented in Tick's README release note; the ZU11EG
project has no such pin. The regression gate that the {doc}`roadmap`
once carried is closed: Tick, the vrt49 Corundum design and hopcap's
combined bitstream all build from the same release.

## Tick hardware validation (done)

Of the acceptance ladder the SDK asked for, driver probe, timed GPIO
and the scheduler-triggered Talise FHM hop are passed; the evidence is
linked above and summarised in {doc}`support-matrix`. Timed capture
with tick-exact timestamps exists only on the VRT path (hopcap's
timestamps come from the vrt49 framer, not from a Tick tagger on the
DMA path). What remains: the DMA-path tagger and `sync_ext` wiring if
the SDK keeps a DMA streaming path on this board, the scope-evidence
staircase against PPS (REQ-TEST-023) that Tick's `tron` suite does not
yet produce. Exposing the scheduler, FHM hops, PPS time and MCS
through `libdatax` is done (P3a); the DMA-path pieces are P3b
({doc}`roadmap`).

## Network and sample plane (delivered by vrt49, exercised by hopcap)

Coexistence of Tick, the vrt49 framer and Corundum in one design is a
built, timing-clean bitstream in hopcap (`system_bd_fabric_hop.tcl`).
The packetizer this page once described as future work is vrt49's
`axi_vrt49_framer`; the block-level walk in {doc}`hdl-datapath-corundum`
still describes the datapath. What remains for P5 and P6 on this board
is the `libdatax` surface and the TX direction: the vrt49 deframer
exists in HDL but hopcap does not exercise it. The hopcap
[example page](https://tfcollins.github.io/hopcap/example.html) shows
the dataflow and the first captures.

## MCS

Dual-chip phase coherence is this platform's defining capability; the
procedure and the SDK contract (`run_mcs()`, live `PHASE_COHERENT` state,
coherence-gated streams) are specified in {doc}`timing-synchronization`.
In P3a `run_mcs()` verifies the JESD and MCS state that the kernel's
JESD204 FSM already ran at boot; it does not re-run the sequence.
`PHASE_COHERENT` stays false because the device tree enables no RF PLL
phase sync, and the cross-chip phase measurement (REQ-TEST-032) needs RF
cabling `tron` does not have yet.

## Capability profile

See the canonical matrix in {doc}`api-object-model`. Summary: streaming
at P2; `TIMED_COMMANDS`/`RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS`/
`FHM_HOP`/`MCS`/`PHASE_COHERENT` at P3; `NET_OFFLOAD_NIC` at P5 (upstream
variant + coexistence); `NET_OFFLOAD_SAMPLES` at P6. `FASTLOCK_HOP` is
n/a (no AD936x). Infrastructure status per row is in
{doc}`support-matrix`: `TIMED_COMMANDS` and `FHM_HOP` are validated;
`STREAM_GATE` and `TIMESTAMPS` are validated on the VRT path through
hopcap; `RX_ARM`/`TX_ARM` on the DMA path, `MCS` and `PHASE_COHERENT`
have no infrastructure row yet. libdatax P3a adds `timed-gpio`,
`fhm-hop`, `sdk-timed` and `mcs` rows for this board (integration
artifacts); `MCS` is verification only and `PHASE_COHERENT` is
unreachable on the current device tree.
