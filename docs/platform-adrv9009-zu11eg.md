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
  streaming needs nothing new.
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
yet produce, and exposing all of it through `libdatax` (P3 as
re-baselined in {doc}`roadmap`).

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

## Capability profile

See the canonical matrix in {doc}`api-object-model`. Summary: streaming
at P2; `TIMED_COMMANDS`/`RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS`/
`FHM_HOP`/`MCS`/`PHASE_COHERENT` at P3; `NET_OFFLOAD_NIC` at P5 (upstream
variant + coexistence); `NET_OFFLOAD_SAMPLES` at P6. `FASTLOCK_HOP` is
n/a (no AD936x). Infrastructure status per row is in
{doc}`support-matrix`: `TIMED_COMMANDS` and `FHM_HOP` are validated;
`STREAM_GATE` and `TIMESTAMPS` are validated on the VRT path through
hopcap; `RX_ARM`/`TX_ARM` on the DMA path, `MCS` and `PHASE_COHERENT`
have no infrastructure row yet. P3 is therefore mostly, not purely,
SDK-API work on this board.
