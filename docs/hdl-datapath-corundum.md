# HDL Datapath: JESD → Corundum → Network

The block-level view of the offload design: how samples move entirely
inside the PL from the JESD204B links to the network cage, and how the
ARM complex controls every stage without ever touching sample data.
Lead platform is the ADRV9009-ZU11EG (JESD204B + QSFP+); on the
ADRV9361-Z7035 the same structure applies with the LVDS interface in
place of JESD and an SFP+ cage behind the new GTX wrapper
({doc}`platform-adrv9361-z7035`).

This page covers the RX (capture) direction; the transmit mirror —
frames in from the network, samples out the JESD links — is
{doc}`hdl-datapath-corundum-tx`.

Two invariants define this page:

1. **Sample data never enters PS DDR.** In offload mode the entire RX
   pipeline — deframing, packing, timestamping, packetization, MAC — is
   fabric-resident. The MVP DMA path (`data_offload` → `axi_dmac` → PS)
   still exists in the design but is bypassed.
2. **The ARM owns all control, and only control.** Every block hangs off
   the PS through AXI-Lite CSRs or SPI; no control decision is made on
   the datapath's critical timing path except the hard-timed actions
   delegated to the Tick scheduler.

```{eval-rst}
.. raw:: html
   :file: _static/images/hdl-datapath-corundum.svg
```

## Data flow (fabric only)

Walking the spine of the figure top to bottom. Widths, rates, and lane
counts are representative of the ZU11EG reference configuration and are
stated as such — measured numbers replace them per
{doc}`requirements-test` evidence.

1. **JESD204B PHY (GTH quads).** The dual-ADRV9009 links terminate on
   GTH serdes lanes clocked from the HMC7044 device-clock tree. Lane
   count and rate follow the selected Talise profile.
2. **JESD204B RX link layer** (`axi_jesd204_rx`). SYSREF-aligned,
   deterministic-latency deframing — the property MCS depends on
   ({doc}`timing-synchronization`). Elastic buffers release on the LMFC
   boundary programmed at bring-up.
3. **Transport + `util_cpack`.** Per-converter sample mapping and
   channel selection. The channel mask set through
   `datax_stream_create()` resolves to cpack enables here.
4. **`tick_stream_timestamp_tag`.** Prepends the 64-bit device time to
   each capture window in-band, so every downstream frame is traceable
   to a Tick timestamp. Gating (`STREAM_GATE`) and timed release
   (`CAPTURE_ARM`/`sync_ext`) act on the stream at this stage boundary.
5. **VITA-49 packetizer** *(new HDL — the P6 deliverable)*. Consumes the
   tagged AXI-Stream, segments it into fixed-payload VRT-style frames,
   and stamps each header from the in-band time plus a per-stream
   sequence counter. UDP/IPv4 encapsulation is fixed-function with
   CSR-programmed addresses/ports — no fabric ARP/ND; peers are static
   on a point-to-point link.
6. **Corundum core — application ingress.** Frames enter through the
   application-section streaming interface into dedicated TX queues,
   arbitrated by Corundum's transmit scheduler ahead of (lower-priority)
   host-originated traffic, then out through the MAC/PCS.
7. **10GBASE-R PHY → QSFP+ cage.** One 10G lane today; the cage's
   remaining lanes are the headroom path discussed in
   {doc}`streaming-model`.

### Frame format (spec-level)

| Field | Size | Source |
|---|---|---|
| VRT-style header (type, stream ID) | 8 B | packetizer CSR (per-stream) |
| Sequence number | 4 B | per-stream counter in packetizer |
| Integer + fractional timestamp | 12 B | in-band device time (Tick ticks + tick-rate metadata) |
| Payload length | 4 B | CSR-programmed, fixed per stream |
| I/Q payload | 8192 samples typ. | cpack output, 16-bit I/Q |

Target ≤ 2 % header overhead at the typical payload with jumbo frames —
the budget worked in {doc}`streaming-model`.

## Control flow (ARM only, no data)

Every control surface terminates at the PS; the figure's thin blue paths
carry registers and SPI transactions, never samples.

| Target | Mechanism | Owner on the ARM |
|---|---|---|
| JESD link + transport CSRs | AXI-Lite via `M_AXI_HPM0` | `jesd204-fsm` drivers |
| Tick scheduler CSR | AXI-Lite (BD `0x4600_0000` → PS `0x8600_0000`) | Tick IIO driver |
| Corundum NIC CSR + rings | AXI-Lite (`0xA000_0000`, 16 MiB) | `mqnic` netdev driver |
| VITA-49 packetizer CSR | AXI-Lite (address TBD at P6 design) | SDK-managed platform driver |
| ADRV9009 ×2 | SPI (Talise API), FHM trigger via Tick GPIO | `adrv9009` driver |
| HMC7044 | SPI | clock framework driver |
| MVP DMA path | AXI-Lite + scatter-gather in PS DDR | `axi_dmac` framework |

Notes on the split:

- **Corundum's rings and doorbells are control.** The `mqnic` driver
  manages queue descriptors and doorbells from the ARM; in offload mode
  the *descriptors* live wherever the driver puts them, but the sample
  payloads sourced by the app section never cross into PS memory.
- **Hard-timed control is delegated, not bypassed.** The ARM stages Tick
  descriptors (batched CSR writes — {doc}`api-c-core`); the scheduler
  then fires gates, `sync_ext`, and FHM hop edges in fabric at exact
  device times. The ARM is out of the timing-critical loop by design.
- **Two Ethernet planes.** Management sessions (iiod, SSH, telemetry)
  ride the PS GigE (GEM). The QSFP+ fabric port carries sample frames —
  and may *also* carry control as a convenience (remote iiod over
  `mqnic`), but control never depends on it.

### Bring-up order

The dependency chain the SDK's `datax_context_create()` +
`run_mcs()` + stream-arm sequence drives, and which the platform
runbook (REQ-DOC-004) documents step-by-step:

```{mermaid}
sequenceDiagram
    participant PS as ARM (Linux)
    participant CLK as HMC7044
    participant RF as 2× ADRV9009
    participant JESD as JESD204B link
    participant TICK as Tick scheduler
    participant NET as Corundum + packetizer

    PS->>CLK: SPI — device clocks + SYSREF profile
    PS->>RF: SPI — Talise init (profile, cals)
    PS->>JESD: CSR — link bring-up (jesd204-fsm)
    RF-->>JESD: lanes up, SYSREF aligned (deterministic latency)
    PS->>RF: MCS sequence (with CLK SYSREF pulses)
    PS->>TICK: CSR — align device time to PPS
    PS->>NET: CSR — MAC/IP/port, stream IDs, payload size
    PS->>TICK: batched descriptors (CAPTURE_ARM @ T)
    TICK-->>NET: sync_ext release at T — frames flow, PL-only
```

## Clock domains

Representative values for the ZU11EG configuration; the design's actual
constraints live with the HDL project.

| Domain | Representative clock | Blocks |
|---|---|---|
| Device-clock tree | HMC7044 outputs (profile-dependent) | GTH refclks, JESD link, transport, cpack |
| Tick domain | 100 MHz | scheduler, timestamp tag counters |
| Corundum datapath | 250 MHz | app section, TX rings, MAC |
| 10G PHY | 156.25 MHz refclk | PCS/PMA |
| PS interfaces | APU/AXI clocks | CSR fabric, GEM |

CDC points that the P5/P6 design reviews must cover explicitly: tag →
packetizer (device-clock → Corundum domain, the only place sample data
changes clocks), Tick `sync_ext` into the device-clock domain, and CSR
crossings (standard AXI-Lite clock converters).

## Exists vs new

| Stage | Status |
|---|---|
| JESD PHY / link / transport / cpack | Upstream reference design |
| `data_offload` + `axi_dmac` (MVP path) | Upstream reference design |
| Tick scheduler + timestamp tag | Integration artifacts — validate at P3 ({doc}`platform-adrv9009-zu11eg`) |
| Corundum core + 10G PHY + QSFP wiring | Upstream `CORUNDUM=1` variant |
| VITA-49 packetizer + app-section plumbing | **New HDL — P6** ({doc}`roadmap`) |
| Z7035 equivalent (LVDS spine + SFP wrapper) | **New HDL — P4/P5**, highest-risk ({doc}`platform-adrv9361-z7035`) |
