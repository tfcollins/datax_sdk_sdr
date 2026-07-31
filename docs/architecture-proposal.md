# Architecture Proposal

## Goal

Build an SDR SDK that turns any supported ADI platform into a **streaming
radiohead**: a stream endpoint with a small set of well-defined,
software-controlled functions — tune, gain, stream on/off, and *timed*
variants of each — behind one libiio-idiomatic C API with Python bindings.
The SDK layers on the stock ADI HDL and Linux IIO stack, adds hard-timed
control through the Tick scheduler IP, and uses Corundum for the
high-speed network plane.

```{eval-rst}
.. raw:: html
   :file: _static/images/sdk-layered-architecture.svg
```

The SDK owns exactly two things: the **mapping** from API calls to the
underlying libiio attributes, Tick descriptors, and DMA buffer operations;
and the **capability model** that tells an application what each platform
can actually do. Everything below the API line is existing, separately
maintained infrastructure.

## Baseline Facts

Upstream projects this proposal builds on:

- Tick scheduler and its architecture proposal:
  <https://tfcollins.github.io/tick/architecture-proposal.html>
- ADI HDL reference designs:
  <https://analogdevicesinc.github.io/hdl/>
- libiio API: <https://analogdevicesinc.github.io/libiio/>
- Corundum NIC: <https://github.com/corundum/corundum>

Baseline constraints the design preserves and states honestly:

- The stock ADI JESD204 / LVDS, AXI-DMAC, `data_offload`, IIO, libiio,
  and pyadi-iio paths remain intact. The SDK adds; it does not fork.
- Tick is validated end-to-end only on AD9081-FMCA-EBZ / ZCU102
  (`hdl_2023_r2`). The ADRV9009-ZU11EG has unvalidated integration
  artifacts; the ADRV9361-Z7035 has no Tick support today.
- `hdl_2026_r1` / Vivado 2025.1 carries an open cache-coherency
  regression (fix in flight, hardware-unconfirmed). The ZU11EG Corundum
  variant needs `hdl_2026_r1`; Tick's validated base is `hdl_2023_r2`.
  This fork is a named decision gate in the {doc}`roadmap`.
- Corundum in the upstream ZU11EG design is a QSFP+ 10 Gb/s **NIC**
  parallel to the JESD datapath — not a sample transport.
- The Tick Linux driver submits one descriptor per sysfs attribute write
  and polls a one-entry completion window. The API is shaped so this
  bottleneck is hidden today and replaceable tomorrow
  (see {doc}`api-c-core`).

## The Radiohead Model

The central abstraction: the radio is a **streaming endpoint plus a
scheduler**, and the application never touches the machinery in between.

What the application sees:

- streams (`rx`, `tx`) that produce/consume timestamped sample blocks and
  can start *now* or *at a device time*;
- radio functions (frequency, gain, sample rate, bandwidth, port) that
  apply *now* or *at a device time*;
- a device-time clock it can read and align to PPS;
- capability flags that say which of the above are hard-timed on this
  platform.

What the SDK deliberately hides:

- AD936x fastlock profile table programming and CTRL_IN bit wiggling;
- ADRV9009 Talise FHM setup and ARM GPIO trigger configuration;
- IIO sysfs attribute paths, device/channel name lookup, and the Tick
  descriptor CSV submission format;
- `data_offload` arming, `sync_ext` release, and DMA buffer lifecycle
  mechanics.

Every hidden mechanism keeps its raw libiio escape hatch — hiding is a
default, not a wall.

## Layered Architecture

Walking the figure above, top to bottom:

**Host applications** — user code in C or Python, plus stock tooling
(`iio_attr`, IIO Oscilloscope) which continues to work unchanged beside
the SDK.

**libdatax + bindings** — the C core (`datax_context`, `datax_device`,
`datax_stream`, `datax_sched`, `datax_caps` — see
{doc}`api-object-model`) and its Python package. Runs on a remote host
(libiio network backend) or directly on the SoC (local backend); the only
difference is the context URI.

**Linux middleware** — unmodified existing drivers: libiio/iiod, the
converter drivers (ad9361, adrv9009), the Tick IIO scheduler driver, the
AXI-DMAC framework, and (where fitted) the Corundum `mqnic` netdev.

**FPGA fabric** — the stock reference design (JESD204 or LVDS link layer,
`util_cpack`/`upack`, `data_offload`, `axi_dmac`) plus the Tick
`axi_timed_command_scheduler` and `tick_stream_timestamp_tag` IPs, and on
network-fitted builds the Corundum NIC core. The future VITA-49
packetizer sits in Corundum's application section (dashed in the figure —
roadmap, not MVP).

**RF** — AD9361 (2R2T, LVDS) on the Z7035; dual ADRV9009 (JESD204B) with
HMC7044 clocking on the ZU11EG.

## Control Plane

Everything is libiio underneath. The SDK's control plane is a mapping
layer with three tiers:

1. **Immediate controls** — `datax_device_set_frequency()` et al. resolve
   to attribute writes on the right IIO device/channel, using compiled-in
   per-platform attribute maps.
2. **Timed controls** — the same calls with a time argument become Tick
   descriptors: hard-timed where fabric targets exist (stream gates,
   GPIO-selected fastlock/FHM hops), pre-staged where the converter needs
   state loaded ahead of the trigger. The scheduler object batches
   descriptors and manages completions ({doc}`api-c-core`).
3. **Capability discovery** — a compiled per-platform capability table,
   refined at `datax_context` creation by probing the live IIO context
   (is a Tick device present? a `data_offload` with `sync_ext`? an
   `mqnic`?). Applications branch on flags, never on board names.

## Data Plane (MVP)

Samples move exactly as they do in the stock designs: converter ↔ link
layer ↔ pack/unpack ↔ `data_offload` ↔ `axi_dmac` ↔ IIO buffer. The SDK
adds two things on top (detailed in {doc}`streaming-model`):

- **Timed start** — `datax_stream_start_at(t)` pre-arms the buffer and
  schedules a Tick `CAPTURE_ARM`/`TRANSMIT_ARM`, which releases the
  armed `data_offload` via its `sync_ext` input at tick T. (The
  `axi_dmac` itself has no trigger input — arming semantics are the
  contract, and they are stated explicitly in the API.)
- **In-band timestamps** — the Tick stream tagger prepends a device-time
  header to capture buffers, so received blocks carry their capture time.

RX and TX MVP datapaths:

```{mermaid}
graph LR
    ADC[Converter RX] --> LINK[Link layer<br/>JESD204B / LVDS]
    LINK --> CPACK[util_cpack] --> TAG[tick_stream<br/>timestamp_tag] --> OFFL[data_offload<br/>arm / sync_ext] --> DMAC[axi_dmac] --> BUF[IIO buffer] --> STR[datax_stream recv]
    SCHED[Tick scheduler] -. "CAPTURE_ARM @ T" .-> OFFL
```

```{mermaid}
graph RL
    STR[datax_stream send] --> BUF[IIO buffer<br/>cyclic or one-shot] --> DMAC[axi_dmac] --> OFFL[data_offload<br/>arm / sync_ext] --> UPACK[util_upack] --> LINK[Link layer<br/>JESD204B / LVDS] --> DAC[Converter TX]
    SCHED[Tick scheduler] -. "TRANSMIT_ARM @ T" .-> OFFL
```

## Data Plane (Roadmap: RF sample offload)

The "radiohead over the network" end state: a packetizer in Corundum's
application section takes tagged samples straight from fabric, wraps them
in VITA-49-style frames carrying device timestamps, and sources them into
the NIC datapath — the host receives line-rate sample streams on a
standard (or DPDK-accelerated) network stack, with the PS DDR bounce
removed.

This is deliberately **not** in the MVP. The arithmetic: 2 channels of
16-bit I/Q at 61.44 MSPS, RX+TX, is ≈ 7.86 Gb/s before framing overhead —
marginal on one 10 G link, and that is the *smaller* platform's native
rate. The phase gates, header budget, and per-platform channel limits are
worked in {doc}`streaming-model`; the Corundum-side scope is in the
platform pages.

In the MVP, Corundum-fitted builds still earn their place: the NIC is the
control and telemetry plane (remote iiod sessions, event/telemetry
streams, PTP-capable hardware for a later timing phase) running parallel
to DMA streaming.

## Software Client Model

Restating the load-bearing API decision: **C core + Python bindings**,
libiio-idiomatic throughout — opaque handles, create/destroy pairs,
integer error returns, `_get_`/`_set_` accessors. The Python layer mirrors
pyadi-iio idioms (`dev.rx_lo = 2.4e9`) and adds a fluent timed-command
builder (`sched.at(t).tune(...)`). The full object model is specified in
{doc}`api-object-model`, the C surface in {doc}`api-c-core`, and the
Python surface in {doc}`api-python`.

## Phases

Authoring and delivery run P0 (this site) through P6 (RF-sample offload),
with explicit gates on Tick hardware-validation milestones and the
`hdl_2023_r2` / `hdl_2026_r1` decision. See {doc}`roadmap`.

## Non-Goals

No UHD compatibility shim, no PTP in v1, no per-sample command
granularity, Linux hosts only, two platforms only. See {doc}`non-goals`.
