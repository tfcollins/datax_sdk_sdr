# C Core API Reference

Prototype-level specification of `libdatax`. Semantics follow the
{doc}`api-object-model`; this page is the contract implementations are
written against ({doc}`requirements-documentation`: every public symbol
appears here before it is implemented).

Conventions: all functions return `int` (0 or negative errno) unless a
handle or count is the documented return; all handles are opaque; `ch`
arguments are channel indices, `mask` arguments are channel bitmasks.

## Types

```c
typedef unsigned long long datax_time;       /* device ticks (see api-object-model) */
#define DATAX_TIME_NOW ((datax_time)0)       /* immediate, software path */

enum datax_direction { DATAX_RX = 0, DATAX_TX = 1 };

#define DATAX_ERR_LATE (-ETIME)              /* deadline unmeetable at submit */

enum datax_cap {                             /* order matches the capability matrix */
    DATAX_CAP_TIMED_COMMANDS, DATAX_CAP_RX_ARM, DATAX_CAP_TX_ARM,
    DATAX_CAP_STREAM_GATE, DATAX_CAP_TIMESTAMPS, DATAX_CAP_FASTLOCK_HOP,
    DATAX_CAP_FHM_HOP, DATAX_CAP_MCS, DATAX_CAP_PHASE_COHERENT,
    DATAX_CAP_NET_OFFLOAD_NIC, DATAX_CAP_NET_OFFLOAD_SAMPLES, DATAX_CAP_COUNT
};
enum datax_limit {
    DATAX_LIMIT_TICK_HZ, DATAX_LIMIT_QUEUE_DEPTH, DATAX_LIMIT_HOP_TABLE_DEPTH,
    DATAX_LIMIT_GUARD_MARGIN_MS, DATAX_LIMIT_MAX_CHANNELS,
    DATAX_LIMIT_REPORT_SPACING_US,          /* min spacing of reported commands (measured) */
    DATAX_LIMIT_HOP_STAGE_US,               /* measured FHM/fastlock staging round trip */
    DATAX_LIMIT_COUNT
};

enum datax_time_source {
    DATAX_TIME_FREE_RUN,      /* internal clock, never aligned */
    DATAX_TIME_PPS_ALIGNED,   /* epoch loaded on a fabric PPS edge */
    DATAX_TIME_SOFT_ALIGNED,  /* aligned to the host clock in software (no PPS) */
    DATAX_TIME_PPS_HOLDOVER   /* was PPS-aligned; PPS lost; running on the internal clock */
};
bool datax_caps_has(const struct datax_caps *caps, enum datax_cap cap);
int  datax_caps_get_limit(const struct datax_caps *caps, enum datax_limit which,
                          unsigned long long *value);

struct datax_event {
    enum datax_event_type type;
    unsigned long long ticks;                /* device time of the event, 0 if unknown */
    long seq;                                /* scheduler sequence id, -1 if none */
    const char *detail;                      /* human-readable, valid during the callback */
};

enum datax_completion_status {
    DATAX_COMPLETION_OK, DATAX_COMPLETION_LATE,
    DATAX_COMPLETION_DROPPED, DATAX_COMPLETION_FLUSHED
};

#define DATAX_VERSION_MAJOR 0                /* mirrored by datax_context_get_version() */
#define DATAX_VERSION_MINOR 1
```

`datax_caps` is opaque, like every other handle; a flag reads true only
when this library can perform the capability on this context, which is
stricter than "the hardware is present". Implementations may expose what
the probe detected through diagnostics (`datax doctor`), never through
`datax_caps_has`.

## Context

```c
int  datax_context_create_from_uri(const char *uri, struct datax_context **ctx);
int  datax_context_create_local(struct datax_context **ctx);
void datax_context_destroy(struct datax_context *ctx);

unsigned int datax_context_get_device_count(const struct datax_context *ctx);
int  datax_context_get_device(struct datax_context *ctx, unsigned int index,
                              struct datax_device **dev);

struct iio_context *datax_context_get_iio_context(struct datax_context *ctx);
const char *datax_context_get_last_error(const struct datax_context *ctx);
int  datax_context_get_version(const struct datax_context *ctx,
                               unsigned int *major, unsigned int *minor);
```

`create_from_uri` accepts any libiio URI (`ip:`, `usb:`, `serial:`,
`local:`) — the radiohead is remote or local with no other code change.
Creation runs capability discovery ({doc}`api-object-model`) once and
caches the result on each device. Only radio families become
`datax_device` objects (AD936x; the ADRV9009 pair folded into one
device), in IIO enumeration order; every other IIO device — monitors,
clock chips, streaming blocks, the Tick scheduler — stays reachable
through `datax_context_get_iio_context()`.

## Device

```c
const char *datax_device_get_name(const struct datax_device *dev);
const struct datax_caps *datax_device_get_caps(const struct datax_device *dev);

/* Radio functions — 'when' is a device time; DATAX_TIME_NOW = immediate. */
int datax_device_set_frequency(struct datax_device *dev, unsigned int ch,
                               unsigned long long hz, datax_time when);
int datax_device_get_frequency(const struct datax_device *dev, unsigned int ch,
                               unsigned long long *hz);
int datax_device_set_gain(struct datax_device *dev, unsigned int ch,
                          double db, datax_time when);
int datax_device_get_gain(const struct datax_device *dev, unsigned int ch, double *db);
int datax_device_set_sample_rate(struct datax_device *dev,
                                 unsigned long long sps);   /* never timed */
int datax_device_get_sample_rate(const struct datax_device *dev,
                                 unsigned long long *sps);
int datax_device_set_bandwidth(struct datax_device *dev, unsigned int ch,
                               unsigned long long hz);
int datax_device_get_bandwidth(const struct datax_device *dev, unsigned int ch,
                               unsigned long long *hz);

/* Hop staging — pre-loads fastlock profiles (Z7035) or the FHM table
 * (ZU11EG). Milliseconds-scale, never timed; stage before scheduling. */
int datax_device_stage_hop_table(struct datax_device *dev,
                                 const unsigned long long *freqs_hz, size_t count);

/* Device time */
int datax_device_get_time(const struct datax_device *dev,
                          unsigned long long *ticks, unsigned long long *tick_hz);
int datax_device_set_time_next_pps(struct datax_device *dev,
                                   unsigned long long epoch_ticks);
int datax_device_get_time_source(const struct datax_device *dev,
                                 enum datax_time_source *src);

/* Multi-chip sync (DATAX_CAP_MCS) */
int datax_device_run_mcs(struct datax_device *dev);
```

A timed `set_frequency` requires a staged hop table containing the target
frequency; otherwise it returns `-EINVAL` with extended error "frequency
not staged".

**Device time and PPS.** Device time is the scheduler's free-running
counter on the fabric's internal clock. It runs, and every timed call
works, without any PPS. `set_time_next_pps(epoch)` aligns on the next PPS
edge when the hardware sees one within 2 s, and the source becomes
`PPS_ALIGNED`. Otherwise it **falls back** instead of failing:
- libdatax aligns to the host clock in software, accurate to about one
  network round trip, and the source becomes `SOFT_ALIGNED`;
- the call still returns 0;
- `DATAX_EVT_PPS_LOCK_CHANGE` fires, naming the fallback.

The software offset is applied wherever device time crosses the API.
Losing PPS after alignment gives `PPS_HOLDOVER`. A PPS that appears later
never makes time jump; its event only says that a hard alignment is now
possible. "PPS" means whatever drives the scheduler's PPS input. On the
ZU11EG hopcap image, that is an external PPS when one is connected, and
otherwise Corundum's free-running PTP second. Either way it is not GNSS
time unless an external GNSS PPS is wired.

**Hop staging.** `stage_hop_table` records the set of frequencies a timed
tune may use (up to `DATAX_LIMIT_HOP_TABLE_DEPTH`). On the ZU11EG it
enables Talise FHM. The engine is one stage deep, so the scheduler emits a
priming edge, which lands on the chip's FHM initial frequency, and keeps
one frequency staged ahead. Every tune is checked by PLL readback. Hops
need about `DATAX_LIMIT_HOP_STAGE_US` between them. Timed tunes are
supported on the channels whose chip has its hop trigger wired to the
scheduler; elsewhere they return `-ENOTSUP` naming the chip.

**MCS.** `run_mcs()` verifies that the JESD204 multi-chip sync sequence
has completed on every chip. It returns 0 when it has, and `-EIO` naming
the chip and the FSM state when it has not. It does not resynchronise
running links. `DATAX_CAP_MCS` means the board supports MCS.
`DATAX_CAP_PHASE_COHERENT` is a live state. It is true only while MCS has
completed, the transceivers' RF PLL phase sync is enabled, and no
single-chip tune has happened since. Without RF PLL phase sync it stays
false, because JESD sync alone does not fix the LO phase between chips. This keeps the pre-staged contract explicit rather than
letting the SDK silently reload profile tables mid-schedule
({doc}`timing-synchronization`).

## Stream

```c
struct datax_stream_config {
    enum datax_direction direction;     /* DATAX_RX or DATAX_TX */
    unsigned int channel_mask;
    size_t block_samples;               /* samples per block, per channel */
    unsigned int block_count;           /* buffers in flight */
    bool cyclic;                        /* TX: repeat from fabric memory */
};

int  datax_stream_create(struct datax_device *dev,
                         const struct datax_stream_config *cfg,
                         struct datax_stream **stream);
void datax_stream_destroy(struct datax_stream *stream);

int datax_stream_start(struct datax_stream *stream);
int datax_stream_start_at(struct datax_stream *stream, datax_time when);
int datax_stream_stop(struct datax_stream *stream);

/* Copying I/O — interleaved int16 I/Q, host order. */
int datax_stream_recv(struct datax_stream *stream, void *dst, size_t samples,
                      struct datax_block_info *info, int timeout_ms);
int datax_stream_send(struct datax_stream *stream, const void *src, size_t samples,
                      int timeout_ms);

/* Zero-copy — borrow the mapped block, return it when done. */
int datax_stream_get_block(struct datax_stream *stream, void **data,
                           struct datax_block_info *info, int timeout_ms);
int datax_stream_put_block(struct datax_stream *stream, void *data);

struct datax_block_info {
    unsigned long long timestamp_ticks; /* first-sample time; 0 if untagged */
    bool discontinuous;                 /* overflow occurred before this block */
    size_t valid_samples;
};
```

### Immediate streaming semantics

- **Sample layout.** Samples are int16 I/Q in host byte order, in the DMA
  frame order: for each sample instant, the enabled radio channels in
  ascending index, each as I then Q. A "sample" in every count is one such
  instant across all enabled channels. There is no scaling or format
  conversion, so the copying and zero-copy paths share one layout. AD9361
  samples are 12 bits sign-extended in 16.
- **One stream per direction per device.** A second `create` in the same
  direction returns `-EBUSY`. `cyclic` is TX only and forces
  `block_count` to 1.
- **`recv`** copies up to `samples` instants and returns the number copied
  (> 0), or `-ETIMEDOUT` if nothing arrived within `timeout_ms`. Any
  `samples` value works with any block size: the stream keeps a cursor
  into the current block. `info` describes the first block the call
  touched.
- **`send`**, one-shot: fills blocks and enqueues each full one; a final
  partial block waits for the next `send`, or is padded with zeros by
  `stop()`. Cyclic: exactly one `send` of at most `block_samples`; exactly
  those `samples` instants repeat until `stop()`; a second `send` returns
  `-EBUSY`. A cyclic stream starts transmitting at that `send`, not at
  `start()`, so enable errors surface there.
- **`get_block`/`put_block`**: RX lends the next filled block, TX lends a
  free one. Blocks go back in the order they were lent (`-EINVAL`
  otherwise, and for a pointer that is not a lent block). When every block
  is lent, `get_block` returns `-EBUSY`, and a failed `get_block` sets
  `*data` to NULL. `stop()` invalidates every lent block. Mixing copying
  and zero-copy calls on one stream returns `-EINVAL`.
- **`send` return value**: the number of instants accepted. It is a
  partial count when the wait for a free block timed out after some data
  was taken, and `-ETIMEDOUT` when none was.
- **`timeout_ms`**: < 0 waits forever, 0 polls, > 0 waits up to that long.
  The bound is approximate: a single libiio block operation waits up to
  the libiio context timeout in force when the stream was created, on
  both the binary and the legacy `iiod` protocol. Polling with 0 is
  unreliable over a binary-protocol `iiod` until a libiio fix lands
  (datax_sdk_sdr#26).
- **Start and stop.** Starting a started stream returns `-EALREADY`;
  stopping a stopped stream returns 0. A later `start()` begins afresh.
  One-shot TX `stop()` drains: it returns 0 once every sample passed to
  `send` has reached the DMA, or `-ETIMEDOUT` (after disabling anyway) if
  a block did not drain within the context timeout. RX `stop()` also
  drains its queued blocks, stopping at the first failure. A stalled
  stream therefore makes `stop()`, `destroy()` and
  `datax_context_destroy()` wait up to one context timeout; with an
  infinite context timeout they can block.
- **Lifetime.** `datax_context_destroy()` destroys the context's streams;
  stream handles are invalid afterwards. Drain results are reported only
  by `stop()`; `destroy()` drains but returns nothing.
- **Threads.** A stream is driven by one thread at a time. Stream I/O
  does not take the context lock (only claiming and releasing the
  device's per-direction slot does), so separate streams can run on
  separate threads. The last error is per context and shared by every
  thread using that context.
- **Mode latch.** A stream's copying-or-zero-copy mode is fixed by its
  first `recv`/`send`/`get_block`/`put_block` call, even one that fails.
- **Overflow.** When the converter core reports a DMA overflow, the next RX
  block is marked `discontinuous`. Over GigE this is the normal case at
  native rates. Where the core's status cannot be read, `discontinuous` is
  always false and `datax doctor` says detection is unavailable.
- `timestamp_ticks` is 0 until the tagger arrives with the timed path (P3).
  Until then `start_at()` returns `-ENOTSUP`.

### Arm semantics (the timed-start contract)

`start_at(T)` is implemented as *arm early, release exactly* — the
`data_offload` block holds the armed DMA until a Tick
`CAPTURE_ARM`/`TRANSMIT_ARM` pulses its `sync_ext` input at T
({doc}`streaming-model`). Contractual consequences:

- all buffers are enqueued and the DMA started **before** T; `start_at`
  fails with `DATAX_ERR_LATE` if T is closer than the guard margin
  (queryable via caps; default 10 ms);
- if the arm descriptor is late at dispatch, the stream errors loudly
  (event + failed start), never a shifted capture;
- `stop()` on an armed-but-unreleased stream cancels the arm and flushes
  the descriptor;
- the first sample of a released RX stream carries timestamp T when the
  tagger is fitted (`DATAX_CAP_TIMESTAMPS`).

## Scheduler

```c
int  datax_sched_create(struct datax_device *dev, struct datax_sched **sched);
void datax_sched_destroy(struct datax_sched *sched);

/* Queue builders — accumulate client-side, in timestamp order. Each
 * returns a sequence id for completion matching. */
long datax_sched_queue_gpio(struct datax_sched *sched, datax_time when,
                            unsigned int mask, unsigned int value);
long datax_sched_queue_marker(struct datax_sched *sched, datax_time when,
                              unsigned int line, unsigned int width_ticks);
long datax_sched_queue_tune(struct datax_sched *sched, datax_time when,
                            unsigned int ch, unsigned long long hz);
long datax_sched_queue_stream_gate(struct datax_sched *sched, datax_time when,
                                   struct datax_stream *stream, bool enable);

/* Mark an already-queued command (by its seq) to report completion. */
int datax_sched_report(struct datax_sched *sched, long seq);

int datax_sched_commit(struct datax_sched *sched);
int datax_sched_flush(struct datax_sched *sched);

int datax_sched_wait(struct datax_sched *sched, long seq, int timeout_ms,
                     struct datax_completion *out);
int datax_sched_get_completions(struct datax_sched *sched,
                                struct datax_completion *out, size_t max,
                                size_t *count);

struct datax_completion {
    long seq;
    enum datax_completion_status status;  /* OK, LATE, DROPPED, FLUSHED */
    unsigned long long requested_ticks;
    unsigned long long executed_ticks;
};
```

### Scheduler semantics

- **One scheduler per device.** A second `datax_sched_create` returns
  `-EBUSY`. A timed device call (`set_frequency` with a `when`) uses the
  device's scheduler and creates it if needed. The scheduler hardware is
  exclusive, so other users of the board's scheduler (applications,
  `iio_attr`) must not run at the same time.
- **Commits stream.** `commit()` accepts any number of queued commands.
  The poller then keeps the hardware queue topped up in timestamp order,
  leaving one entry spare. A command that the host could not write before
  its timestamp minus the guard margin completes `DATAX_COMPLETION_LATE`
  (detail "host could not keep the queue fed") and is never written. A
  command already inside the guard margin when `commit()` is called makes
  `commit()` return `DATAX_ERR_LATE`, and nothing in that batch is written.
- **Late never executes silently.** Commands are queued with drop-on-late.
  A command the hardware finds late completes `LATE` (when reported) and
  is counted, and the count raises `DATAX_EVT_LATE_COMMAND`.
- **Reporting is sparse and spaced.** Only commands marked with
  `datax_sched_report()` produce a completion; `queue_tune` marks its hop
  edge itself. The scheduler hardware holds a reported command while its
  single completion slot is unacknowledged, then records it as on time
  (tfcollins/tick#38). So `commit()` refuses, with `-EINVAL`, reported
  commands closer together than `DATAX_LIMIT_REPORT_SPACING_US`, a value
  measured when the scheduler is created. A completion drained later than
  the next reported command's time marks that command `LATE`, with detail
  "poller lagged". `wait(seq)` on a command that was not reported returns
  `-EINVAL`. A reported command whose completion never arrives completes
  `DROPPED`, with detail naming the scheduler's overflow count.
- **Reserved lines.** On platforms where a scheduler GPIO line triggers
  hops, `queue_gpio` refuses a mask that touches that line (`-EINVAL`);
  only `queue_tune` drives it.
- `queue_stream_gate` and `stream_start_at` return `-ENOTSUP` until a
  platform's timed-stream hardware exists (ZU11EG: P3b).

### Abstracting the Tick submission bottleneck

This section exists because the current kernel interface shapes the API.
Today, the Tick IIO driver accepts **one 48-byte descriptor per sysfs
attribute write** (a CSV of twelve 32-bit words) and reports completions
through a **polled one-entry window** with no interrupt. Naive per-call
submission would bottleneck and lose completions. The SDK therefore:

- **batches** — `queue_*` builders accumulate descriptors client-side,
  sorted by timestamp; `commit()` writes them back-to-back in one pass,
  respecting queue-depth headroom from the capability limits;
- **polls centrally** — one SDK thread drains the completion window into
  a per-scheduler ring sized to the queue depth, acking each entry;
  `wait`/`get_completions` read the ring and never race the hardware
  window;
- **stays replaceable** — the builder/commit shape is exactly what a
  future kernel fast path (chardev bulk submit, IRQ-driven completions —
  a Tick roadmap item) wants. When it lands, `commit()` becomes one
  ioctl and the poller thread retires, **with no API change**.

```{mermaid}
sequenceDiagram
    participant App
    participant SDK as libdatax
    participant DRV as Tick IIO driver
    participant HW as scheduler (fabric)

    App->>SDK: queue_tune / queue_gpio / ... (client-side, sorted)
    App->>SDK: commit()
    SDK->>DRV: descriptor writes, back-to-back, one pass
    DRV->>HW: 48-byte descriptors → command FIFO
    HW-->>DRV: completions (polled one-entry window)
    loop SDK poller thread
        SDK->>DRV: drain + ack window
        SDK->>SDK: append to completion ring
    end
    App->>SDK: wait(seq) / get_completions()
    SDK-->>App: {seq, status, requested, executed}
```

Rates that fit this design: hundreds of commands per commit at
millisecond cadence — hop schedules, TDD frames, capture batches. Not
per-sample control ({doc}`non-goals`).

## Events

```c
enum datax_event_type {
    DATAX_EVT_LATE_COMMAND,
    DATAX_EVT_QUEUE_OVERFLOW,
    DATAX_EVT_STREAM_OVERFLOW,
    DATAX_EVT_STREAM_UNDERFLOW,
    DATAX_EVT_PPS_LOCK_CHANGE,
};

typedef void (*datax_event_cb)(const struct datax_event *evt, void *user);
int datax_context_set_event_callback(struct datax_context *ctx,
                                     datax_event_cb cb, void *user);
```

Callbacks fire on the SDK's poller thread and must not block; a NULL
callback disables delivery (errors remain visible through return codes
and completions).
