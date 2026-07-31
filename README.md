# DataX SDR SDK

**A streaming-radiohead SDK for ADI SDR platforms.**

DataX SDR SDK is a planned SDR-optimized, simplified API layered over the
existing ADI IIO drivers and HDL reference designs. It combines:

- **libiio** as the transport and control substrate,
- **[Tick](https://tfcollins.github.io/tick/)** — an FPGA-resident timed-command
  scheduler — for hard-timed control (timed tuning, gated streaming, TDD,
  multi-device alignment),
- **[Corundum](https://github.com/corundum/corundum)** FPGA NIC designs for the
  high-speed network plane, with a roadmap path to direct RF-sample offload.

The radio is treated as a *streaming radiohead*: a stream endpoint with a small
set of well-defined, software-controlled functions (tune, gain, stream on/off,
timed actions) — not a register playground.

First targets: **ADRV9361-Z7035** and **ADRV9009-ZU11EG**, with full feature
parity planned for both.

> **Status: documentation / planning phase.** This repository currently
> contains the architecture proposal, API specification, and hardware / test /
> documentation / support requirements. No SDK code exists yet.

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
