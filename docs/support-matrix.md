# Support Matrix

This page is *reference*. For each repository the SDK builds on, it
lists the platforms the repository supports, which features, at which
test tier of {doc}`requirements-test`, and where the evidence is.
Status words are the three of {doc}`requirements-documentation`:
*validated*, *integration artifacts*, *planned*. The table is
hand-maintained today, checked against the repositories on
2026-11-03; the next sub-project of
`specs/2026-11-03-support-matrix-and-planning-hub-design.md` replaces
it with a table rendered from manifests the repositories own.

Evidence links go to public documentation sites where one exists
(tick, hopcap) and to source files on GitHub otherwise. The vrt49
repository is private, so its links resolve only for collaborators.

## Tick

FPGA-resident timed-command scheduler: Python wire model, RTL, IIO
kernel driver, UAPI. <https://tfcollins.github.io/tick/>

| Platform | Feature | Status | Tier | Evidence |
|---|---|---|---|---|
| AD9081-FMCA-EBZ / ZCU102 (`mini2`) | timed GPIO, timed capture, NCO FFH hop PoC | validated | 2 | [supported targets](https://tfcollins.github.io/tick/index.html), [timed GPIO staircase](https://tfcollins.github.io/tick/example-timed-gpio-staircase.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | scheduler | validated | 2 | [ZU11EG bring-up](https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timed Talise FHM hop (edge timing and PLL readback; no RF settle measurement) | validated | 2 | [FHM hop](https://tfcollins.github.io/tick/adrv9009-fhm-hop.html) |
| ADRV9009 / ZC706 (`nemo`) | scheduler | validated | 2 | [ZC706](https://tfcollins.github.io/tick/adrv9009-zc706-hop.html) |
| ADRV9009 / ZC706 (`nemo`) | FHM hop | planned | — | [ZC706](https://tfcollins.github.io/tick/adrv9009-zc706-hop.html) |
| ADALM-Pluto | scheduler, fastlock hop | integration artifacts | 1 | [Pluto fastlock hop](https://tfcollins.github.io/tick/pluto-fastlock-hop.html) |

## vrt49

VITA 49.2 stack: C library, libiio host backend, `iiod-vrt49` daemon,
framer/deframer HDL, kernel buffer driver, reference designs.
Repository: <https://github.com/tfcollins/vrt49> (private).

| Platform | Feature | Status | Tier | Evidence |
|---|---|---|---|---|
| ADRV9009-ZU11EG, Corundum 10G SFP+/QSFP+ | VITA 49.2 RX framing over UDP, `iiod-vrt49`, host backend | validated (9/9 qualification on `tron`) | 2 | [hardware results](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/hw-results-zu11eg.md), [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9009zu11eg.md) (private) |
| ADRV9361-Z7035, 1G SFP | VITA 49.2 RX over 1G, vendored Tick, fastlock hop controller | integration artifacts (control and transport qualified; RF settle unresolved) | 2 | [Tick hop examples](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md) (private) |
| ADRV9361-Z7035, CCFMC LVDS | VITA 49.2 framing to host DMA | integration artifacts | 1 | [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9361z7035_ccfmc.md) (private) |
| ADRV9002 / ZCU102 | 4x10G striped UDP | integration artifacts (exact-boot HIL exists, last run failed) | 2 | [4x10G guide](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/adrv9002-zcu102-4x10g.md) (private) |
| AD9081 / ZCU102 | VITA 49.2 framing | integration artifacts | 1 | [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/ad9081_zcu102.md) (private) |
| AD-FMCOMMS2 / ZCU102 | full-duplex framer/deframer over AXI DMA | integration artifacts | 1 | [project page](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/fmcomms2_zcu102.md) (private) |
| VCU118 + FMCDAQ3 | 100G RoCEv2 full rate (39.5 Gb/s, 600 s soak) | validated | 2 | [VCU118 RoCEv2](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/vcu118-rocev2.md) (private) |
| VCU118 + FMCDAQ3 | 100G UDP to the DAQIRI receiver | integration artifacts | 1 | [DAQIRI receiver](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/daqiri-receiver.md) (private) |

## libiio (daqiri branch)

The `daqiri:` backend on the `feature/daqiri-udp` branch of the libiio
fork: high-rate UDP sample receive through NVIDIA DAQIRI, plus the
`iiod` UDP stream setup command and `iiod-emu --udp`.
Repository: <https://github.com/tfcollins/libiio/tree/feature/daqiri-udp>

| Platform | Feature | Status | Tier | Evidence |
|---|---|---|---|---|
| host, any NIC | `daqiri:` backend, UDP sample mode, socket engine | validated (software: unit, emulator, loopback in CI) | 1 | [backend guide](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/doc/source/daqiri-backend.md) |
| host, ConnectX-5 | raw DPDK / ibverbs queues | integration artifacts (implemented, not carrying sample mode; lab-host-only tier) | 1 | [test matrix](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |
| any sender | `IIOD_OP_UDP_STREAM_SETUP`, `iiod-emu --udp` | validated (software) | 1 | [test matrix](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |

## hopcap

Composite application on the ADRV9009-ZU11EG: Tick-timed Talise FHM
hop with hardware-gated VRT49 capture over QSFP.
<https://tfcollins.github.io/hopcap/>

| Platform | Feature | Status | Tier | Evidence |
|---|---|---|---|---|
| ADRV9009-ZU11EG (`tron`) | Tick-timed FHM hop, hardware-gated VRT49 capture over QSFP, Context with hop frequency, sample-exact VRT timestamps, SigMF export | validated | 2 | [first tron run](https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html), [VRT timestamps](https://tfcollins.github.io/hopcap/reports/2026-10-25-tron-vrt-timestamps.html) |
| ADRV9009-ZU11EG (`tron`) | measured Talise settle time | planned (settle is a configured knob) | — | [example](https://tfcollins.github.io/hopcap/example.html) |

## What "validated" means here

*Validated* means tier 2 or tier 3 of {doc}`requirements-test` passed
on the named hardware with evidence a reader can open; a row whose
validation is software-only says so in its status cell. Cells go
stale: this table reflects the repositories on 2026-11-03, and the
manifest pipeline in the next sub-project is what keeps it current.
