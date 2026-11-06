# Python Bindings

The Python package `datax` wraps `libdatax` the way pylibiio wraps
libiio, then adds pyadi-iio-style ergonomics on top. Python is the
primary integration surface for v1 ({doc}`non-goals` — no GNU Radio
blocks yet).

## Binding strategy

- **ctypes (or cffi) over the C ABI** — no compiled extension module;
  the wheel is pure Python and tracks `libdatax.so` versioning, exactly
  the pylibiio model.
- **numpy at the edges** — sample blocks cross the boundary as
  `numpy.complex64` arrays (int16 I/Q converted at the edge; a raw int16
  path exists for throughput-critical code).
- **properties over methods** — pyadi-iio muscle memory:
  `dev.rx_lo = 2.4e9`, not `dev.set_frequency(...)`.
- **context managers** — every object is a `with`-able; teardown order
  follows the C ownership rules.

```{mermaid}
graph LR
    APP[application] --> DX[datax package —<br/>properties, builders,<br/>with-contexts]
    DX --> CA[ctypes bindings —<br/>pure-Python wheel]
    CA --> LD[libdatax.so]
    LD -->|int16 I/Q blocks| CA
    CA -->|numpy complex64;<br/>raw int16 path for<br/>throughput| APP
```

## C → Python mapping

| C | Python | Notes |
|---|---|---|
| `datax_context` | `datax.Context(uri)` | `Context()` = local |
| `datax_device` | `datax.Device` | `ctx.devices[i]` |
| `datax_stream` | `datax.RxStream` / `datax.TxStream` | `dev.rx_stream(...)`, `dev.tx_stream(...)` |
| `datax_sched` | `datax.Scheduler` | `dev.scheduler` (lazy, caps-gated) |
| `datax_caps` | `datax.Capabilities` | `dev.caps`, supports `in` |
| `datax_time` | `int` ticks + `dev.time` helpers | `dev.time.now`, `dev.time.seconds(x)` |
| negative errno | `datax.Error` subclasses | `LateError` (`DATAX_ERR_LATE`), `BusyError` (`-EBUSY`), `DeadlockError` (`-EDEADLK`), `CapabilityError` (`-ENOTSUP`), `OverflowError` |
| `datax_completion` | `datax.Completion` | `.seq`, `.status` (`datax.CompletionStatus`), `.requested_ticks`, `.executed_ticks`, `.detail` |
| `datax_time_source` | `datax.TimeSource` | `dev.time.source` |
| event callback | `ctx.on_event(fn)` | `fn(type, ticks, seq, detail)` with `type` a `datax.EventType`; runs on the scheduler's poller thread, never after `ctx.close()`; must not block (`sched.wait` there raises `DeadlockError`); exceptions are logged and swallowed |

Convenience layer (matching pyadi-iio):

- `dev.rx()` — one-shot capture returning `(samples, timestamp)`;
- `dev.tx(data)` — one-shot or cyclic transmit;
- `dev.rx_lo`, `dev.tx_lo`, `dev.rx_gain`, `dev.sample_rate`,
  `dev.rx_bandwidth` properties.

## Timed-command builder

`sched.at(t)` returns a builder whose calls queue descriptors; `commit()`
submits the batch ({doc}`api-c-core`):

```python
sched = dev.scheduler
t0 = dev.time.now + dev.time.seconds(0.5)

sched.at(t0).marker(line=0)          # scope-visible start edge (unreported)
for i, f in enumerate(hop_plan):
    sched.at(t0 + i * dwell).tune(f)
sched.commit()
sched.wait_all(timeout=2.0)          # raises LateError on any late hop
```

Only reported commands have completions: `tune` reports its hop edge (only
every Nth one when hops are dense), `gpio` and `marker` report with
`report=True`. `wait(seq)` on an unreported command raises `datax.Error`
(`EINVAL`); `wait_all` skips unreported tunes. A rejected `commit()`
(`LateError`, or `Error` `EINVAL` for report spacing) discards the batch.
`dev.stage_hop_table(freqs)` must precede `tune`, and the first tune needs
the guard margin plus a priming lead. Queue dense hops in one commit.
`sched.flush()` cancels everything outstanding and returns the
`Completion` list of the reported commands it ended (`FLUSHED`, plus any
already finished but not yet waited for); those seqs are consumed, so a
later `wait` on them raises `datax.Error` (`EINVAL`).

```python
dev.time.align_next_pps(epoch=0)     # hard on a PPS edge, else soft (host clock)
print(dev.time.source)               # datax.TimeSource.PPS_ALIGNED / SOFT_ALIGNED / FREE_RUN
```

## Worked examples (spec-level)

These are the acceptance examples for the API design — they must read
this cleanly, or the API is wrong. They become runnable in roadmap P3/P4.

### Timed capture at the next PPS

```python
import datax

with datax.Context("ip:analog.local") as ctx:
    dev = ctx.devices[0]
    dev.rx_lo = 2.4e9
    dev.sample_rate = 30.72e6

    dev.time.align_next_pps(epoch=0)          # device time = 0 at PPS edge
    with dev.rx_stream(channels=[0], block_samples=65536) as rx:
        rx.start_at(dev.time.seconds(1.0))    # exactly 1 s after the edge
        samples, ts = rx.recv()
        assert ts == dev.time.seconds(1.0)    # first sample is tick-exact
```

### Phase-coherent dual-chip capture (ADRV9009-ZU11EG)

```python
with datax.Context("ip:zu11eg.local") as ctx:
    dev = ctx.devices[0]                      # dual ADRV9009 = one device
    if "mcs" not in dev.caps:
        raise SystemExit("needs DATAX_CAP_MCS")

    dev.run_mcs()                             # coherence gate — see timing docs
    assert "phase_coherent" in dev.caps       # live state, true only post-MCS

    with dev.rx_stream(channels=[0, 1, 2, 3]) as rx:   # spans both chips
        rx.start_at(dev.time.now + dev.time.seconds(0.1))
        samples, ts = rx.recv()               # (4, N) complex64, one timestamp
```

### Frequency-hop scan (ADRV9361-Z7035, fastlock)

```python
with datax.Context("ip:z7035.local") as ctx:
    dev = ctx.devices[0]
    plan = [2.40e9, 2.42e9, 2.44e9, 2.46e9]  # ≤ 8: fastlock profile limit
    dev.stage_hop_table(plan)                 # untimed, milliseconds — do it early

    sched, dwell = dev.scheduler, dev.time.seconds(0.005)
    t0 = dev.time.now + dev.time.seconds(0.5)
    with dev.rx_stream(channels=[0], block_samples=16384) as rx:
        for i, f in enumerate(plan):
            sched.at(t0 + i * dwell).tune(f)
        sched.commit()
        rx.start_at(t0)                       # capture spans the whole scan
        blocks = [rx.recv() for _ in plan]
    sched.wait_all()                          # every hop confirmed on time
```

## Error handling idioms

```python
try:
    rx.start_at(dev.time.now)                 # inside the guard margin
except datax.LateError as e:
    print(e.requested, e.margin)              # explicit, never a shifted capture
```

`Capabilities` supports feature-gating without board names:

```python
if "timed_commands" in dev.caps:
    schedule_hops(dev)
else:
    fallback_immediate(dev)                   # same code path, degraded timing
```
