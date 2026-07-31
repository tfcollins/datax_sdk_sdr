# Platform: ADRV9361-Z7035

Zynq-7035 + AD9361 SOM. The smaller target — and the one where every SDK
capability beyond plain streaming is **new work**. Full parity with the
ZU11EG is a committed goal (roadmap P4/P5/P6), and this page is honest
about what that costs.

## Board summary

- **SoC**: Xilinx Zynq XC7Z035 (Kintex-class fabric, GTX transceivers).
- **RF**: AD9361 — 2R2T, 70 MHz–6 GHz, up to 61.44 MSPS, LVDS CMOS
  interface (no JESD204).
- **Carriers**: ADRV1CRR-BOB (breakout) and ADRV1CRR-FMC (FMC carrier;
  the FMC route exposes GTX lanes — relevant to the offload item below).
- **Timed-tune mechanism**: AD9361 fastlock — 8 stored PLL profiles
  selected by CTRL_IN pins ({doc}`timing-synchronization`).

```{eval-rst}
.. raw:: html
   :file: _static/images/platform-z7035.svg
```

## What exists today

- Stock ADI HDL reference design (`adrv9361z7035`) and Linux support —
  the P2 streaming MVP needs nothing new.
- **No Tick support.** The closest analogue is Tick's ADALM-Pluto port
  (Zynq-7010 + AD9363): same AD936x family, same fastlock CTRL_IN GPIO
  hop mechanism. That port is itself at *integration artifacts* maturity
  — the analogue de-risks the design, not the schedule.
- **No Corundum wrapper** for this board exists anywhere — no ethernet
  PHY wrapper, no board top-level, no pinout.

## New work 1 — Tick port (roadmap P4)

HDL scope, scaled from the Pluto port:

1. Instantiate `axi_timed_command_scheduler` +
   `tick_stream_timestamp_tag` in the `adrv9361z7035` project TCL
   (address assignment following Tick's per-board pattern).
2. Wire `gpio_out[3:0]` → AD9361 CTRL_IN (fastlock profile select);
   board XDC for the chosen carrier's pins.
3. Insert stream gates and the timestamp tagger into the LVDS RX/TX
   datapath; wire `CAPTURE_ARM`/`TRANSMIT_ARM` sync outputs to the
   `data_offload` `sync_ext` inputs.
4. Devicetree node per Tick's binding
   (`adi,axi-timed-command-scheduler-1.0`).

Acceptance criteria (traced in {doc}`requirements-test`):

- driver probes; measured tick rate reported and sane;
- timed-GPIO staircase example passes with scope evidence;
- timed capture (`start_at`) delivers tick-exact first-sample timestamps;
- fastlock hop scan: settling within AD9361 fastlock spec, hops confirmed
  on-time through the completion path.

## New work 2 — network offload path (roadmap P5, highest-risk)

The honest hard part. Z7035 GTX lanes can carry 10GBASE-R, but nothing
is shipped: a Corundum port for this board means a new ethernet wrapper
(PHY on GTX), a board top-level integration, carrier pinout for
SFP/FMC-mounted cages, and resource-fit work in a fabric much smaller
than the ZU11EG's. It is scheduled as its own phase gate and explicitly
allowed to slip without dragging P4 parity ({doc}`roadmap`).

**MVP fallback, stated plainly:** PS GigE carries control and telemetry
(`NET_OFFLOAD_NIC` absent); streaming stays on the DMA path. Every SDK
feature except the two `NET_OFFLOAD_*` capabilities works over the
fallback.

## Capability profile

See the canonical matrix in {doc}`api-object-model`. Summary: streaming
at P2; `TIMED_COMMANDS`/`RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS`/
`FASTLOCK_HOP` at P4; `NET_OFFLOAD_NIC` at P5 (new wrapper);
`NET_OFFLOAD_SAMPLES` at P6, channel/rate subsets only. `FHM_HOP`, `MCS`,
`PHASE_COHERENT` are structurally n/a (single chip).
