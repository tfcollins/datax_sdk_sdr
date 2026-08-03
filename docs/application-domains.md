# Application Domains: What Missions Demand

Four mission domains — radar, electronic warfare, direction finding,
and communications — and the demands each places on an SDR platform.
This page is *explanation*: it works top-down from what these systems
do operationally to the timing, coherence, streaming, and usability
requirements that motivate the primitives in {doc}`api-design-goals`.
{doc}`api-application-mapping` runs the complementary direction —
archetype → verbs; this page runs mission → requirements, and the two
meet in the table below. Scope boundaries are per {doc}`non-goals`.

## How domains decompose onto archetypes

A mission domain is not an archetype. A radar is not "the radar
archetype" — it is a gate schedule, a timed playback, and often a
distributed capture, composed on one timeline. The decomposition:

| Domain | Spectrum scanner | Phase-coherent array | TDD burst modem | Record & playback | Distributed multi-node | Char / prod test |
|---|---|---|---|---|---|---|
| Radar | ○ | ○ | ● | ● | ● | ○ |
| EW (ESM / ECM) | ● | ○ | ○ | ● | ● | ○ |
| Direction finding | ○ | ● | — | ○ | ● | ● |
| Communications | — | ○ | ● | ● | ○ | ○ |

● = defining archetype for the domain, ○ = supporting role, — =
rarely applicable. (Same glyphs, different axis, than the archetype ×
feature matrix in {doc}`api-application-mapping` — that table scores
API features, this one scores mission fit.) Verb sequences per
archetype live on that page; per-platform capabilities in the
canonical matrix in {doc}`api-object-model`.

## Radar

**Mission profile:** a pulse-Doppler radar transmits a pulse train at
a fixed pulse-repetition interval (PRI) and processes the echoes of N
pulses together as a coherent processing interval (CPI). Doppler
resolution comes from an FFT *across* pulses, so PRI jitter smears
directly into the Doppler bins. Range is the delay between the TX
pulse edge and the echo samples, so "what device time was sample 0"
must be exact — that timestamp *is* range zero. Range gating opens RX
windows at precise offsets after each TX pulse to bound data volume.
Multistatic and passive variants add geographically separated
receivers that must share the transmit timeline.

**System demands:** TX/RX gate edges hard-timed at fabric resolution
(10 ns — {doc}`timing-synchronization`), repeated without drift over
hundreds of pulses per CPI; a sample-accurate device timestamp on
every capture as the range-zero reference; loud failure on any gap —
one dropped block invalidates the whole CPI, so overflow must surface
as an event with the block marked discontinuous (the failure table in
{doc}`streaming-model`); and the host out of the per-pulse loop
entirely — a 1 kHz PRF sits far inside Linux scheduling jitter, so
the pulse schedule must run from fabric while the host refills a
horizon of queued gates.

One CPI on the wire — the host appears twice, the fabric every pulse:

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant FAB as fabric (Tick)

    App->>SDK: gate schedule for one CPI (N pulses, PRI spacing)
    SDK->>FAB: queued descriptors, horizon ahead
    loop every PRI — no host involvement
        FAB->>FAB: TX gate at T + k·PRI
        FAB->>FAB: RX gate at T + k·PRI + range offset
        FAB-->>SDK: echo block, timestamp = range zero
    end
    SDK-->>App: N timestamped blocks → one CPI
    App->>SDK: refill horizon (next CPI)
```

**The author never writes:** DMA arm/release mechanics, per-pulse
descriptor submission, gate-edge timing loops, or timestamp recovery
from raw buffers.

**Decomposes onto:** the TDD burst modem archetype (a PRI train is a
gate schedule with different labels), record and playback (cyclic
timed replay of the pulse waveform, `start_at`-aligned to the RX
gates), distributed multi-node receiver (multistatic geometry), and
characterization for calibration — all in
{doc}`api-application-mapping`.

**Honest boundaries:** waveform *synthesis* — the chirp itself — is
per-sample work, and per-sample manipulation is the converter's or
the DSP fabric's job, not the scheduler's ({doc}`non-goals`). The SDK
owns the timeline: when the waveform plays and when the gates open,
not what the samples contain. Multistatic deployments get cross-node
*time* alignment on the shared PPS + 10 MHz reference; cross-node
*phase* coherence is never claimed.

## Electronic warfare (ESM / ECM)

**Mission profile:** the receive side (electronic support measures)
surveys a wide band in dwells: tune, capture, extract pulse
descriptor words — time of arrival, frequency, pulse width, amplitude
— and feed a deinterleaver that sorts pulses into emitters. The
design driver is revisit rate against emitter scan periods: revisit
time ≈ (dwell + retune settling) × frequency-plan length, and a plan
is only engineerable if every term is known. Alongside the scan sits
wideband snapshot capture to disk for post-mission analysis. The
transmit side (electronic countermeasures) plays scheduled
techniques: this waveform, at this time, on this frequency.

**System demands:** tuning agility with *published* settling — staged
hops via AD9361 fastlock on the Z7035 (8-profile hop set) or Talise
FHM on the ZU11EG, each applied by a hard-timed edge
({doc}`timing-synchronization`); dwell boundaries known to the sample
so TOA measurements survive the retune — the timestamped-block model
does the slicing; hop-set depth and staging cost exposed as
capability data so the frequency plan can be sized before deployment;
and sustained capture rates that are stated per platform
({doc}`streaming-model`).

The two loops — the SDK owns the survey loop; the reactive loop is
fabric territory, out of the SDK's scope:

```{mermaid}
graph TD
    subgraph OUTER ["SDK survey loop"]
        A[stage hop table<br/>fastlock / FHM] --> B[hard-timed hop edge<br/>at dwell boundary]
        B --> C[timestamped dwell capture<br/>TOA survives the retune]
        C --> D[PDW extraction +<br/>deinterleaving — app code]
        D --> B
    end
    subgraph INNER ["FPGA fast loop"]
        X[detect] -.->|sub-µs,<br/>not the SDK's| Y[respond] -.-> X
    end
    OUTER -. pre-staged responses,<br/>armed gates, telemetry .-> INNER
```

**The author never writes:** fastlock/FHM register programming,
CTRL_IN/GPIO wiring, dwell-boundary bookkeeping, or settling-time
guesswork.

**Decomposes onto:** spectrum scanner (the defining archetype — an
ESM dwell schedule *is* a staged hop scan), record and playback
(snapshot missions, technique playback), and distributed multi-node
receiver (netted ESM, TDOA geolocation — time-aligned only).

**Honest boundaries:** reactive electronic attack — detect a threat
and respond inside the pulse — is not a host-API mission, and this
SDK does not pretend otherwise. The host path is software-timed with
Linux-jitter bounds (the command-class table in
{doc}`timing-synchronization` says which class each verb gets);
closed loops at threat timescales belong in the FPGA DSP fabric. What
the SDK offers a reactive system is the outer loop — pre-staged
responses, armed gates ready to release, timeline control, telemetry
— never the trigger path itself. That is why no REQ-APP below names a
host reaction latency: the number would be a lie ({doc}`non-goals`).

## Direction finding

**Mission profile:** angle-of-arrival estimation — correlative
interferometry, MUSIC-class subspace methods — consumes the
inter-channel phase of simultaneously sampled array elements. An
unknown phase offset between channels is indistinguishable from a
bearing error, so channel-to-channel coherence is not a nice-to-have;
it is the measurement. Array manifold calibration adds a second
workload: repeatable coherent captures against a known source, re-run
until the cal table converges.

**System demands:** N-channel capture with sample simultaneity and
one timestamp per block; phase coherence as *observable, live state*
— one call establishes it (`run_mcs()`), a capability flag reports
it, tuning visibly invalidates it, staged hops within a table
preserve it (the exact contract in {doc}`timing-synchronization`);
refusal to start a coherent stream before MCS has run, rather than a
silent phase ambiguity discovered later in the bearing residuals; and
repeatable timed captures for calibration, with the repeatability
bound published (REQ-TEST-032).

The coherence lifecycle the application observes:

```{mermaid}
stateDiagram-v2
    direction LR
    state "Not coherent" as NC
    state "Phase coherent<br/>(capability flag true)" as C
    [*] --> NC
    NC --> C : run_mcs()
    C --> NC : tune either chip
    C --> C : staged hop within table
    NC --> NC : coherent stream start — refused, loud
    C --> C : N-channel capture,<br/>one timestamp per block
```

**The author never writes:** HMC7044/SYSREF choreography, JESD204B
deterministic-latency bring-up, MCS step sequencing, or coherence
bookkeeping across retunes.

**Decomposes onto:** phase-coherent array capture (the defining
archetype), characterization / production test (calibration runs),
and distributed multi-node receiver (TDOA as the multi-site DF mode).

**Honest boundaries:** single-node phase coherence is a dual-chip
ZU11EG capability and structurally unavailable on the Z7035 — the
capability flag says so, and application code branches on the flag,
never the board name (REQ-API-002, {doc}`api-design-goals`). Across
nodes only *time* alignment is claimed: TDOA works; cross-node
interferometry is not promised. The AoA math itself is application
code — the SDK delivers coherent, timestamped blocks and stops there.

## Communications

**Mission profile:** communication waveforms live on frame timelines.
A TDD link alternates TX bursts and RX windows against a peer's
clock; FDD runs continuous duplex streams; network entry means
aligning the local timeline to network time — PPS/GPSDO-disciplined
in v1. Around the link sits test infrastructure: BER and throughput
harnesses replaying recorded or synthetic waveforms against the
receiver under test.

**System demands:** gate schedules committed a horizon ahead and
fired with per-edge fabric accuracy (the TDD frame walkthrough,
sequence diagram included, is in {doc}`api-application-mapping`);
epoch alignment to PPS (`set_time_next_pps`,
{doc}`timing-synchronization`) so both ends of the link agree what
"slot 0" means; sustained-rate ceilings that are *stated* per
platform — the MVP path is host-link bound on the Z7035 (the rate
table in {doc}`streaming-model`) — so a symbol rate can be validated
against reality on paper, before hardware; and cyclic TX for beacons
and pilots with the host fully detached.

Network entry — both ends agree on the timeline before a single
burst flies (per-frame mechanics are the TDD walkthrough in
{doc}`api-application-mapping`):

```{mermaid}
sequenceDiagram
    participant A as station A
    participant REF as PPS + 10 MHz
    participant B as station B

    REF-->>A: PPS edge
    REF-->>B: PPS edge
    A->>A: set_time_next_pps(epoch)
    B->>B: set_time_next_pps(epoch)
    Note over A,B: both timelines agree what "slot 0" means
    A->>B: TX burst, slot k — gate fires at slot boundary
    B->>A: TX burst, slot k+1 — gate fires at slot boundary
```

**The author never writes:** per-frame host wakeups, `axi_tdd`
register programming, or (to first order) buffer-geometry tuning.

**Decomposes onto:** TDD burst modem (the defining archetype), record
and playback (waveform replay, receiver test), and distributed
multi-node receiver (point-to-multipoint timelines).

**Honest boundaries:** modem DSP is application code, and no
flowgraph scheduler ships in v1 (no GNU Radio blocks —
{doc}`non-goals`). Network-time discipline is PPS + 10 MHz only; PTP
is deferred. Host round-trip latency is unbounded — which is exactly
why the API's answer to "low latency" is pre-queued schedules running
from fabric, not fast control writes.

## Requirements (REQ-APP)

Distilled from the four domains above; each item names the domains
that motivate it and the existing requirements that discharge it.

- **REQ-APP-001 — Deterministic edges at fabric resolution.**
  Periodic edge patterns — radar PRI trains, TDD frames — fire
  hard-timed on device-time ticks, never host-timed. *From: Radar,
  Communications. Discharged by:* REQ-API-004
  ({doc}`api-design-goals`), REQ-TEST-022.
- **REQ-APP-002 — Sample-accurate time-tagging.** The first sample of
  a timed capture is device time T, and in-band timestamps let dwell
  and pulse boundaries be recovered to the sample (radar range zero,
  ESM TOA). *From: Radar, EW. Discharged by:* the arm/release
  contract in {doc}`streaming-model`, REQ-TEST-023.
- **REQ-APP-003 — Tuning agility with published arithmetic.**
  Staged-hop settling time, staging cost, and hop-set depth are
  capability data, so an ESM revisit rate is computable before
  deployment. *From: EW. Discharged by:* REQ-TEST-031, the capability
  matrix in {doc}`api-object-model`.
- **REQ-APP-004 — Coherence as observable state.** Multi-channel
  phase coherence is established by one call, reported live,
  invalidated visibly, and enforced by refusal-to-start. *From:
  Direction finding. Discharged by:* the MCS contract in
  {doc}`timing-synchronization`, REQ-TEST-032.
- **REQ-APP-005 — Cross-node time alignment, honestly bounded.**
  Multi-node missions schedule against a shared PPS + 10 MHz timeline
  with scope-verifiable alignment; cross-node *phase* is never
  claimed. *From: Radar (multistatic), EW (TDOA), Direction finding.
  Discharged by:* REQ-HW-002, REQ-TEST-023.
- **REQ-APP-006 — No silent data loss.** Overflow, underflow, and
  late commands are loud events, and affected blocks are marked
  discontinuous — a gap that silently skews a CPI or a BER run is a
  defect. *From: all four. Discharged by:* REQ-API-008
  ({doc}`api-design-goals`).
- **REQ-APP-007 — Host out of the repetition loop.** Periodic
  timelines run from fabric with the host refilling a schedule
  horizon; Linux jitter bounds queue depth, never edge accuracy.
  *From: Radar, Communications. Discharged by:* REQ-API-005, the
  command classes in {doc}`timing-synchronization`.
- **REQ-APP-008 — Stated throughput ceilings.** Sustained-rate bounds
  per platform are published as measured capability data so waveform
  and survey designs can be validated on paper. *From: EW,
  Communications. Discharged by:* the rate table in
  {doc}`streaming-model`, measured per {doc}`requirements-test`
  evidence rules.
- **REQ-APP-009 — Defining flows fit the ergonomic ceilings.** Each
  domain's defining (●) archetype flow stays within the REQ-API-001
  line counts and the REQ-API-002 no-board-names rule — mission code
  is verb composition, not infrastructure. *From: all four.
  Discharged by:* REQ-API-001/002/003.

Deliberately absent: a reactive-response latency requirement. The EW
section explains why — the host loop cannot honestly carry one, and
the fabric loop that could is outside the SDK's scope
({doc}`non-goals`).

## What this page holds to account

The trace runs both ways. Every REQ-APP names the domain sections
that motivate it and the REQ-API / REQ-TEST items that discharge it.
A domain demand with no REQ-APP, or a REQ-APP whose defining
archetype has no verb path in {doc}`api-application-mapping`, is a
spec bug: per REQ-DOC-001, the spec changes — not the mission.
