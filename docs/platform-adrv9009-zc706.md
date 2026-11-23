# Platform: ADRV9009 on ZC706

*Reference.* A single ADRV9009 (Talise) evaluation board, ADRV9009-W/PCBZ, on
the Xilinx ZC706 (Zynq-7045). The stock ADI reference design is enough for SDK
streaming. libdatax drives it with the same `adrv9009` device family as the
ZU11EG, so it is the cheaper of the two ADRV9009 boards for streaming work.
Timed control is not available on it yet. Labgrid place: `nemo`.

## Board summary

- **SoC**: Xilinx Zynq-7000 XC7Z045 (ZC706 evaluation kit).
- **RF**: one ADRV9009: 2R2T (plus an observation receiver), JESD204B. The
  stock project's links are RX M=4 L=2, TX M=4 L=4, RX_OS M=2 L=2.
- **Timed-tune mechanism**: Talise FHM ({doc}`timing-synchronization`), but
  only once Tick is in the PL (see below).
- **Not on this board**: multi-chip sync and phase coherence (single chip),
  and a 10G network sample path (no Corundum or vrt49 design targets it).

## What exists today

- **Immediate RX/TX streaming through libdatax, validated 2026-11-23.** The
  `kuiper` leg of libdatax `hw-test.yml` asks labgrid for part `adrv9009` on
  carrier `zc706`. labgrid boots the stock Kuiper 2023_R2_P1 image, and the
  hardware suite passes 10 tests and skips 15 (the timed-control tests). That
  covers RX on both channels, receive-timeout recovery, one-shot and cyclic
  TX, start/stop cycles, and digital loopback bit-exact on ch0 and ch1. The
  loopback has I and Q exchanged and unit gain, the same framer loopback as
  the ZU11EG. Evidence:
  [libdatax docs/evidence/ci/2026-11-23-zc706](https://github.com/tfcollins/libdatax/blob/main/docs/evidence/ci/2026-11-23-zc706/README.md).
- **Tick on this board (integration artifacts).** Tick's scheduler was built
  into `projects/adrv9009/zc706` and validated by hand: the driver probed, the
  measured timebase was 99.9975 MHz, and the timed-GPIO staircase executed on
  exact ticks. No CI workflow targets it, so the row stays at *integration
  artifacts*. The Talise FHM hop on this board is *planned* in tick. See Tick's
  [ADRV9009 on ZC706](https://tfcollins.github.io/tick/adrv9009-zc706-hop.html)
  page.
- libdatax's timed control (P3a) has not run here. The stock PL has no Tick,
  and no SDK image with Tick exists for this board.

## Runbook

The step-by-step version, with the exact commands and the known-good versions
table, is in libdatax
[docs/hardware.md](https://github.com/tfcollins/libdatax/blob/main/docs/hardware.md)
("ADRV9009 on ZC706").

1. **Image.** Kuiper 2023_R2_P1 on the ZC706's SD card. Set up its boot
   partition: copy `BOOT.BIN` and `devicetree.dtb` from the
   `zynq-zc706-adv7511-adrv9009` folder and `uImage` from `zynq-common` to the
   partition's root. The board then autoboots from SD on power-on. No custom
   bitstream is needed.
2. **Known-good versions** (from the validating run): PL `hdl_2023_r2`
   (`2156ac7e`), kernel `6.1.70-284114-g2e8908932dfd`, stock iiod
   `0.26-5e1e9cb`, and host libiio the pinned v1 fork (libdatax `pins.json`).
3. **Boot and run in the lab.** Dispatch libdatax `hw-test.yml` with
   `place=zc706`. Or run `scripts/hw/kuiper-run.sh zc706 adrv9009 zc706 <out>`
   from a host that can reach the labgrid coordinator. labgrid powers the
   board, waits for the SD autoboot and exports the IIO URI, and the script runs
   the suite against it.
4. **Run by hand.** Boot the board, set `DATAX_HW_URI=ip:<board>` and
   `DATAX_HW_IMAGE=stock`, then run `python -m pytest tests/hardware`.
5. **Expected result.** 10 passed and 15 skipped. RX throughput over `ip:`
   (about 32 MB/s on 2026-11-23) and the RX overflow count are recorded, not
   asserted. Overflows during the 10 s pull are expected, because iiod's TCP
   path is far slower than the converter.
6. **Evidence.** Each run writes `evidence-zc706.json` and
   `junit-zc706.xml`, redacted on the runner, and uploads them as the run's
   artifact.

## Capability profile

The canonical matrix is in {doc}`api-object-model`. On this board, with the
stock image:

- **validated**: streaming (immediate RX and TX), digital loopback.
- **integration artifacts**: `TIMED_COMMANDS` infrastructure (Tick, by hand).
- **planned**: `FHM_HOP` (needs Tick in the PL and the FHM trigger).
- **n/a**: `MCS` and `PHASE_COHERENT` (single chip), `FASTLOCK_HOP` (no
  AD936x), `NET_OFFLOAD_*` (no network sample path).

Per-row status and evidence: {doc}`support-matrix`.
