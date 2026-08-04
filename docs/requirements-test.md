# Test Requirements

Four tiers. A capability may not be advertised (matrix in
{doc}`api-object-model`) until its tier-2/tier-3 criteria pass on that
platform — "validated" status is earned, never asserted.

```{mermaid}
graph LR
    T1[Tier 1 — sim + unit<br/>every push, under 5 min] --> T2[Tier 2 — HIL, labgrid<br/>smoke nightly, timed suite<br/>gates P3/P4 exit]
    T2 --> T3[Tier 3 — RF-level<br/>EVM, hop settling,<br/>phase coherence]
    T3 --> V[capability advertised<br/>as validated]
    T4[Tier 4 — CI] -.->|red nightly blocks<br/>matrix changes| V
```

## Tier 1 — Simulation and unit (no hardware)

- **REQ-TEST-001** — The SDK inherits Tick's descriptor-contract tests:
  the 48-byte wire format is cross-validated between the SDK's
  serializer, Tick's Python model, and the kernel UAPI header.
- **REQ-TEST-002** — API unit tests run against a **mocked IIO
  context** (attribute map + fake Tick device): full coverage of
  capability discovery, batching/commit ordering, completion-ring
  drainage, guard-margin rejection, and error mapping.
- **REQ-TEST-003** — Timed-path state machines (arm/release, late
  handling, flush) covered by deterministic simulation against the
  Python Tick model — every failure mode in {doc}`streaming-model`
  reproduced in sim before it is tested on hardware.
- **REQ-TEST-004** — Tier 1 runs in CI on every push, < 5 minutes.

## Tier 2 — Hardware-in-the-loop (labgrid)

- **REQ-TEST-020** — Both platforms are labgrid places (REQ-HW-020);
  suites acquire, flash, boot, test, release — unattended.
- **REQ-TEST-021** — Per-board smoke suite: boot, context creation,
  capability probe matches the expected matrix row, driver probes
  (Tick where fitted), immediate-stream sanity RX and TX.
- **REQ-TEST-022** — Timed suite (gates P3/P4 exit): timed-GPIO
  staircase, timed capture with tick-exact first-sample timestamp,
  gated burst pattern, hop schedule with all-on-time completions.
- **REQ-TEST-023** — Every timed claim ships **evidence artifacts**:
  scope captures of markers/staircases against PPS, measured tick rate,
  completion logs. Stored per-run, linked from the platform runbook.
- **REQ-TEST-024** — Suites are release-pinned: results name the HDL
  release, Vivado version, kernel commit, and bitstream hash.

## Tier 3 — RF-level

- **REQ-TEST-030** — Loopback EVM / flatness per channel at
  representative rates — the streaming path moves *correct* samples,
  not just samples.
- **REQ-TEST-031** — Hop-settling measurement: time from trigger edge
  to within-spec LO settle, per mechanism (fastlock on Z7035, FHM on
  ZU11EG), against the numbers claimed in
  {doc}`timing-synchronization`.
- **REQ-TEST-032** — ZU11EG phase-coherence: cross-channel phase spread
  across chips measured over repeated MCS runs; repeatability bound
  published in the platform runbook.
- **REQ-TEST-033** — Corundum tiers (P5+): NIC link/throughput sanity;
  P6 adds packetizer stream integrity (sequence gaps, timestamp
  monotonicity) at rated load.

## Tier 4 — CI

- **REQ-TEST-040** — Docs build with `-W` and linkcheck on every push
  (the P0 gate, already live).
- **REQ-TEST-041** — Tier 1 on every push; Tier 2 smoke nightly on both
  places; the full timed suite on demand and before any release tag.
- **REQ-TEST-042** — A red nightly blocks capability-matrix changes:
  no capability flips to "available" while its suite is failing.
