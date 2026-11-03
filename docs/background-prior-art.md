# Background and Prior Art

Why layer another SDK over a stack that already works? Because the two
ecosystems SDR developers actually use each solve half of the problem.

## The UHD timing model

UHD (the USRP Hardware Driver) established the API vocabulary that most SDR
software assumes:

- **Timed commands** — `set_command_time()` stamps every subsequent control
  call (tune, gain, antenna, GPIO) with a future execution time; the radio
  queues and fires them on its own clock.
- **`set_time_next_pps()`** — device time is aligned to a shared PPS edge, so
  multiple radios agree on "now" to within a sample period.
- **Stream commands** — `stream_cmd_t` with `time_spec` starts or stops
  RX/TX at an exact device time.
- **VITA-49 framing** — every sample packet carries a device timestamp, so
  the host knows exactly when each buffer was captured.

This is what makes multi-channel alignment, frequency-hop schedules, TDD
frames, and repeatable captures one-liners in UHD-based applications. The
caveats are well known: late commands execute immediately and silently, the
radio-side queue is finite, and only some operations are timeable — but the
model is the de-facto standard.

## The libiio model and its limits

libiio exposes ADI devices through contexts, devices, channels, attributes,
and buffers. It is an excellent instrumentation transport:

- One C API — the same application code runs locally on the SoC, over
  Ethernet, or over USB; only the context URI changes.
- Buffer-based streaming through AXI-DMAC with zero-copy paths.
- Every device knob is a readable/writable attribute.

But for SDR-style operation the gaps are structural:

- **Control writes are immediate.** An attribute write lands whenever Linux
  scheduling lets it land. There is no per-command time tag.
- **No scheduled-start primitive.** A buffer starts filling when the DMA is
  enabled, not at a device-time edge.
- **Timestamps are an afterthought.** Nothing in the stock datapath stamps
  buffers with device time.

Synchronously tuning N devices to within a sample period — direct in UHD —
requires building the primitive yourself on host-side timing, which Linux
jitter makes unreliable below the millisecond range.

## Tick: the missing primitive

[Tick](https://tfcollins.github.io/tick/) moves that primitive into FPGA
fabric. Its `axi_timed_command_scheduler` IP adds to a stock ADI HDL design:

- a **64-bit device-time counter** (100 MHz baseline tick rate), disciplined
  by PPS + 10 MHz, alignable on a PPS edge;
- a **timestamp-ordered command FIFO** — commands fire when
  `timestamp_ticks <= device_time_ticks`, bounded by the fabric clock
  period, not Linux jitter;
- **hard-timed targets** wired directly in fabric: GPIO writes, marker
  pulses, stream gates, TDD sync;
- late- and overflow-detection counters, so a missed deadline is an
  observable error rather than a silent misfire.

Commands fall into three classes, a taxonomy this SDK adopts wholesale:

| Class | Guarantee | Examples |
|---|---|---|
| Hard-timed | Fires on an exact device-time tick, in fabric | GPIO, marker, stream gate, TDD sync, capture/transmit arm |
| Pre-staged | Software stages state early; a hard-timed trigger applies it | AD936x fastlock profile select, ADRV9009 FHM hop |
| Software-timed | Best-effort, jitter-bounded by Linux | ordinary attribute writes |

A single fixed **48-byte descriptor** wire format is shared by Tick's Python
model, iverilog testbench, RTL, Linux IIO driver, and libiio clients — the
contract this SDK builds on.

Tick's current maturity matters to this plan and is stated honestly
throughout: the full path is validated end-to-end on AD9081-FMCA-EBZ /
ZCU102 and on the ADRV9009-ZU11EG (scheduler and timed FHM hop); on the
ADRV9361-Z7035 Tick ships inside vrt49's 1G SFP design at
integration-artifacts maturity. See {doc}`support-matrix`, the platform
pages and {doc}`roadmap`.

## Corundum: the network plane

[Corundum](https://github.com/corundum/corundum) is an open-source
FPGA-based NIC: thousands of hardware queues in BRAM, a replaceable
transmit scheduler, native IEEE 1588 PTP, a Linux `mqnic` netdev driver,
and — most interesting here — an **application section** in the datapath
where custom logic can source and sink packets.

The upstream ADI HDL tree already ships a Corundum variant for the
ADRV9009-ZU11EG (`make CORUNDUM=1`): a QSFP+ 10 Gb/s NIC alongside the
JESD204 datapath. Today that is a *network interface*, not a sample
transport — the JESD samples still move through AXI-DMAC into PS DDR. The
SDK treats it accordingly: in the MVP, Corundum is the control/telemetry
plane (remote iiod, event streams); direct RF-sample packetization through
the Corundum application section is a designed-but-later roadmap phase.
The bandwidth arithmetic that forces this phasing is worked through in
{doc}`streaming-model`.

The composition in one picture — three proven pieces, one new layer:

```{mermaid}
graph TD
    APP[application — C or Python]
    APP --> LD[libdatax —<br/>one radiohead API]
    LD --> IIO[libiio<br/>transport + control]
    LD --> TICK[Tick<br/>FPGA-resident timed commands]
    LD --> COR[Corundum<br/>network plane]
    IIO -.->|iio_context escape hatch,<br/>always available| APP
```

## Positioning

| | UHD | libiio + pyadi-iio | **DataX SDR SDK** |
|---|---|---|---|
| Timed control | Per-command time tags | Immediate writes only | Tick descriptors behind `sched.at(t)` |
| Scheduled stream start | `stream_cmd_t` + time_spec | None | `stream.start_at(t)` via arm/release |
| Sample timestamps | VITA-49 per packet | None | Tick stream tagger (in-band header); VITA-49 on roadmap |
| Capability discovery | Property tree | Manual per-device knowledge | First-class capability flags |
| Network offload | 10G/100G VITA-49 | iiod over TCP | Corundum NIC now; sample offload on roadmap |
| Hardware | USRP only | Any ADI platform | ADI SDR platforms (2 initial targets) |
| Language surface | C++ / Python | C / Python / others | C core + Python bindings |

The intent is not UHD compatibility (see {doc}`non-goals`) — it is UHD
*parity of expressiveness* on the ADI stack, with libiio kept underneath as
an escape hatch. What that expressiveness gap costs real missions — radar,
EW, direction finding, communications — is worked through in
{doc}`application-domains`.
