# DataX SDR SDK

**A streaming-radiohead SDK for ADI SDR platforms.**

DataX SDR SDK provides a simplified API for timed SDR control and streaming
above the existing ADI IIO drivers and HDL reference designs. It combines:

- **libiio** as the transport and control substrate,
- **[Tick](https://tfcollins.github.io/tick/)** — an FPGA-resident timed-command
  scheduler — for hard-timed control (timed tuning, gated streaming, TDD,
  multi-device alignment),
- **[Corundum](https://github.com/corundum/corundum)** FPGA NIC designs for the
  high-speed network plane, with a roadmap path to direct RF-sample offload.

The radio is treated as a *streaming radiohead*: a stream endpoint with a small
set of well-defined, software-controlled functions (tune, gain, stream on/off,
timed actions) — not a register playground.

First targets: **ADRV9361-Z7035** and **ADRV9009-ZU11EG**. Check the
[support matrix](docs/support-matrix.md) for what has actually been tested on
each platform; targeting a board does not imply feature parity.

## Integration hub

Start here for the [SDK architecture](docs/architecture-proposal.md), API
specification, [requirements](docs/requirements-test.md), and
[cross-project roadmap](docs/roadmap.md). This repo owns those contracts and the
published support matrix; the code, build recipes, and test evidence live with
the projects that produce them.

| Project | Owns |
|---|---|
| [libdatax](https://github.com/tfcollins/libdatax) | SDK implementation: C library and Python bindings. |
| [Tick](https://tfcollins.github.io/tick/) | FPGA timed-command scheduler and its software interfaces. |
| [vrt49](https://github.com/tfcollins/vrt49) (private) | VITA 49.2 streaming stack, including host software and FPGA data-path components. |
| [libiio DAQIRI fork](https://github.com/tfcollins/libiio/tree/feature/daqiri-udp) | DAQIRI UDP transport integration. |
| [hopcap](https://tfcollins.github.io/hopcap/) | Composed ZU11EG example: Tick-timed tuning and VRT49 capture, with its own hardware evidence. |
| [datax-manifests](https://github.com/tfcollins/datax-manifests) | CIM workspace recipes for ADI HDL, Linux, and boot firmware. |
| [labgrid-plugins](https://github.com/tfcollins/labgrid-plugins) | Board control, boot and FPGA programming strategies, and reusable hardware CI. |

### Support evidence and release pins

The [support matrix](docs/support-matrix.md) is generated from each project's
support manifest. [`sources.json`](sources.json) pins the inputs to that
render; those revisions are **not** a tested whole-SDK build or release lock.

For example, the
[November 11 libdatax hardware run](https://github.com/tfcollins/libdatax/blob/main/docs/evidence/ci/2026-11-11-tron/README.md)
records ZU11EG streaming on the stock image and timed control on a separate
hopcap SFP image. Those results do not establish one all-features image, RF
phase coherence, or Z7035 parity.

Record release pins separately, per validated platform and image, after the
[release checklist](docs/requirements-process.md#every-release) has been run.
Include the exact source revisions, toolchain and boot artifact hashes, and
link the hardware evidence for that combination.

## Documentation

The rendered site: <https://tfcollins.github.io/datax_sdk_sdr/>

Build locally:

```bash
pip install -r docs/requirements.txt
cd docs && make html
python -m http.server -d _build/html
```

## License

MIT — see [LICENSE](LICENSE).
