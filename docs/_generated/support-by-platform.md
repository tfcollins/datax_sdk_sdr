| Platform | Feature | Project | Status | Tier | Evidence |
|---|---|---|---|---|---|
| AD9081-FMCA-EBZ / ZCU102 (`mini2`) | timed capture | tick | validated | 2 | [evidence](https://tfcollins.github.io/tick/example-timed-capture.html) |
| AD9081-FMCA-EBZ / ZCU102 (`mini2`) | timed GPIO | tick | validated | 2 | [evidence](https://tfcollins.github.io/tick/example-timed-gpio-staircase.html) |
| AD9081-FMCA-EBZ / ZCU102 (`mini2`) | VITA 49.2 over UDP, 10G | vrt49 | integration artifacts | 1 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/ad9081_zcu102.md) (private repository) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Corundum NIC | vrt49 | validated | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/hw-results-zu11eg.md) (private repository) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Talise FHM hop (Tick-timed Talise FHM hop with hop frequency and epoch in a hardware Context packet) | hopcap | validated | 2 | [evidence](https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Talise FHM hop (edge timing and PLL readback; no RF settle measurement) | tick | validated | 2 | [evidence](https://tfcollins.github.io/tick/adrv9009-fhm-hop.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | stream gate (vrt49_fhm_hop_ctrl gates sample admission after a settle delay) | hopcap | validated | 2 | [evidence](https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | stream gate (fabric hop gating is exercised by hopcap) | vrt49 | integration artifacts | 1 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9009zu11eg.md) (private repository) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timed capture (Talise settle time is a configured knob, not a measurement) | hopcap | planned | — | — |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timed GPIO | tick | validated | 2 | [evidence](https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timestamps (sample-exact VRT timestamps on the QSFP path) | hopcap | validated | 2 | [evidence](https://tfcollins.github.io/hopcap/reports/2026-10-25-tron-vrt-timestamps.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timestamps | vrt49 | validated | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/hw-results-zu11eg.md) (private repository) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | VITA 49.2 over UDP, 10G (QSFP lane 0 to the host spooler) | hopcap | validated | 2 | [evidence](https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html) |
| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | VITA 49.2 over UDP, 10G | vrt49 | validated | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/hw-results-zu11eg.md) (private repository) |
| ADRV9009 / ZC706 | Talise FHM hop | tick | planned | — | — |
| ADRV9009 / ZC706 | timed GPIO (scheduler validated by hand on the ZC706 (README); no CI workflow targets this board yet) | tick | integration artifacts | 2 | [evidence](https://tfcollins.github.io/tick/adrv9009-zc706-hop.html) |
| ADRV9361-Z7035 | AD936x fastlock hop (control and transport qualified; RF settle unresolved) | vrt49 | integration artifacts | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md) (private repository) |
| ADRV9361-Z7035 | timed GPIO | vrt49 | integration artifacts | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md) (private repository) |
| ADRV9361-Z7035 | VITA 49.2 framing to host DMA | vrt49 | integration artifacts | 1 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9361z7035_ccfmc.md) (private repository) |
| ADRV9361-Z7035 | VITA 49.2 over UDP, 1G | vrt49 | integration artifacts | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/adrv9361z7035_sfp.md) (private repository) |
| ADRV9002 / ZCU102 (`mini2`) | VITA 49.2 over UDP, 10G (4x10G striped; exact-boot HIL exists) | vrt49 | integration artifacts | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/adrv9002-zcu102-4x10g.md) (private repository) |
| AD-FMCOMMS2 / ZCU102 | VITA 49.2 framing to host DMA | vrt49 | integration artifacts | 1 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/projects/fmcomms2_zcu102.md) (private repository) |
| VCU118 + FMCDAQ3 | VITA 49.2 over RoCEv2, 100G (39.5 Gb/s, 600 s soak, zero protocol errors) | vrt49 | validated | 2 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/vcu118-rocev2.md) (private repository) |
| VCU118 + FMCDAQ3 | VITA 49.2 over UDP, 100G | vrt49 | integration artifacts | 1 | [evidence](https://github.com/tfcollins/vrt49/blob/main/doc/source/how-to/daqiri-receiver.md) (private repository) |
| ADALM-Pluto | AD936x fastlock hop | tick | integration artifacts | 1 | [evidence](https://tfcollins.github.io/tick/pluto-fastlock-hop.html) |
| host | DAQIRI receive, raw DPDK/ibverbs (DPDK and ibverbs raw queues implemented; not yet carrying sample mode; lab-host-only tier) | libiio | integration artifacts | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |
| host | DAQIRI receive, socket engine (UDP sample mode through the DAQIRI socket engine; unit, emulator and loopback tiers in CI) | libiio | validated (software) | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/doc/source/daqiri-backend.md) |
| host | iiod UDP stream setup (IIOD_OP_UDP_STREAM_SETUP and iiod-emu --udp) | libiio | validated (software) | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |
