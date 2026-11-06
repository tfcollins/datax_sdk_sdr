# Roadmap

Seven phases. Each exits on acceptance criteria traced to
{doc}`requirements-test` IDs; capabilities flip in the
{doc}`api-object-model` matrix only at phase exit (REQ-TEST-042).
The operating rhythm that runs these gates — per change, nightly,
per phase, per release — is {doc}`requirements-process`.

```{mermaid}
graph TD
    P0[P0 — documentation site<br/>this site, published] --> P1[P1 — SDK skeleton<br/>context/device over libiio]
    P1 --> P2[P2 — streaming MVP<br/>both boards, stock designs]
    P2 --> P3[P3 — timed control ZU11EG]
    P2 --> P4[P4 — Tick port Z7035<br/>= full API parity]
    P3 --> P4
    P3 --> P5[P5 — Corundum integration]
    P4 --> P5
    P5 --> P6[P6 — VITA-49 RF-sample offload]

    I[infrastructure delivered:<br/>tick · vrt49 · hopcap on ZU11EG] -.-> P3
    I -.-> P5
    I -.-> P6
    G3{{gate: Z7035 10G GTX wrapper<br/>feasibility — may slip alone}} -.-> P5
```

## P0 — Documentation site

**Status: done.** This site, published and green. **Exit**:
REQ-TEST-040 live (CI `-W` + linkcheck + Pages deploy).

## P1 — SDK skeleton

**Status: not started.** First code task. `libdatax` context/device
over libiio + Python bindings + capability framework. Runs against
*any* IIO device — no Tick, no target hardware needed. **Exit**:
REQ-TEST-001/002 passing; API matches {doc}`api-c-core` or the doc is
amended first (REQ-DOC-001).

## P2 — Streaming MVP

**Status: done (2026-11-05).** libdatax streams (RX/TX, one-shot and cyclic, zero-copy) validated on both labgrid places: `lablp` 10/10 and `tron` 12/12, digital loopback bit-exact on every channel. tron ran an HDL `main` PL, not stock 2023_R2 ({doc}`platform-adrv9009-zu11eg`). The matrix rows stay *integration artifacts* until `hw-test.yml` has a green run, which needs self-hosted runners for libdatax (REQ-TEST-041/042).

Stream objects over AXI-DMAC on both boards, stock reference designs.
Immediate start/stop, RX/TX, cyclic TX, zero-copy paths. The transport is
libiio v1 blocks over the stock DMA devices, reached from the host
through the boards' stock `iiod`; vrt49's `vrt49://` backend needs
libiio v0 and its network-sample surface is P6 (design:
`specs/2026-11-05-libdatax-p2-streaming-design.md`). **Exit**:
REQ-TEST-021 smoke green on both labgrid places; REQ-TEST-030's digital
loopback part on both.

## P3 — Timed control, ADRV9009-ZU11EG

The timed API surface (`start_at`, scheduler, FHM hops, MCS) on `tron`.
Both gates this phase once carried are satisfied: Tick is validated on
`tron` and the `hdl_2026_r1` regression is resolved
({doc}`platform-adrv9009-zu11eg`). P3 is now the phase that exposes
through `libdatax` what tick and hopcap already prove.

**Exit**: REQ-TEST-022 timed suite + REQ-TEST-031/032 with evidence
artifacts (REQ-TEST-023); ZU11EG matrix row flips to P3 capabilities.

## P4 — Tick on ADRV9361-Z7035 · full parity milestone

Tick and a fastlock hop controller already ship inside vrt49's 1G SFP
design for this board; the remaining work is listed on
{doc}`platform-adrv9361-z7035` (RF-measured settle, DMA-path gates and
timestamps, PPS route, runbook). **Exit**: REQ-TEST-022 + REQ-TEST-031
on the Z7035 — at which point **both boards expose the same timed
API**, differing only in hop mechanism and coherence capabilities.

## P5 — Network plane through vrt49

ZU11EG: delivered infrastructure — Tick, the vrt49 framer and Corundum
coexist in hopcap's bitstream, with the NIC also available as
control/telemetry plane ({doc}`platform-adrv9009-zu11eg`). Z7035: the
1G SFP design is the shipped path; the **10G GTX wrapper** stays
flagged highest-risk and may slip independently without dragging the
rest of P5 (the Z7035 fallback stays PS GigE). **Exit**: REQ-TEST-033
NIC tier on ZU11EG (and Z7035 if the wrapper lands); `NET_OFFLOAD_NIC`
flips accordingly.

## P6 — RF-sample offload

The VITA 49.2 packetizer ({doc}`streaming-model`) is vrt49's framer,
delivered on the ZU11EG and exercised by hopcap. Remaining: the
`libdatax` surface, TX via the vrt49 deframer, Z7035 channel/rate
subsets, and the 100G VCU118 + DAQ3 tier with the libiio `daqiri:`
backend as receiver. **Exit**: REQ-TEST-033 packetizer integrity at
rated load; `NET_OFFLOAD_SAMPLES` flips.

## External dependencies, named

| Dependency | Owner | Phases |
|---|---|---|
| Tick kernel fast path (bulk submit / IRQ completions) | Tick project | improves P3+, API-neutral by design ({doc}`api-c-core`) |
| hopcap upstream PRs: `VRT_FABRIC_HOP_ENABLE` to vrt49, `--system-top` to Tick | hopcap | P3 |
| `mqnic` mainline-quality driver | corundum-zcu102-fmcomms2 effort | P5 |
| Corundum upstream pin refresh | Corundum / ADI HDL | P5 |
| libiio `feature/daqiri-udp` upstreaming | libiio fork | P6 |
| VCU118 + DAQ3 UDP bitstream for the DAQIRI path | vrt49 | P6 |
| labgrid place for the 100G host NIC | lab infrastructure | P6 |
