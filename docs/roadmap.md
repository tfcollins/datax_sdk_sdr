# Roadmap

Seven phases. Each exits on acceptance criteria traced to
{doc}`requirements-test` IDs; capabilities flip in the
{doc}`api-object-model` matrix only at phase exit (REQ-TEST-042).

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

    G1{{gate: Tick ZU11EG<br/>hardware validation}} -.-> P3
    G2{{gate: hdl_2026_r1<br/>coherency regression decision}} -.-> P3
    G2 -.-> P5
    G3{{gate: Z7035 GTX wrapper<br/>feasibility — may slip alone}} -.-> P5
```

## P0 — Documentation site

This site, published and green. **Exit**: REQ-TEST-040 live (CI `-W` +
linkcheck + Pages deploy).

## P1 — SDK skeleton

`libdatax` context/device over libiio + Python bindings + capability
framework. Runs against *any* IIO device — no Tick, no target hardware
needed. **Exit**: REQ-TEST-001/002 passing; API matches
{doc}`api-c-core` or the doc is amended first (REQ-DOC-001).

## P2 — Streaming MVP

Stream objects over AXI-DMAC on both boards, stock reference designs.
Immediate start/stop, RX/TX, cyclic TX, zero-copy paths. **Exit**:
REQ-TEST-021 smoke green on both labgrid places; REQ-TEST-030 loopback
on both.

## P3 — Timed control, ADRV9009-ZU11EG

Tick hardware validation on `tron` + the timed API surface
(`start_at`, scheduler, FHM hops, MCS). **Gated on**:

- Tick's "ZU11EG validated" milestone (today: integration artifacts);
- the `hdl_2026_r1` regression decision — if the coherency fix is not
  hardware-confirmed, P3 ships on `hdl_2023_r2` *without* Corundum and
  P5 waits ({doc}`platform-adrv9009-zu11eg`).

**Exit**: REQ-TEST-022 timed suite + REQ-TEST-031/032 with evidence
artifacts (REQ-TEST-023); ZU11EG matrix row flips to P3 capabilities.

## P4 — Tick port to ADRV9361-Z7035 · full parity milestone

The new-HDL phase scoped in {doc}`platform-adrv9361-z7035`: scheduler +
tagger instantiation, CTRL_IN fastlock wiring, LVDS-path gates, XDC,
devicetree. **Exit**: REQ-TEST-022 + REQ-TEST-031 on the Z7035 —
at which point **both boards expose the same timed API**, differing only
in hop mechanism and coherence capabilities.

## P5 — Corundum integration

ZU11EG: Tick + Corundum coexistence in one design (address map,
resources, clocking) with the NIC as control/telemetry plane. Z7035:
the **new GTX wrapper** — flagged highest-risk from day one; it may slip
independently without dragging the rest of P5 (the Z7035 fallback stays
PS GigE). **Exit**: REQ-TEST-033 NIC tier on ZU11EG (and Z7035 if the
wrapper lands); `NET_OFFLOAD_NIC` flips accordingly.

## P6 — RF-sample offload

The VITA-49 packetizer in Corundum's application section
({doc}`streaming-model`), ZU11EG-led; Z7035 limited to channel/rate
subsets. **Exit**: REQ-TEST-033 packetizer integrity at rated load;
`NET_OFFLOAD_SAMPLES` flips.

## External dependencies, named

| Dependency | Owner | Phases |
|---|---|---|
| Tick ZU11EG hardware validation | Tick project | P3 |
| Tick kernel fast path (bulk submit / IRQ completions) | Tick project | improves P3+, API-neutral by design ({doc}`api-c-core`) |
| `hdl_2026_r1` cache-coherency fix confirmation | ADI HDL / Tick | P3, P5 |
| `mqnic` mainline-quality driver | corundum-zcu102-fmcomms2 effort | P5 |
| Corundum upstream pin refresh | Corundum / ADI HDL | P5 |
