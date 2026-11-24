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
  per-block, not as global state: `DATAX_EVT_STREAM_OVERFLOW` and
  `DATAX_EVT_STREAM_UNDERFLOW` are the events, and a block after an
  overflow is marked `discontinuous`.

## Capability discovery

A `datax_caps` object is a set of flags plus numeric limits, built from a
compiled per-platform table refined by probing the live IIO context at
startup (Tick device present? Tick's `stream_gate_map` attribute and
capability bitmap? `data_offload` with `sync_ext` on AD9081? `mqnic`
netdev? tagger in the datapath?). The timed-stream flags are probed from
the image, never from a board table.

Flags in v1:

| Flag | Meaning |
|---|---|
| `DATAX_CAP_TIMED_COMMANDS` | Tick scheduler present; `sched` object available |
| `DATAX_CAP_RX_ARM` / `DATAX_CAP_TX_ARM` | Timed start of that direction (`start_at`): Tick's `stream_gate_map` names the direction's level and mode bits and the capability bitmap has `STREAM_GATE_TARGET` (0x08), with the scheduler working |
| `DATAX_CAP_STREAM_GATE` | Hard-timed gating of running streams: `RX_ARM` or `TX_ARM`. RX mid-stream gating is still `-ENOTSUP` on the ZU11EG; TX gating is supported |
| `DATAX_CAP_TIMESTAMPS` | Block 0 of each release is hardware-stamped in-band: the bitmap has `STREAM_TIMESTAMP` (0x40), the `capture_tag_*` attributes exist and the map names the RX gate. Later blocks are derived |
| `DATAX_CAP_FASTLOCK_HOP` | Pre-staged tuning via AD936x fastlock |
| `DATAX_CAP_FHM_HOP` | Pre-staged tuning via ADRV9009 Talise FHM |
| `DATAX_CAP_MCS` | Multi-chip sync; `run_mcs()` supported |
| `DATAX_CAP_PHASE_COHERENT` | *Current* coherence state (false until MCS runs) |
| `DATAX_CAP_NET_OFFLOAD_NIC` | Corundum NIC fitted (control/telemetry plane) |
| `DATAX_CAP_NET_OFFLOAD_SAMPLES` | RF-sample offload path (roadmap; always false in v1) |

The Tick driver's read-only `stream_gate_map` attribute is populated from
a device-tree property on the Tick node (for example `adi,stream-gate-map
= "rx-dma", "tx-dma", "rx-mode", "tx-mode"`; exact spelling is the
driver's). Absent means no gate is wired and every timed-stream flag is
false. A second `"fhm-b"` entry is what turns on `FHM_HOP` for channels
2-3; until then they keep `-ENOTSUP`. Images without a map (hopcap's
`sfp` image) keep every flag false.

Limits carried alongside: hop-table depth (8 fastlock profiles / FHM
table size), scheduler queue depth, tick rate, guard margin, max
channel-mask width.

## Capability matrix (canonical)

Capabilities by platform *and phase* — the phase gates are defined in the
{doc}`roadmap`:

| Capability | ADRV9361-Z7035 | ADRV9009-ZU11EG | ADRV9009 / ZC706 |
|---|---|---|---|
| Streaming (immediate) | P2 — done (validated 2026-11-23) | P2 — done (validated 2026-11-11) | P2 — done (validated 2026-11-23) |
| `TIMED_COMMANDS` | P4 — Tick in vrt49's 1G SFP design, RF settle open | P3a — done 2026-11-06 (libdatax on Tick) | no phase (no Tick in the stock PL) |
| `RX_ARM` / `TX_ARM` | P4 | P3b — DMA gate (Tick `STREAM_GATE` level), not `data_offload` | no phase |
| `STREAM_GATE` | P4 | P3b (DMA gate; TX gating, RX start-only) | no phase |
| `TIMESTAMPS` | P4 | P3b (oneshot tagger on RX block 0 of each release) | no phase |
| `FASTLOCK_HOP` | P4 | — (n/a) | — (n/a) |
| `FHM_HOP` | — (n/a) | P3a — done, chip A (chip B in P3b, once the map names it) | no phase (needs Tick and the FHM trigger) |
| `MCS` | — (single chip) | P3a — done, verification of the boot-time sequence | — (single chip) |
| `PHASE_COHERENT` | — | false until the device tree enables RF PLL phase sync | — (single chip) |
| `NET_OFFLOAD_NIC` | P5 — 1G SFP shipped; 10G GTX wrapper (highest-risk) | P5 — vrt49 Corundum design validated | no phase |
| `NET_OFFLOAD_SAMPLES` | P6 — subsets only | P6 | no phase |

"P*n*" = the capability turns on in `libdatax` when that roadmap phase
exits its acceptance criteria on that platform; "—" = structurally not
applicable; "no phase" = possible on the silicon but no roadmap phase
targets it (the ZC706 is a streaming board: {doc}`platform-adrv9009-zc706`). Full API parity between the two boards is the P4 exit
milestone. The **infrastructure** behind each cell — what tick, vrt49
and hopcap prove today — is tracked per repository in
{doc}`support-matrix`: on the ZU11EG, `TIMED_COMMANDS`, `FHM_HOP` and
the P5/P6 network rows have validated infrastructure, `STREAM_GATE`
and `TIMESTAMPS` on the VRT path only, and `RX_ARM`/`TX_ARM`, `MCS`
and `PHASE_COHERENT` have none yet; on the Z7035, `TIMED_COMMANDS` and
`FASTLOCK_HOP` are at integration artifacts and the rest is planned.
A cell flips only when both the infrastructure row and the SDK suite
(REQ-TEST-042) are green.

Infrastructure status per cell, rendered from the repositories'
manifests (best status over the features mapped to each capability;
"—" means no repository claims a row yet):

```{include} _generated/capability-infrastructure.md
```
