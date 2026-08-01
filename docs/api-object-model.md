# API Object Model

The concepts behind the C surface in {doc}`api-c-core` and the Python
surface in {doc}`api-python`. The *why* behind the surface's size — and
the requirements that police it — live in {doc}`api-design-goals`; how
applications compose it is {doc}`api-application-mapping`. This page is
the canonical home of the capability matrix — other pages link here
rather than duplicating it.

## Design principles

`libdatax` is **libiio-idiomatic**, because its users already know libiio
and its maintenance model has proven out:

- opaque handles, `_create` / `_destroy` pairs, no exposed structs;
- integer error returns (negative errno), out-parameters for values;
- `_get_` / `_set_` accessor naming;
- no global state; every object hangs off a context;
- the raw `iio_context` is always reachable — hiding is a default, not a
  wall ({doc}`non-goals`).

Two additions libiio does not have, both load-bearing:

- **time as an argument** — most verbs accept a device time, with
  `DATAX_TIME_NOW` for immediate execution;
- **capabilities as data** — applications branch on flags, never on
  board names.

## Object hierarchy

```{mermaid}
classDiagram
    class datax_context {
        create_from_uri(uri)
        get_device_count()
        get_device(index)
        get_iio_context()
    }
    class datax_device {
        set_frequency(ch, hz, time)
        set_gain(ch, db, time)
        get_time()
        set_time_next_pps(epoch)
        run_mcs()
        get_caps()
    }
    class datax_stream {
        start()
        start_at(time)
        recv(block, timeout)
        send(block, timeout)
        stop()
    }
    class datax_sched {
        queue_at(time)
        commit()
        wait(seq, timeout)
        get_completions()
    }
    class datax_caps {
        has(flag)
        limits()
    }
    datax_context "1" --> "*" datax_device : owns
    datax_device "1" --> "*" datax_stream : creates
    datax_device "1" --> "0..1" datax_sched : creates
    datax_device "1" --> "1" datax_caps : describes
```

Ownership is strictly top-down: destroying a context destroys its
devices; destroying a device stops and destroys its streams and
scheduler. A `datax_device` is one radio — on the ZU11EG the dual
ADRV9009s present as **one device** with four RX / four TX channels,
because that is the phase-coherent unit the application reasons about
(MCS, {doc}`timing-synchronization`).

## Threading model

- Context and device calls are thread-safe (internally locked).
- A stream is owned by one thread at a time; `recv`/`send` are blocking
  with timeouts. One thread per stream is the intended pattern.
- The scheduler's completion poller runs on an SDK-internal thread; the
  event callback fires on that thread and must not block.

## The time model

`datax_time` is a 64-bit tick count against the device's Tick counter:

- `datax_device_get_time()` → `{ticks, tick_hz}` — the rate is always
  queried, never assumed;
- second ↔ tick conversion helpers take the queried rate;
- `DATAX_TIME_NOW` (0) means immediate execution on the software path —
  no descriptor is queued;
- times are absolute. Relative scheduling is a client-side convenience
  (`now + offset`) in the Python layer.

## The error model

- Every call returns 0 or a negative errno; extended detail via
  `datax_context_get_last_error()` (message + subsystem).
- **Timing failures are first-class.** `DATAX_ERR_LATE` (deadline
  unmeetable at submit), `DATAX_EVT_LATE_COMMAND` (Tick detected late at
  dispatch), and `DATAX_EVT_QUEUE_OVERFLOW` map Tick's late/overflow
  counters into the API. A late command is never silently executed —
  this deliberately diverges from UHD's silent-late behavior
  ({doc}`background-prior-art`).
- Stream data errors (overflow, underflow, discontinuity) are delivered
  per-block, not as global state.

## Capability discovery

A `datax_caps` object is a set of flags plus numeric limits, built from a
compiled per-platform table refined by probing the live IIO context at
startup (Tick device present? `data_offload` with `sync_ext`? `mqnic`
netdev? tagger in the datapath?).

Flags in v1:

| Flag | Meaning |
|---|---|
| `DATAX_CAP_TIMED_COMMANDS` | Tick scheduler present; `sched` object available |
| `DATAX_CAP_RX_ARM` / `DATAX_CAP_TX_ARM` | Timed stream start via arm/release |
| `DATAX_CAP_STREAM_GATE` | Hard-timed gating of running streams |
| `DATAX_CAP_TIMESTAMPS` | In-band capture timestamps (stream tagger) |
| `DATAX_CAP_FASTLOCK_HOP` | Pre-staged tuning via AD936x fastlock |
| `DATAX_CAP_FHM_HOP` | Pre-staged tuning via ADRV9009 Talise FHM |
| `DATAX_CAP_MCS` | Multi-chip sync; `run_mcs()` supported |
| `DATAX_CAP_PHASE_COHERENT` | *Current* coherence state (false until MCS runs) |
| `DATAX_CAP_NET_OFFLOAD_NIC` | Corundum NIC fitted (control/telemetry plane) |
| `DATAX_CAP_NET_OFFLOAD_SAMPLES` | RF-sample offload path (roadmap; always false in v1) |

Limits carried alongside: hop-table depth (8 fastlock profiles / FHM
table size), scheduler queue depth, tick rate, guard margin, max
channel-mask width.

## Capability matrix (canonical)

Capabilities by platform *and phase* — the phase gates are defined in the
{doc}`roadmap`:

| Capability | ADRV9361-Z7035 | ADRV9009-ZU11EG |
|---|---|---|
| Streaming (immediate) | P2 | P2 |
| `TIMED_COMMANDS` | P4 — new Tick port | P3 — Tick HW validation |
| `RX_ARM` / `TX_ARM` | P4 | P3 |
| `STREAM_GATE` | P4 | P3 |
| `TIMESTAMPS` | P4 | P3 |
| `FASTLOCK_HOP` | P4 | — (n/a) |
| `FHM_HOP` | — (n/a) | P3 |
| `MCS` | — (single chip) | P3 |
| `PHASE_COHERENT` | — | P3 (post-MCS state) |
| `NET_OFFLOAD_NIC` | P5 — new GTX wrapper (highest-risk) | P5 — upstream `CORUNDUM=1` exists |
| `NET_OFFLOAD_SAMPLES` | P6 — subsets only | P6 |

"P*n*" = the capability turns on when that roadmap phase exits its
acceptance criteria on that platform; "—" = structurally not applicable.
Full API parity between the two boards is the P4 exit milestone.
