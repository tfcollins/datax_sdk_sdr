# Hardware Requirements

Numbered so later phases trace against them. "Per platform" means one
set for the Z7035 rig and one for the ZU11EG rig.

```{mermaid}
graph TD
    TS[timing source —<br/>locked PPS + 10 MHz] --> R1[Z7035 rig]
    TS --> R2[ZU11EG rig]
    TS --> SC[scope — 500 MHz, 4 ch,<br/>triggers from PPS]
    R1 --> SC
    R2 --> SC
    LG[labgrid exporter —<br/>power, console, boot] --> R1
    LG --> R2
    R2 --- NET[dual-port 10 G host NIC,<br/>QSFP+ DAC breakout]
    R1 --- LB[RF loopback per rig —<br/>TX→RX, 30 dB pads]
    R2 --- LB
```

## Lab inventory — per platform

- **REQ-HW-001** — Target board and carrier: ADRV9361-Z7035 on
  ADRV1CRR-FMC (FMC carrier required for the P5 offload work; BOB is
  acceptable through P4), and ADRV9009-ZU11EG on ADRV2CRR-FMC.
- **REQ-HW-002** — Timing source providing locked **PPS + 10 MHz** with
  distribution to every board and to the scope (REQ-HW-003). All timed
  acceptance tests run PPS-disciplined.
- **REQ-HW-003** — Oscilloscope, ≥ 500 MHz bandwidth, ≥ 4 channels, for
  marker/staircase evidence captures; must trigger from the shared PPS.
- **REQ-HW-004** — RF loopback: SMA cabling + fixed attenuators (30 dB
  typical) TX→RX per channel pair; a spectrum view (scope FFT or
  analyzer) for hop-settling measurements.
- **REQ-HW-005** — Boot/console/power control per board (SD mux or
  network boot, UART, switched PDU) — the labgrid exporter contract
  (REQ-TEST-020).
- **REQ-HW-006** — ZU11EG network rig: dual-port 10 G host NIC, QSFP+
  → SFP+ DAC breakout, jumbo-frame capable switch or point-to-point.
- **REQ-HW-007** — Z7035 offload rig (P5 only): SFP+ cage on the FMC
  carrier path + 10 G host port. Deferred until the P5 gate opens.

## Build machines

- **REQ-HW-010** — Vivado version matrix, both required:
  2023.2 (`hdl_2023_r2` — Tick's validated base) and 2025.1
  (`hdl_2026_r1` — Corundum variant). ≥ 64 GB RAM, ≥ 500 GB free disk;
  ZU11EG synthesis needs the larger-device license tier — verify
  entitlement **before** scheduling P3 (a sibling project lost weeks to
  exactly this).
- **REQ-HW-011** — Linux build host for ADI kernel + rootfs per
  platform (may be the Vivado host).
- **REQ-HW-012** — Remote-synthesis capable: builds run headless
  (Tick's six-stage workflow is the model), artifacts fetched to the
  test rack.

## Rack expectations

- **REQ-HW-020** — Both platforms registered as labgrid places with
  power/console/boot drivers, reachable from CI.
- **REQ-HW-021** — Shared timing distribution (REQ-HW-002) reaches
  every rack position; cross-board sync tests assume one reference.
- **REQ-HW-022** — Evidence capture path: scope screenshot export and
  measurement files land in the test-artifacts store automatically
  (REQ-TEST-023).
