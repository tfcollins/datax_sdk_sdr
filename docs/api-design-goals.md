# Focused API: Goals and Requirements

Why this SDK ships a deliberately *small* API — and the numbered,
testable requirements that keep it that way. The object model
({doc}`api-object-model`) is the *what*; this page is the *why* and the
acceptance bar.

## The problem with big surfaces

Every existing way to drive these radios pushes its full complexity to
the application:

- **Raw IIO / sysfs** — hundreds of attributes per platform, each a
  string path the application must know, none with timing semantics.
- **pyadi-iio** — friendlier, but per-part classes whose property sets
  mirror the driver, so application code is written *to a board*, and
  the timed-control gap remains.
- **UHD** — the right verbs, but a large C++ surface (device
  properties, tune requests, subdev specs) whose breadth exists to span
  every USRP ever made.

The cost is identical in each case: every knob visible to the
application is a decision the application author must make, a line they
must write, and a portability liability they must carry. Most SDR
applications spend that effort re-deriving the same ten operations.

## The radiohead answer

The streaming-radiohead model ({doc}`architecture-proposal`) reduces
the application-facing surface to a small verb set with uniform timing
semantics. A verb earns a place in `libdatax` only if it passes all
three tests:

1. **Commonality** — it appears in most application archetypes
   ({doc}`api-application-mapping`), not one.
2. **Portability** — it is implementable on both targets, or degrades
   through a capability flag without changing shape.
3. **Timeability** — it has meaningful immediate *and* timed semantics,
   or is explicitly and documentedly untimeable (its command class per
   {doc}`timing-synchronization`).

Everything that fails the tests stays reachable through the raw
`iio_context` escape hatch — hidden by default, never walled off
({doc}`non-goals`).

The admission path every candidate verb walks:

```{mermaid}
graph TD
    V[candidate verb] --> C{common across<br/>archetypes?}
    C -->|no| ESC[stays behind the<br/>iio_context escape hatch]
    C -->|yes| P{portable to both targets,<br/>or degrades via<br/>capability flag?}
    P -->|no| ESC
    P -->|yes| T{timeable — or documented<br/>untimeable with its<br/>command class?}
    T -->|no| ESC
    T -->|yes| IN[ships in libdatax —<br/>roughly twenty verbs]
```

## The entire surface

The proof of focus is that it fits in one table. Excluding
create/destroy pairs and getters, the complete v1 verb set:

| Object | Verbs |
|---|---|
| `datax_context` | `create_from_uri` · `get_device` · `get_iio_context` |
| `datax_device` | `set_frequency(t)` · `set_gain(t)` · `set_sample_rate` · `set_bandwidth` · `stage_hop_table` · `get_time` · `set_time_next_pps` · `run_mcs` · `get_caps` |
| `datax_stream` | `start` · `start_at(t)` · `stop` · `recv` / `send` · `get_block` / `put_block` |
| `datax_sched` | `queue_gpio/tune/marker/stream_gate(t)` · `commit` · `wait` · `get_completions` · `flush` |
| events | `set_event_callback` |

Roughly twenty verbs. Full signatures in {doc}`api-c-core`; Python
idioms in {doc}`api-python`.

## Requirements (REQ-API)

Numbered so the P1 exit criteria and the runnable examples
(REQ-DOC-006) can trace against them.

- **REQ-API-001 — Line-count ceilings for canonical tasks.** Measured
  on the runnable Python examples once they exist: timed capture at a
  PPS edge ≤ 15 lines; phase-coherent dual-chip capture ≤ 20;
  staged hop scan ≤ 25 ({doc}`api-python` holds the reference
  versions). If an example cannot be written inside its ceiling, the
  API — not the example — is wrong (REQ-DOC-001: fix the spec first).
- **REQ-API-002 — No board names in application code.** Applications
  branch on capability flags exclusively. A grep for platform
  identifiers over any shipped example must come back empty.
- **REQ-API-003 — Location transparency.** The same application source
  runs on the SoC and remotely; only the context URI differs.
- **REQ-API-004 — Uniform time semantics.** Every radio verb takes a
  device time (`DATAX_TIME_NOW` for immediate) or is documented
  untimeable with its command class. No verb has timing behavior that
  differs silently between platforms — differences surface as
  capability flags and staging costs, never as changed call shape.
- **REQ-API-005 — Hidden machinery stays hidden.** Applications never
  touch: DMA buffer mechanics, `data_offload` arming, fastlock/FHM
  register programming, Tick descriptor formats or CSV submission,
  JESD bring-up, MCS step sequencing. The SDK owns the mapping
  ({doc}`architecture-proposal`); the archetype walkthroughs list what
  each application did *not* have to write.
- **REQ-API-006 — Graceful degradation.** Absence of a capability
  downgrades the timing class of a call (hard-timed → software-timed)
  or fails it loudly at submit — it never changes the calling
  convention. Feature-gated code reads as `if "timed_commands" in
  dev.caps:`, not as a second API.
- **REQ-API-007 — Escape hatch, always.** `datax_context_get_iio_context()`
  is guaranteed present and supported; using it voids no warranty on
  the rest of the context.
- **REQ-API-008 — Loud failure.** Late commands, underflow, sequence
  gaps, and queue overflow are events and error codes
  ({doc}`api-object-model`), never silent best-effort. An application
  that ignores events still gets failed return codes on the calls that
  mattered.
- **REQ-API-009 — One mental model across bindings.** The Python
  binding adds idiom (properties, context managers, numpy), never
  semantics: any behavior expressible in Python is expressible in C
  with the same object lifecycle.

## What this buys the application author

The measurable end state, restated from the application's side of the
API: a working SDR application is the *composition of verbs*, not the
orchestration of infrastructure. The archetype pages
({doc}`api-application-mapping`) hold this claim to account — every
archetype must be expressible in the verb table above, and anything it
lacks goes through the spec-change process rather than a per-app
workaround.
