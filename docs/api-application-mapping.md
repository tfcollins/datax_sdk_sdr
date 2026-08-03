# Application Archetypes → API Mapping

How real applications decompose onto the focused verb set
({doc}`api-design-goals`). This page is the API's accountability
mechanism: each archetype must be expressible with the shipped verbs
and capabilities — if one is not, the spec changes (REQ-DOC-001), not
the application. The mission-side view — which domains generate these
archetypes and why — is {doc}`application-domains`.

## The matrix

Which API features each archetype consumes (● = core dependency,
○ = optional):

| Archetype | Streams | `start_at` | Hop staging | Gating | MCS | Events | Net offload |
|---|---|---|---|---|---|---|---|
| Spectrum scanner | ● | ● | ● | ○ | — | ● | ○ |
| Phase-coherent array capture | ● | ● | — | — | ● | ● | ○ |
| TDD burst modem | ● | ● | — | ● | — | ● | — |
| Record and playback | ● | ○ | — | — | — | ● | ○ (P6) |
| Distributed multi-node receiver | ● | ● | — | ○ | ○ | ● | ● (P6) |
| Characterization / production test | ● | ○ | ○ | — | ○ | ● | — |

Capabilities per platform and phase: the canonical matrix in
{doc}`api-object-model`.

## Spectrum scanner

**Goal:** sweep a frequency plan, capturing a dwell at each hop, with
hop timing tight enough that dwell boundaries are known to the sample.

**Flow:** stage the hop table once (`stage_hop_table`) → queue timed
tunes at dwell boundaries (`sched.at(t).tune(f)` — pre-staged class:
fastlock select on the Z7035, FHM on the ZU11EG) → one gapless
`start_at`-armed RX stream spanning the sweep → slice the capture by
dwell using the in-band timestamps → `sched.wait_all()` confirms every
hop fired on time.

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant FAB as fabric (Tick)

    App->>SDK: stage_hop_table (once, untimed)
    App->>SDK: sched.at(t_k).tune(f_k) — all dwells, one commit
    App->>SDK: rx.start_at(T) — one gapless stream
    loop every dwell — no host involvement
        FAB->>FAB: hop edge at t_k (pre-staged)
        FAB-->>SDK: samples keep flowing, timestamped
    end
    SDK-->>App: wait_all() — every hop on time, or loud
    App->>App: slice the capture by dwell via timestamps
```

**The SDK hid:** fastlock profile programming, CTRL_IN/FHM GPIO
wiring, descriptor batching, offload arming, timestamp recovery.
Reference code: the hop-scan example in {doc}`api-python`
(REQ-API-001: ≤ 25 lines).

**Platform notes:** hop-set depth 8 on the Z7035 (fastlock) vs the FHM
table on the ZU11EG — same application code, different `caps` limits.

## Phase-coherent array capture (DF / beamforming)

**Goal:** N-channel capture where inter-channel phase is meaningful —
direction finding, beamforming calibration, MIMO channel sounding.

**Flow:** `run_mcs()` → assert `"phase_coherent" in dev.caps` → open
one RX stream with a channel mask spanning both chips →
`start_at(T)` → every block is a phase-consistent `(4, N)` array with
one timestamp.

```{mermaid}
graph LR
    A["run_mcs()"] --> B["assert 'phase_coherent'<br/>in dev.caps"]
    B --> C["open RX stream —<br/>mask spans both chips"]
    C --> D["start_at(T)"]
    D --> E["(4, N) blocks,<br/>one timestamp each"]
    T[tune] -.->|invalidates<br/>coherence| A
```

**The SDK hid:** HMC7044 SYSREF choreography, Talise MCS steps,
deterministic-latency JESD bring-up, the coherence-invalidation rules
(tuning resets coherence — the capability flag tracks it live,
{doc}`timing-synchronization`).

**Platform notes:** ZU11EG-defining archetype; structurally n/a on the
single-chip Z7035 — the capability flag, not a board check, tells the
application (REQ-API-002).

## TDD burst modem

**Goal:** alternate TX bursts and RX windows on an exact frame
timeline shared with a peer.

**Flow:** align device time to PPS → arm one TX and one RX stream →
queue a repeating gate schedule
(`sched.at(t).gate_on(tx)` / `.gate_off(tx)` / `.gate_on(rx)` …) in
frame-sized batches, recommitting a horizon ahead → `TDD_SYNC` aligns
an `axi_tdd` instance where fitted.

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant TICK as Tick (fabric)

    App->>SDK: gate schedule, frames N..N+k (one commit)
    SDK->>TICK: batched descriptors
    loop every frame — no host involvement
        TICK-->>TICK: gate_on(TX) @ t0 · gate_off(TX) @ t1
        TICK-->>TICK: gate_on(RX) @ t2 · gate_off(RX) @ t3
    end
    TICK-->>SDK: completions (drained to ring)
    SDK-->>App: wait_all() — every edge on time, or loud
```

**The SDK hid:** the host is out of the per-frame loop entirely —
Linux jitter bounds how far *ahead* the schedule is queued, not frame
edge accuracy (the pre-staged/hard-timed distinction,
{doc}`timing-synchronization`).

## Record and playback

**Goal:** capture a long RF segment to storage; later, replay it —
optionally forever.

**Flow:** record — RX stream with deep buffering, blocks streamed to
disk with their timestamps. Replay — `tx(data)` one-shot, or
`cyclic=True` so the waveform repeats from fabric memory with the host
detached. Timed replay (`start_at`) aligns playback to a device-time
edge for receiver-under-test work.

```{mermaid}
graph LR
    A[RX stream,<br/>deep buffers] --> B[blocks +<br/>timestamps] --> C[(storage)]
    C --> D["tx(data),<br/>cyclic=True"] --> E[fabric repeats —<br/>host detached]
    S["start_at(T)"] -.->|aligns replay to a<br/>device-time edge| D
```

**The SDK hid:** cyclic buffer mechanics, sustained-rate buffer
sizing (caps carry the platform's DMA bounds), underflow surfacing.

**Roadmap:** at P6 this archetype is where RF-sample offload lands
first — record becomes line-rate frames to a host array
({doc}`hdl-datapath-corundum`), replay its TX mirror.

## Distributed multi-node receiver

**Goal:** several boards, one timeline — TDOA, multistatic radar,
distributed spectrum sensing.

**Flow:** shared PPS + 10 MHz (REQ-HW-002) → each node
`set_time_next_pps(epoch)` → one `datax_context` per node (remote
URIs, REQ-API-003) → `start_at(T)` on all nodes → captures align to
the shared timeline; `marker` outputs give the scope-verifiable proof
(REQ-TEST-023). Cross-node phase coherence is *not* claimed — this is
time alignment, honest per {doc}`timing-synchronization`.

```{mermaid}
graph TD
    CTL[control host —<br/>one context per node,<br/>remote URIs]
    REF[shared PPS + 10 MHz]
    CTL --> N1[node 1]
    CTL --> N2[node 2]
    CTL --> N3[node n]
    REF -.-> N1
    REF -.-> N2
    REF -.-> N3
    N1 --> ALIGN["set_time_next_pps(epoch),<br/>then start_at(T), every node"]
    N2 --> ALIGN
    N3 --> ALIGN
    ALIGN --> OUT[captures on one timeline —<br/>markers = scope-verifiable proof]
```

**Roadmap:** P6 turns each node into a line-rate frame source toward a
collection host — the "radiohead over the network" end state.

## Characterization / production test

**Goal:** scripted RF verification — loopback EVM, hop-settling
measurement, gain flatness — the {doc}`requirements-test` Tier-3
suites themselves.

**Flow:** immediate-mode controls (`DATAX_TIME_NOW`) for sweep loops;
`start_at` only where the measurement needs a known capture instant
(settling profiles); events monitored so an overflow invalidates a
measurement loudly rather than skewing it.

```{mermaid}
graph LR
    A["set state<br/>(DATAX_TIME_NOW)"] --> B["capture — start_at<br/>where the instant matters"]
    B --> C[measure] --> D{next<br/>point?}
    D -->|yes| A
    D -->|done| E[report]
    EV[overflow event] -.->|invalidates the<br/>point, loudly| C
```

**Mapping note:** the test tiers consume the same public API as
applications — no privileged backdoor — so passing Tier 3 *is*
evidence the focused surface suffices (REQ-API-005).

## Coverage argument

Six archetypes, twenty verbs, no gaps — and two deliberate
out-of-scope shapes, stated per {doc}`non-goals`: per-sample adaptive
control (chirps, sample-rate feedback loops — the converter's or DSP
fabric's job) and GNU Radio-style graph scheduling (the Python
bindings are the integration surface in v1). Anything an archetype
needs beyond the verb table goes through the doc-first spec change
process — the mechanism that keeps "focused" true over time.
