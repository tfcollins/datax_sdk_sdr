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
  `tick_stream_timestamp_tag`, each capture carries a device-time header;
  the SDK strips it and delivers `{samples, timestamp}`.

Expected sustained rates (estimates, to be replaced by measured numbers
per {doc}`requirements-test` evidence):

| Platform | Native rate | MVP path bound |
|---|---|---|
| ADRV9361-Z7035 | 2R2T × 61.44 MSPS (LVDS) | Zynq-7000 HP ports / DDR3 — full native rate is a burst-capture use case, sustained streaming is host-link bound (GigE) |
| ADRV9009-ZU11EG | 4R4T × 245.76 MSPS (JESD204B) | PS DDR4 and RPU/APU memory bandwidth — fabric can source far more than the PS can sink sustained |

The gap between native and sustained rates is exactly why the offload
roadmap exists.

## Timed start: arm/release semantics

The `axi_dmac` has **no trigger input**. Timed capture and transmit work
by *arming early and releasing exactly*:

1. the SDK enqueues and starts the DMA transfer — samples do not flow yet
   because the `data_offload` block in front of it holds;
2. a Tick `CAPTURE_ARM` / `TRANSMIT_ARM` descriptor, queued for tick T,
   pulses the offload's `sync_ext` input at T;
3. the offload releases, and the first sample through carries device time
   T (tagged in-band when the tagger is present).

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant Drv as Tick IIO driver
    participant OFFL as data_offload
    participant DMA as axi_dmac

    App->>SDK: stream_start_at(T)
    SDK->>DMA: enqueue + start buffers (pre-arm)
    SDK->>Drv: batched descriptor writes (CAPTURE_ARM @ T)
    Note over OFFL: holds — no samples flow
    Drv-->>OFFL: sync_ext pulse at tick T (fabric)
    OFFL->>DMA: samples flow, first sample = T
    DMA-->>SDK: filled block via IIO buffer
    SDK-->>App: recv() → {samples, timestamp T}
```

The contract, stated bluntly in the API docs:

- buffers **must** be armed before T; the SDK enforces a configurable
  guard margin and reports `DATAX_ERR_LATE` if T is inside it;
- if the arm descriptor goes late in the queue (Tick's late detection),
  the stream start fails loudly through the completion path — never a
  silently-shifted capture;
- an armed-but-never-released offload (T unreachable, e.g. time
  realigned) must be cancelable: `datax_stream_stop()` tears down the
  arm and flushes the descriptor.

Failure modes and their surfaced errors:

| Failure | Surface |
|---|---|
| T already past at submit | `DATAX_ERR_LATE` from `stream_start_at` |
| Arm descriptor late at dispatch | `DATAX_EVT_LATE_COMMAND` + stream start error |
| Offload FIFO overflow before release (RX) | `DATAX_EVT_OVERFLOW`, block marked discontinuous |
| Host too slow draining (RX) | standard IIO overflow accounting, surfaced per-block |

## Gated streaming

`STREAM_GATE` descriptors latch a fabric enable on tick boundaries. The
SDK exposes this as schedulable gate windows on a running stream —
`sched.at(t1).gate_on(stream)`, `.at(t2).gate_off(stream)` — the building
block for TDD frames and burst duty cycles. `TDD_SYNC` alignment of an
`axi_tdd` instance (where fitted) rides the same mechanism.

## Roadmap: Corundum RF-sample offload

The end state moves samples fabric → Ethernet without touching PS DDR: a
packetizer in Corundum's application section consumes tagged samples and
sources VITA-49-style frames (device timestamp, stream ID, sequence
numbers) into the NIC datapath.

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
- Z7035 GTX lanes top out lower and the board has no shipped Corundum
  wrapper at all — its offload story is bounded to subsets from day one
  ({doc}`platform-adrv9361-z7035`).

Header budget target: ≤ 2% overhead at 8k-sample payloads — one VRT-style
header per packet, jumbo frames assumed on the point-to-point link.

**What Corundum does in the MVP, meanwhile:** the NIC is the control and
telemetry plane — remote iiod over the fabric NIC, SDK event/telemetry
streams, and a PTP-capable substrate for a post-v1 timing phase. Sample
data stays on the DMA path until the packetizer phase clears its gates in
the {doc}`roadmap`.
