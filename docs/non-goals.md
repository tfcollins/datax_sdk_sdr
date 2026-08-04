# Non-Goals

Scope boundaries for the first releases. Each of these is a deliberate
decision, not an oversight; several may become goals in later phases.

## No UHD API compatibility shim

The SDK targets UHD's *expressiveness*, not its API. A `multi_usrp`
adapter layer would import UHD's semantics (motherboard/daughterboard
model, property tree) that do not map cleanly onto IIO. Applications
migrate by analogy, not by recompilation.

## Not a libiio replacement

libiio remains the transport and control substrate. `libdatax` is a layer
on top, and raw `iio_context` / `iio_device` escape hatches stay available
(`datax_context_get_iio_context()`) so anything the SDK does not model is
still reachable.

## No PTP time discipline in v1

Inherited from Tick: device time is disciplined by PPS + 10 MHz (or
free-runs). The architecture leaves room for a PTP-backed timing authority
— Corundum even ships PTP support in its NIC datapath — but v1 does not
implement or expose it.

## No per-sample command granularity

Tick dispatches state changes at fabric-clock (AXI-Lite) edges, not at the
converter sample edge. Per-sample I/Q manipulation (chirps, per-sample
gain ramps) is the converter's or the DSP fabric's job, not the
scheduler's.

## No GNU Radio blocks in v1

The Python bindings are the integration surface. A `gr-datax` out-of-tree
module is a natural later addition once the Python API is stable.

## Linux hosts only in v1

Host-side support targets Linux (x86_64 and the on-SoC ARM cores). No
Windows or macOS host libraries in v1, although libiio's network backend
means nothing precludes them later.

## Two target platforms only

ADRV9361-Z7035 and ADRV9009-ZU11EG. Other ADI platforms (Pluto, FMCOMMS
carriers, MxFE evaluation boards) are explicitly out of scope for v1, even
where Tick already has collateral for them. The capability-flag model
({doc}`api-object-model`) is designed so new platforms are additive.

## No RF-sample-over-Ethernet in the MVP

The Corundum integration ships as a NIC / control / telemetry plane first.
Direct RF-sample packetization through the Corundum application section is
a designed-but-deferred phase with its own gate in the {doc}`roadmap` —
the bandwidth budget and the required packetizer HDL are real engineering
efforts, not configuration.
