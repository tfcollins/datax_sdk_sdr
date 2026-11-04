# Support Matrix

This page is *reference*. One table lists, per hardware platform, every
feature a repository claims for it, which repository backs the claim,
at which test tier of {doc}`requirements-test`, and where the evidence
is. Status words are the three of {doc}`requirements-documentation`:
*validated*, *integration artifacts*, *planned*.

The table is **rendered, not written**. Each repository owns a
`support.json` manifest that its own CI checks fail-closed (a
*validated* row must name a workflow that exists there and link
durable evidence). The SDK pins the manifests in `sources.json`,
renders them into `docs/_generated/` with `datax-support render`, and
a CI job fails if the committed fragments are stale. A nightly
re-renders from branch tips, checks that every *validated* row's
workflow last passed, and link-checks the evidence; drift opens the
issue "support matrix: drift/red". The design is
`specs/2026-11-03-support-matrix-and-planning-hub-design.md`.

## Projects

- **tick** — FPGA-resident timed-command scheduler: Python wire model,
  RTL, IIO kernel driver, UAPI. <https://tfcollins.github.io/tick/>
- **vrt49** — VITA 49.2 stack: C library, libiio host backend,
  `iiod-vrt49` daemon, framer/deframer HDL, kernel buffer driver,
  reference designs. <https://github.com/tfcollins/vrt49> (private;
  its evidence links resolve only for collaborators and are marked).
- **libiio** — the `daqiri:` backend on the `feature/daqiri-udp` branch
  of the libiio fork: high-rate UDP sample receive through NVIDIA
  DAQIRI, plus the `iiod` UDP stream setup command. Its rows are
  software-validated and say so. The platform is `host`.
  <https://github.com/tfcollins/libiio/tree/feature/daqiri-udp>
- **hopcap** — composite application on the ADRV9009-ZU11EG:
  Tick-timed Talise FHM hop with hardware-gated VRT49 capture over
  QSFP. <https://tfcollins.github.io/hopcap/>

## By platform

Rows are grouped by platform, then feature, then project; a feature
that two projects back on the same board appears once per project.

```{include} _generated/support-by-platform.md
```

## What "validated" means here

*Validated* means tier 2 or tier 3 of {doc}`requirements-test` passed
on the named hardware with evidence a reader can open; a row whose
validation is software-only says so in its status cell. Tier names
the highest test tier that ran for the row; status names what it
proved. The capability-level view of the same data sits under the
matrix in {doc}`api-object-model`.
