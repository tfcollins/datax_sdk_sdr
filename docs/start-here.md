# Start Here: Why SDR Applications Are Hard

The front door to this documentation, written for engineers new to
SDR application development. It explains, before any architecture,
what makes real SDR applications hard and what this SDK promises to
make easy. This page is *explanation*. One honest note up front:
the project is documentation-first today ({doc}`roadmap`) — this
page describes the experience being designed, not software you can
install yet.

## The five-minute success

Modern SDR hardware ships with genuinely good tooling. With an ADI
radio and pyadi-iio, a newcomer goes from unboxing to spectrum plot
in minutes: connect to the board, set a center frequency, call
`rx()`, FFT the samples, plot. It works on the first try more often
than not, and it is honestly one of the best onramps in embedded
engineering.

That success is real — and it is exactly where the easy part ends.

## The cliff

Every real project eventually needs to say one of three sentences
that the five-minute toolchain cannot say:

- **"At exactly this time."** Start the capture on a GPS pulse
  edge. Transmit only inside your assigned time slot. Fire the next
  hop of a frequency scan at a precise boundary.
- **"On all channels together."** Capture an antenna array where
  the phase relationship *between* channels is the measurement
  itself.
- **"Without ever dropping a sample."** Record for hours, where one
  silent gap quietly invalidates the whole run.

Each sounds like a small step from the working demo. Each is a
wall, and they are walls for different reasons.

### Why "at exactly this time" is a wall

Your program runs on Linux, and a general-purpose OS makes no
promise about *when* anything happens. Between `sleep()` returning
and your capture call reaching the hardware lie scheduler wakeups,
USB or network round-trips, and driver queues — milliseconds of
jitter on a good day. Radio timelines care about microseconds and
nanoseconds. No amount of careful Python closes that gap: the only
fix is to move the *when* into hardware that counts sample clocks,
and let software decide the *what* ahead of time
({doc}`timing-synchronization`).

### Why "on all channels together" is a wall

Two radios — even two channels of one radio — do not naturally
share a clock, a sampling instant, or a phase reference. Making
inter-channel phase *mean something* is a hardware ceremony:
distribute one reference, align sampling edges, synchronize the
converters, and verify the result. Skip a step and the data looks
plausible while the phase is garbage. No software flag fixes an
array that was never aligned.

### Why "without ever dropping a sample" is a wall

A modest 61.44 MSPS complex stream is about 2 Gb/s. Sustaining that
through buffers, buses, and disks is a systems problem — and worse,
the failure mode is silence: a buffer overflows, samples vanish,
and the math downstream just gets quietly wrong. At these rates,
"the app will keep up" is not a plan ({doc}`streaming-model`).

### The reframe

Notice what none of these walls are: your algorithm. They are
infrastructure — timing, synchronization, data movement — and
today every serious SDR project re-solves them from scratch,
badly, on a deadline, before writing the first line of the code it
actually set out to write.

```{mermaid}
graph LR
    DEMO[the five-minute demo —<br/>connect · tune · rx · plot]
    subgraph WALLS ["the three walls"]
        W1["at exactly this time"]
        W2["all channels together"]
        W3["never drop a sample"]
    end
    SDK[this SDK —<br/>the walls become verbs]
    APP[a deployable system —<br/>your algorithm, not plumbing]
    DEMO --> W1 --> SDK
    DEMO --> W2 --> SDK
    DEMO --> W3 --> SDK
    SDK --> APP
```

## What easy would look like

The SDK's goal, stated as the experience it owes you: each wall
becomes roughly one line of code. Timed capture is `start_at(T)`.
Coherence is `run_mcs()` and a capability flag you can check.
Sustained capture is a stream object whose overflow is a loud
event, never a silent gap. The same code runs on every supported
radio — applications branch on capability flags, never board names
— and when the hardware cannot deliver a guarantee, the call fails
loudly at submit instead of pretending.

The contrast, concretely. What you would naively write today:

```python
target = time.time() + 1.0
time.sleep(target - time.time())   # lands... eventually
samples = sdr.rx()                 # late by an unknowable amount —
                                   # and when was sample 0, exactly?
```

What this SDK is being designed to let you write:

```python
dev.time.align_next_pps(epoch=0)            # device time = 0 at PPS
with dev.rx_stream(channels=[0]) as rx:
    rx.start_at(dev.time.seconds(1.0))      # hardware-exact start
    samples, ts = rx.recv()                 # ts = first-sample time
```

Abridged from the worked examples in {doc}`api-python` — the design
target this documentation exists to pin down, with measurable
ceilings on how short these programs must stay
({doc}`api-design-goals`, REQ-API-001).

## Where to go next

- **Why don't existing tools already do this?** The ecosystem gap —
  what UHD, libiio, and Tick each solve — is {doc}`background-prior-art`.
- **What should arriving feel like?** The out-of-box target and the
  processes that guard it, in {doc}`out-of-box-experience`.
- **What do real missions demand?** Radar, EW, direction finding,
  and communications, worked from mission to requirement, in
  {doc}`application-domains`.
- **What is the API being designed?** The focused verb set and its
  acceptance bar in {doc}`api-design-goals`, then the Python
  experience in {doc}`api-python`.
