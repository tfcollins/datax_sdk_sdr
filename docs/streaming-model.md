# Streaming Model

The data plane, from the radiohead abstraction down to DMA mechanics —
and the honest arithmetic behind phasing the Corundum RF-sample offload.

## The streaming radiohead

An application sees a radio as:

- one or more **streams** — RX streams produce timestamped sample blocks,
  TX streams consume them;
- **stream lifecycle** — create (direction, channel mask, buffer
  geometry) → start *now* or *at device time T* → recv/send → stop →
  destroy;
- **gating** — a running stream can be gated on and off at exact device
  times for burst and TDD patterns;
- **no DMA vocabulary** — buffers, offload engines, and arming mechanics
  are the SDK's problem.

Control is *asynchronous but schedulable*: the control plane
({doc}`architecture-proposal`) can change radio state while streams run,
immediately or at a scheduled time.

## MVP datapath: AXI-DMAC + libiio

Samples move through the stock reference-design path — converter ↔ link
layer ↔ `util_cpack`/`upack` ↔ `data_offload` ↔ `axi_dmac` ↔ IIO buffer
(the diagrams are in {doc}`architecture-proposal`). The SDK's stream
object wraps the libiio buffer API:

- **Buffer geometry** — block size and count chosen at stream creation;
  defaults sized per platform (the capability table carries DMA and DDR
  bandwidth notes).
- **RX** — `datax_stream_recv()` blocks (with timeout) for the next
  filled block; zero-copy get/put variants expose the mapped buffer.
- **TX** — one-shot blocks or cyclic mode (waveform repeats from fabric
  memory without host involvement — the stock ADI cyclic-buffer path).
- **In-band timestamps** — when the design includes
  `tick_stream_timestamp_tag`, block 0 of each timed release carries a
  device-time header; the SDK strips it, reduces `valid_samples` by the
  overwritten samples and delivers `{samples, timestamp}`. Later blocks
  are derived from block 0 (see {doc}`api-c-core`).

Expected sustained rates (estimates, to be replaced by measured numbers
per {doc}`requirements-test` evidence):

| Platform | Native rate | MVP path bound |
|---|---|---|
| ADRV9361-Z7035 | 2R2T × 61.44 MSPS (LVDS) | Zynq-7000 HP ports / DDR3 — full native rate is a burst-capture use case, sustained streaming is host-link bound (GigE) |
| ADRV9009-ZU11EG | 4R4T × 245.76 MSPS (JESD204B) | PS DDR4 and RPU/APU memory bandwidth — fabric can source far more than the PS can sink sustained |

The gap between native and sustained rates is exactly why the offload
roadmap exists.

## Timed start: per-board mechanism

The `axi_dmac` has **no trigger input**, so a timed start is always some
fabric element in front of (RX) or behind (TX) the DMA that is closed
while the DMA is armed and opened exactly at tick T. The element differs
per board. *This section describes planned P3b behaviour; until it ships,
`datax_stream_start_at()` returns `-ENOTSUP`.*

| Board | RX mechanism | TX mechanism |
|---|---|---|
| ADRV9009-ZU11EG | Tick `STREAM_GATE` level drives a fabric gate between the TPL outputs and `util_cpack`; a oneshot tagger on RX block 0 | the same level drives a gate after `axi_tx_fifo` (before `util_upack` and the DAC TPL) |
| AD9081 (ZCU102) | `data_offload` armed, released by a Tick `CAPTURE_ARM` pulse on `sync_ext` | `data_offload` armed by `TRANSMIT_ARM` |

No ADRV9009 design has a `data_offload`, and on RX it is a bounded burst
store that cannot start a continuous stream at T and keep it running. The
ZU11EG therefore uses the gate; the arm commands are not used on that
board.

### ZU11EG: STREAM_GATE and the DMA gate

Tick's `STREAM_GATE` command sets or clears a latched level bit. Two such
bits per direction drive one fabric gate (`tick_dma_gate`): a **level**
(1 = pass) and a **mode** bit (0 = forced open, the reset state).
`pass = !mode | level`, evaluated in the device clock after a two-flop
clock-domain crossing.

- **Reset is open.** With every bit at 0 the image streams exactly like
  the stock design, so an untimed client (iio-oscilloscope, pyadi-iio, a
  P2-era libdatax) sees no difference.
- **RX gate.** While closed it holds cpack's write enable low, and only
  that pin, so the TPL's other consumers are untouched. It also holds
  cpack in reset, so channel alignment restarts cleanly on opening. Samples
  during a closed gate are discarded in fabric; that is not an overflow.
- **TX gate.** Before a `start_at` release it holds the TX FIFO's reads,
  so the first sample on the DAC is the buffer's first. Later closures
  **mute**: reads continue and the DAC gets zeros (mid-scale), so a
  cyclic buffer stays time-aligned. A true pause behind the DDR
  `axi_dacfifo` corrupts samples (spike G2, 2026-11-24).
- **Tagger.** Tick's `tick_stream_timestamp_tag`, in oneshot mode behind a
  FIFO-interface adapter, overwrites the first 32 bytes of RX block 0 of
  each release with a header carrying the tick latched when the opening
  `STREAM_GATE` executed (T, for an on-time command).

**Latency bound.** The tick clock (100 MHz) and the device clock are
asynchronous, so the gate opens at a fixed CDC latency, plus or minus one
device clock, after tick T. The bound is measured on `tron` before the
capability flips.

### Start sequence

`start_at(T)` is "close, arm the DMA, open at T":

1. write execute-now commands that set the direction's mode bit and clear
   its level (exempt from the guard margin) and wait for their completions;
2. open the IIO buffer and enqueue every RX block, or load the TX data;
3. commit the opening `STREAM_GATE` at T, late-drop, with a completion.

The stream is `started` at once; `recv` blocks until data arrives.

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant Drv as Tick IIO driver
    participant GATE as DMA gate (fabric)
    participant DMA as axi_dmac

    App->>SDK: stream_start_at(T)
    SDK->>Drv: execute-now STREAM_GATE: mode=1, level=0
    SDK->>DMA: enqueue + start buffers (pre-arm)
    SDK->>Drv: STREAM_GATE level=1 @ T
    Note over GATE: closed — no samples reach the DMA
    Drv-->>GATE: level rises at tick T (fabric)
    GATE->>DMA: samples flow, first sample = T (+ fixed CDC latency, ±1 device clock)
    DMA-->>SDK: block 0 carries the 32-byte tag
    SDK-->>App: recv() → {samples, timestamp T}
```

The contract, stated bluntly in the API docs:

- buffers **must** be armed before T; the SDK enforces a configurable
  guard margin and reports `DATAX_ERR_LATE` if T is inside it;
- if the opening command is late at dispatch (Tick's late detection), the
  stream is marked failed and `recv`/`send` return `DATAX_ERR_LATE` — never
  a silently-shifted capture;
- an armed-but-never-opened stream (T unreachable, e.g. time realigned)
  must be cancelable: `datax_stream_stop()` flushes the pending opening
  command and forces the gate open (mode 0), so a later untimed `start()`
  finds it open.

Failure modes and their surfaced errors:

| Failure | Surface |
|---|---|
| T already past or inside the guard margin at submit | `DATAX_ERR_LATE` from `stream_start_at` |
| Opening command late at dispatch | `DATAX_EVT_LATE_COMMAND`; stream failed; `DATAX_ERR_LATE` from `recv`/`send` |
| DMA overflow (RX) | `DATAX_EVT_STREAM_OVERFLOW`; block marked discontinuous; timestamps read 0 until the next `start_at` |
| TX underflow | `DATAX_EVT_STREAM_UNDERFLOW` |
| Host too slow draining (RX) | standard IIO overflow accounting, surfaced per-block |

## Gated streaming

`STREAM_GATE` descriptors latch a fabric enable on tick boundaries. The
SDK exposes this as schedulable gate windows on a running stream that was
started with `start_at` —
`sched.at(t1).gate_on(stream)`, `.at(t2).gate_off(stream)` — the building
block for TDD frames and burst duty cycles. `TDD_SYNC` alignment of an
`axi_tdd` instance (where fitted) rides the same mechanism.

## RF-sample offload (vrt49 today, SDK surface on the roadmap)

The end state moves samples fabric → Ethernet without touching PS DDR: a
packetizer in Corundum's application section consumes tagged samples and
sources VITA-49-style frames (device timestamp, stream ID, sequence
numbers) into the NIC datapath. vrt49's `axi_vrt49_framer` implements
this on the ZU11EG and hopcap exercises it; the figure and the datapath
pages below remain the block-level description.

```{eval-rst}
.. raw:: html
   :file: _static/images/corundum-vita49-offload.svg
```

The block-level walk of this pipeline — every stage, its control
surface, and the clock domains — is on its own pages:
{doc}`hdl-datapath-corundum` (RX) and {doc}`hdl-datapath-corundum-tx`
(TX).

The bandwidth arithmetic that gates this phase:

- 2 ch × 61.44 MSPS × 32 bit I/Q = 3.93 Gb/s one direction; RX+TX ≈
  **7.86 Gb/s** — before Ethernet/IP/UDP/VRT headers, on one 10 G link.
  That is the *smaller* platform's native rate.
- ZU11EG native (4 ch × 245.76 MSPS) is ≈ 31.5 Gb/s per direction — far
  beyond a single 10 G port. Mitigations, in design order: channel/rate
  subsets, sample-width packing (12/8-bit modes), and the QSFP+ cage's
  4-lane / 25 G-per-lane headroom (a Corundum-side project of its own).
- Z7035 GTX lanes top out lower; the shipped path is vrt49's 1G SFP
  design, which at 61.44 MSPS forwards one frame in three (about
  0.68 Gb/s on the wire), with no 10G — its offload story is bounded
  to subsets from day one ({doc}`platform-adrv9361-z7035`).

Header budget target: ≤ 2 % overhead — met at 0.9 % with the standard
2048-sample payload on a jumbo-frame point-to-point link; the frame
layout is specified in {doc}`vrt-frame-format`.

**What Corundum does in the MVP, meanwhile:** the NIC is the control and
telemetry plane — remote iiod over the fabric NIC, SDK event/telemetry
streams, and a PTP-capable substrate for a post-v1 timing phase. Sample
data moves on either path; the SDK's P6 exit in the {doc}`roadmap` is
the `libdatax` surface over the vrt49 path.
