# HDL Datapath: Network → Corundum → JESD (TX)

The transmit mirror of {doc}`hdl-datapath-corundum`: VRT frames arrive
from the network, samples leave through the JESD204B TX links — again
entirely inside the PL, again with the ARM steering through CSRs and SPI
only. Lead platform is the ADRV9009-ZU11EG; the ADRV9361-Z7035 mirrors
the structure with LVDS and the new SFP wrapper
({doc}`platform-adrv9361-z7035`).

The RX page's two invariants hold unchanged (samples never enter PS DDR
in offload mode; the ARM owns all control and only control). TX adds a
third:

3. **TX is pull-timed.** The JESD link consumes samples on the device
   clock whether the network delivered them or not. Samples must be
   resident in fabric *before* their air time — the network is never in
   the timing loop, and shortfall is a first-class, loud **underflow**,
   not silence.

```{eval-rst}
.. raw:: html
   :file: _static/images/hdl-datapath-corundum-tx.svg
```

## Data flow (fabric only)

Walking the spine top to bottom — network in, RF out. Values are
representative of the ZU11EG reference configuration
({doc}`requirements-test`).

1. **10GBASE-R PHY ← QSFP+ cage.** Frames from the host enter on the
   same 10G lane the RX direction transmits on — the link is
   full-duplex; RX offload and TX fill share it, which is why the
   RX+TX ≈ 7.86 Gb/s budget in {doc}`streaming-model` is the number
   that matters.
2. **Corundum core — application egress.** The MAC/PCS delivers frames
   into Corundum's RX path, where a CSR-programmed classifier steers
   sample-bearing flows (by UDP port / stream ID) to the
   application-section egress interface instead of the host RX rings.
   Everything else — management traffic riding the fabric port —
   continues to the `mqnic` driver as normal.
3. **VITA-49 depacketizer** *(new HDL — the P6 deliverable, shared
   design with the RX packetizer)*. Validates each frame (stream ID,
   sequence number, length — the full rule list is in
   {doc}`vrt-frame-format`), strips VRT/UDP/IP headers, and emits the
   I/Q payload as AXI-Stream. Sequence gaps and malformed frames are
   counted and raised — the fill policy below decides what the DAC
   hears.
4. **TX sample buffer + timed release.** The `data_offload`-based
   staging RAM. Three fill modes (below); release is immediate,
   hard-timed via Tick `TRANSMIT_ARM` pulsing `sync_ext` at tick T, or
   cyclic. This is the boundary where sample data crosses from the
   Corundum clock domain to the device-clock domain.
5. **`util_upack` + transport.** Channel de-multiplex and per-converter
   sample mapping — the TX counterpart of cpack; the stream's channel
   mask resolves to upack enables here.
6. **JESD204B TX link layer** (`axi_jesd204_tx`). SYSREF-aligned,
   deterministic-latency framing toward the DACs — the property MCS and
   phase-coherent TX depend on ({doc}`timing-synchronization`).
7. **JESD204B PHY (GTH) → 2× ADRV9009.** Serdes lanes to the
   transceivers' DAC side, clocked from the HMC7044 tree.

## TX fill modes and underflow

The buffer stage is where TX earns its keep. Spec-level contract:

| Mode | Fill | Release | Network load |
|---|---|---|---|
| **Streamed** | continuous frames, watermark-guarded | immediate once above low-watermark | sustained ≈ sample rate |
| **Scheduled** | pre-loaded (frames or MVP DMA) | `TRANSMIT_ARM` @ T via `sync_ext` | burst, ahead of time |
| **Cyclic** | loaded once | repeats from fabric RAM | none after load |

- **Underflow is loud.** If the link drains the buffer (streamed mode
  behind rate, scheduled mode exhausted early), the event surfaces as
  `DATAX_EVT_STREAM_UNDERFLOW` with a fabric count — mirroring Tick's
  late/overflow philosophy ({doc}`api-object-model`).
- **Gap policy is explicit.** On a sequence gap the depacketizer either
  halts the stream (default — coherent waveforms must not air with
  holes) or zero-fills and counts (CSR-selectable, for
  tolerant-payload use). Never silent stale-sample repetition.
- **Timestamp semantics.** In scheduled mode the frame timestamp is the
  *earliest air time* — the buffer holds samples until Tick releases at
  T. In streamed/cyclic modes the field is informational.

## Control flow (ARM only, no data)

Same pattern as RX — every surface terminates at the PS over
`M_AXI_HPM0` or SPI. TX-specific control surfaces:

| Target | Mechanism | Owner on the ARM |
|---|---|---|
| JESD TX link + transport CSRs | AXI-Lite | `jesd204-fsm` drivers |
| Depacketizer CSR — flow classifier, stream-ID map, gap policy, watermarks | AXI-Lite (address TBD at P6) | SDK-managed platform driver |
| TX buffer (`data_offload`) — mode, depth, arm | AXI-Lite | SDK via IIO framework |
| Tick scheduler — `TRANSMIT_ARM`, gates | AXI-Lite CSR + batched descriptors | Tick IIO driver |
| ADRV9009 TX profile / attenuation | SPI (Talise API) | `adrv9009` driver |
| MVP TX DMA path (bypassed in offload mode) | AXI-Lite + PS DDR scatter-gather | `axi_dmac` framework |

Shared surfaces (CSR fabric, HMC7044, management GigE, Corundum rings)
are identical to the RX page — one control plane serves both
directions.

### Arming sequence

```{mermaid}
sequenceDiagram
    participant Host as Remote host
    participant PS as ARM (Linux)
    participant NET as Corundum + depacketizer
    participant BUF as TX buffer
    participant TICK as Tick scheduler
    participant JESD as JESD204B TX

    PS->>NET: CSR — classifier (port/stream ID), gap policy
    PS->>BUF: CSR — mode = scheduled, depth
    Host-->>NET: VRT frames (pre-load burst)
    NET-->>BUF: validated payload, seq-checked
    PS->>TICK: batched descriptors (TRANSMIT_ARM @ T)
    TICK-->>BUF: sync_ext release at tick T
    BUF-->>JESD: samples on device clock — first sample airs at T
    Note over BUF,JESD: buffer drains early → loud underflow event to PS
```

## Clock domains

Same table as the RX page ({doc}`hdl-datapath-corundum`) with the
crossing reversed: the one place sample data changes clocks is
**depacketizer → TX buffer** (Corundum 250 MHz domain → device-clock
domain). The P5/P6 CDC review items apply symmetrically, plus one TX
addition: `sync_ext` release and buffer-drain accounting must be
glitch-free across that same boundary.

## Exists vs new

| Stage | Status |
|---|---|
| JESD TX PHY / link / transport / upack | Upstream reference design |
| `data_offload` TX + `axi_dmac` (MVP path) | Upstream reference design |
| Tick scheduler (`TRANSMIT_ARM`) | Integration artifacts — validate at P3 ({doc}`platform-adrv9009-zu11eg`) |
| Corundum core + 10G PHY | Upstream `CORUNDUM=1` variant |
| Flow classifier + VITA-49 depacketizer + app-egress plumbing | **New HDL — P6** ({doc}`roadmap`) |
| Z7035 equivalent (LVDS + SFP wrapper) | **New HDL — P4/P5**, highest-risk ({doc}`platform-adrv9361-z7035`) |
