# Platform: ADRV9361-Z7035

Zynq-7035 + AD9361 SOM. The smaller target. Tick and a 1G VITA 49.2
path already exist for it in vrt49; the remaining work is RF
qualification and the SDK's timed surface. Full parity with the ZU11EG is a
committed goal (roadmap P4/P5/P6), and this page is honest about what
that costs.

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

- Stock ADI HDL reference design (`adrv9361z7035`) and Linux support:
  libdatax streaming needs nothing new. **Immediate RX/TX streaming
  validated 2026-11-23** by the `kuiper` leg of libdatax `hw-test.yml` on
  `lablp`. labgrid boots the stock Kuiper 2023_R2_P1 image
  (`adrv9361z7035_ccfmc`, LVDS, `hdl_2023_r2`). The hardware suite passes 10
  tests and skips 15 (the timed-control tests). Digital loopback
  (`ad9361-phy` debug `loopback`=1) is bit-exact as TX >> 4 on both
  channels. RX throughput over `ip:` and DMA overflows (read from the RX
  core's status register) are recorded, not asserted: about 34 MB/s with
  overflows in that run, 41–47 MB/s in the controller-run P2 sessions of
  2026-11-05. Evidence:
  [libdatax docs/evidence/ci/2026-11-23-lablp](https://github.com/tfcollins/libdatax/blob/main/docs/evidence/ci/2026-11-23-lablp/README.md)
  and [docs/evidence/p2](https://github.com/tfcollins/libdatax/tree/main/docs/evidence/p2).
- **Tick in the vrt49 1G SFP design** (`adrv9361z7035_vrt49_sfp`): the
  vendored `axi_timed_command_scheduler`, and `vrt49_ad9361_hop_ctrl`
  at `0x44AB0000` driving the AD9361 `fastlock_select` pins from
  `gpio_out` and gating the framer's sample admission, with hop
  metadata (frequency, epoch) carried in Context packets.
  `adrv9361_tick_hop.py` preloads a fastlock bank of at most eight
  frequencies and submits absolute-time GPIO events. `pps_in` is tied
  low, so Tick time is reset-relative only. See the vrt49
  [Tick hop tutorial](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md)
  (private repository).
- **Evidence boundary, stated by vrt49**: control and Context/IQ
  transport passed qualification on hardware; an independent
  RF-measured hop settle has **not** been established. Status:
  *integration artifacts*.
- **1G SFP network path** (1000BASE-X; at 61.44 MSPS the
  `vrt49_frame_throttle` forwards one frame in three, about 0.68 Gb/s
  on the wire; GPSDO 1PPS timestamping) and a CCFMC LVDS variant
  to host DMA. There is no Corundum port for this board and no 10G
  path. See the vrt49
  [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9361z7035_sfp.md)
  (private repository).

## Runbook

This section covers SDK streaming on the stock image. The step-by-step version,
with the exact commands and the known-good versions table, is in libdatax
[docs/hardware.md](https://github.com/tfcollins/libdatax/blob/main/docs/hardware.md)
("ADRV9361-Z7035 on ADRV1CRR-FMC"). The vrt49 SFP image is covered by
vrt49's [Tick hop tutorial](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md)
(private repository).

1. **Image.** Kuiper 2023_R2_P1 on the SOM's SD card. Set up its boot
   partition from the `zynq-adrv9361-z7035-fmc` folder. The board autoboots
   from SD on power-on, which takes about 3 minutes.
2. **Known-good versions** (from the validating run): PL `hdl_2023_r2`
   (`2156ac7e`, `adrv9361z7035_ccfmc`, LVDS), kernel
   `6.1.70-284114-g2e8908932dfd`, stock iiod `0.26-5e1e9cb`, and host libiio
   the pinned v1 fork (libdatax `pins.json`). The fork talks to the stock v0
   iiod unchanged.
3. **Boot and run in the lab.** Dispatch libdatax `hw-test.yml` with
   `place=lablp`. Or run
   `scripts/hw/kuiper-run.sh lablp adrv9361z7035 adrv1crr-fmc <out>`, which
   asks labgrid for part `adrv9361z7035` on carrier `adrv1crr-fmc`.
4. **Run by hand.** Boot the board, set `DATAX_HW_URI=ip:<board>` and
   `DATAX_HW_IMAGE=stock`, then run `python -m pytest tests/hardware`.
5. **Expected result.** 10 passed and 15 skipped.
6. **Known quirk.** The ADRV1CRR-FMC's USB console (CP2103) is powered by the
   board, so it appears only a few seconds after power-on. labgrid-plugins
   `ec8bf30` and later reconnect a console that drops then; libdatax pins it.
   An older pin fails the first boot with "Broken pipe".

## Remaining Tick work (roadmap P4)

What vrt49 does not yet provide:

1. RF-measured fastlock settle (REQ-TEST-031) with scope or spectrum
   evidence.
2. `tick_stream_timestamp_tag` and `CAPTURE_ARM`/`TRANSMIT_ARM` wiring
   to the `data_offload` `sync_ext` inputs, so the DMA path has the
   same `RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS` semantics as the
   ZU11EG — or a decision that the VRT framer path is the SDK's
   streaming path on this board.
3. An external PPS route for `pps_in`.
4. The runbook (REQ-DOC-004).

Acceptance criteria (traced in {doc}`requirements-test`):

- driver probes; measured tick rate reported and sane;
- timed-GPIO staircase example passes with scope evidence;
- timed capture (`start_at`) delivers tick-exact first-sample timestamps;
- fastlock hop scan: settling within AD9361 fastlock spec, hops confirmed
  on-time through the completion path.

## 10G offload path (roadmap P5, still highest-risk)

The honest hard part. The 1G SFP path is shipped and forwards one
frame in three at 61.44 MSPS (about 0.68 Gb/s on the wire); 10G on the
FMC carrier's GTX lanes is the unshipped part. Z7035 GTX lanes can carry 10GBASE-R, but a Corundum
port for this board means a new ethernet wrapper (PHY on GTX), a board
top-level integration, carrier pinout for SFP/FMC-mounted cages, and
resource-fit work in a fabric much smaller than the ZU11EG's. It is
scheduled as its own phase gate and explicitly allowed to slip without
dragging P4 parity ({doc}`roadmap`).

**MVP fallback, stated plainly:** PS GigE carries control and telemetry
(`NET_OFFLOAD_NIC` absent); streaming stays on the DMA path. Every SDK
feature except the two `NET_OFFLOAD_*` capabilities works over the
fallback.

## Capability profile

See the canonical matrix in {doc}`api-object-model`. Summary: streaming
at P2 (validated); `TIMED_COMMANDS`/`RX_ARM`/`TX_ARM`/`STREAM_GATE`/`TIMESTAMPS`/
`FASTLOCK_HOP` at P4; `NET_OFFLOAD_NIC` at P5 (new wrapper);
`NET_OFFLOAD_SAMPLES` at P6, channel/rate subsets only. `FHM_HOP`, `MCS`,
`PHASE_COHERENT` are structurally n/a (single chip). Infrastructure
status per row is in {doc}`support-matrix`: `TIMED_COMMANDS` and
`FASTLOCK_HOP` infrastructure is at *integration artifacts*; the
DMA-path gate and timestamp rows have no infrastructure yet.
