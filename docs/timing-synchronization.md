# Timing and Synchronization

The SDK's timing model is Tick's timing model, surfaced through the API.
This page specifies device time, its discipline modes, the command-class
taxonomy as it applies to each platform, timed tuning mechanics, and
multi-chip synchronization on the ADRV9009-ZU11EG.

## Device time

Each platform carries one **64-bit device-time counter** in FPGA fabric,
owned by the Tick scheduler. The counter increments at a synthesis-time
tick rate (100 MHz on every current Tick target — 10 ns resolution). The
driver reports the rate, and the API never assumes it:

- `datax_device_get_time()` returns `{ticks, tick_hz}`;
- helpers convert seconds ↔ ticks using the *reported* rate;
- `DATAX_TIME_NOW` is the sentinel for immediate execution.

The scheduling horizon is bounded by 2⁶⁴ ticks (millennia at 100 MHz) but
practically by the command FIFO depth and the late-command rules
({doc}`api-c-core`).

## Time discipline

Three modes, in increasing order of usefulness:

| Mode | Behavior | Good for |
|---|---|---|
| Free-run | Counter starts at reset, drifts with the fabric oscillator | Single-board relative timing |
| PPS-aligned | `datax_device_set_time_next_pps(epoch)` loads an epoch on the next PPS edge | Multiple boards agreeing on "now" |
| PPS + 10 MHz disciplined | Counter clocked from the shared reference; PPS aligns the epoch | Long captures, cross-board schedules |

PTP-backed discipline is explicitly deferred ({doc}`non-goals`), matching
Tick. The API exposes discipline state read-only: `pps_present`,
`time_aligned`, and the measured tick rate (Tick's ZC706 bring-up
measured 99.9975 MHz against the reference — the API reports what the
hardware measures, not the nominal number).

## Command classes

The Tick taxonomy, restated as the API contract:

| Class | Guarantee | SDK calls that use it |
|---|---|---|
| **Hard-timed** | Fires on an exact device-time tick, in fabric | `stream_start_at` / `stop_at` (stream gates, capture/transmit arm), `sched.at(t).gpio(...)`, `.marker(...)`, TDD sync |
| **Pre-staged** | Software stages converter state ahead; a hard-timed GPIO edge applies it | `sched.at(t).tune(...)` — fastlock select (Z7035), FHM hop (ZU11EG) |
| **Software-timed** | Best-effort; recorded, not guaranteed | `sched.at(t).attr_write(...)` for slow controls (gain ramps, port switches) |

Only hard-timed actions are advertised as sample-clock deterministic.
The capability flags ({doc}`api-object-model`) tell an application which
class a given operation gets *on this platform* — the same
`sched.at(t).tune(f)` call is pre-staged on both targets but with
different staging costs and profile-count limits.

The three classes on one time axis:

```{mermaid}
graph LR
    subgraph HT ["hard-timed"]
        H1[queued descriptor] --> H2[fires on exact tick T<br/>fabric edge, 10 ns step]
    end
    subgraph PS ["pre-staged"]
        P1[converter state staged<br/>at T − margin, untimed] --> P2[hard-timed GPIO edge<br/>applies it exactly at T]
    end
    subgraph SW ["software-timed"]
        S1[host writes near T] --> S2[lands inside a<br/>Linux jitter band]
    end
```

Late commands are a first-class error: Tick detects
`timestamp < device_time` at dispatch, counts it, and the SDK surfaces it
through the completion path and the event callback — never a silent
immediate execution ({doc}`api-c-core`).

## Timed tuning per platform

"Tune at time T" is the signature SDR request and the clearest example of
the pre-staged class. The two targets implement it with different
converter mechanisms, both triggered by a Tick hard-timed GPIO edge:

### ADRV9361-Z7035 — AD9361 fastlock

The AD9361 stores up to **8 fastlock profiles** (complete PLL states) per
PLL. The SDK pre-loads profiles for the hop set, then a Tick `GPIO_WRITE`
drives the CTRL_IN pins that select the active profile at T. Settling
after the edge is the PLL's fastlock switch time (tens of microseconds),
not a full re-lock. Costs the application must plan around:

- profile load is milliseconds-scale and *not* timed — stage early;
- the hop set is limited to 8 frequencies without reloading;
- this is the exact mechanism of Tick's Pluto port, ported to the Z7035
  ({doc}`platform-adrv9361-z7035`).

### ADRV9009-ZU11EG — Talise FHM

The ADRV9009's frequency-hopping mode (FHM) is configured through the
Talise API; a designated ARM GPIO then triggers hops. The SDK stages the
hop table, and a Tick `GPIO_WRITE` fires the hop edge at T. The hop range
and settling behavior come from the Talise FHM constraints; on the dual
transceiver both chips must hop coherently, which folds into MCS below.

## Multi-chip sync (ADRV9009-ZU11EG)

The ZU11EG SOM carries **two ADRV9009s** behind an HMC7044 clock
distributor. Phase-coherent 4R4T operation requires multi-chip sync:

```{mermaid}
graph TD
    REF[PPS + 10 MHz reference] --> HMC[HMC7044<br/>SYSREF + device clocks]
    HMC --> A[ADRV9009 A]
    HMC --> B[ADRV9009 B]
    HMC --> FPGA[FPGA — JESD204B<br/>deterministic latency]
    A --> JESD[JESD204B links]
    B --> JESD
    FPGA --> TICK[Tick device time]
```

The contract the SDK enforces:

1. `datax_device_run_mcs()` executes the MCS sequence (HMC7044 SYSREF
   pulses, Talise MCS steps, JESD204B link re-establishment with
   deterministic latency).
2. The `DATAX_CAP_PHASE_COHERENT` capability reports *current* coherence
   state, not board ability — it is false until MCS has run.
3. Phase-coherent streams (channel masks spanning both chips) refuse to
   start until MCS has completed; the error is explicit, not a silent
   phase ambiguity.
4. Tuning either chip invalidates coherence until re-MCS (fastlock/FHM
   hops within a staged table preserve it; the capability matrix carries
   the exact rules).

## Cross-board synchronization

Nothing SDK-specific: share the PPS + 10 MHz reference, align epochs with
`set_time_next_pps`, and schedule against the common timeline. Tick
`MARKER_PULSE` outputs give a scope-verifiable alignment check — the test
requirements ({doc}`requirements-test`) use exactly this for evidence
artifacts.
