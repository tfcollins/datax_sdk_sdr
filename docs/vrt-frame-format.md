# VRT Frame Format

The wire contract shared by the RX **packetizer**
({doc}`hdl-datapath-corundum`) and the TX **depacketizer**
({doc}`hdl-datapath-corundum-tx`) — one format, both directions. This
page is the canonical spec; other pages link here rather than
duplicating it (REQ-DOC-009).

```{admonition} Status
:class: note

Proposed v0 layout, aligned to VITA-49.2 signal-data packets as
profiled by DIFI (IEEE-ISTO 4900, the industry standard for I/Q over
IP). Exact class-ID/OUI encodings and any remaining deviations are
pinned at the P6 design review ({doc}`roadmap`). Field positions below
are the design intent, stated so host tooling can be prototyped early.
```

## Design goals

1. **Parseable by commodity tools.** A VITA-49/DIFI-aware host stack
   (or Wireshark dissector) reads these frames without custom code;
   deviations are few and listed at the bottom.
2. **Fixed-function HDL friendly.** No runtime-optional fields: every
   per-stream property (payload size, addresses, timestamp mode) is CSR
   -programmed at configuration time, so the packetizer datapath is a
   constant-shape pipeline.
3. **Timestamps are Tick device time.** Every frame carries the device
   time of its first sample, derived losslessly from the in-band tag
   ({doc}`timing-synchronization`).
4. **Overhead ≤ 2 %** at the standard payload on a jumbo-frame link
   (actual: ≈ 0.9 %, table below).

## Encapsulation stack

Point-to-point link, jumbo frames (9000-byte MTU), IPv4, no VLAN in v1.
All multi-byte fields network byte order (big-endian).

| Layer | Bytes | Notes |
|---|---|---|
| Ethernet II header | 14 | CSR: dst/src MAC, EtherType 0x0800 |
| IPv4 header | 20 | CSR: dst/src IP; no options; DF set |
| UDP header | 8 | CSR: dst/src port — dst port selects the flow (TX classifier) |
| VRT prologue | 28 | 7 × 32-bit words, layout below |
| I/Q payload | 8192 | 2048 samples × 32 bit (standard size) |
| Ethernet FCS | 4 | MAC-generated |

Total frame: 8274 bytes on the wire — comfortably inside a 9000-byte
MTU with headroom for a future trailer or VLAN tag.

## Prologue layout

Seven 32-bit words, VITA-49.2 signal-data packet with stream ID and
class ID:

```{mermaid}
packet-beta
0-3: "Type=0001"
4: "C=1"
5-7: "Ind"
8-9: "TSI=11"
10-11: "TSF=10"
12-15: "Count (mod 16)"
16-31: "Packet size (32-bit words)"
32-63: "Word 1 — Stream ID (CSR per stream)"
64-95: "Word 2 — Class ID: OUI (pinned at P6)"
96-127: "Word 3 — Class ID: info / packet class"
128-159: "Word 4 — Integer timestamp (seconds)"
160-191: "Word 5 — Fractional timestamp, upper 32 (picoseconds)"
192-223: "Word 6 — Fractional timestamp, lower 32 (picoseconds)"
```

Field semantics:

- **Type / C / indicators** — signal-data packet with stream ID
  (`0001`), class ID present. Indicator bits all zero in v1 (no
  trailer).
- **TSI = 0b11 ("other")** — integer seconds of device time:
  `ticks / tick_hz`. When the Tick epoch has been PPS-aligned to UTC
  ({doc}`timing-synchronization`), this *is* UTC seconds; the SDK
  reports which through the stream metadata rather than overloading the
  bit encoding.
- **TSF = 0b10 (real-time, picoseconds)** — 64-bit fractional
  timestamp: `(ticks mod tick_hz) × (10¹² / tick_hz)` ps. At the
  100 MHz baseline tick rate this multiplier is exactly 10 000 — the
  conversion is lossless integer math in fabric, and the host recovers
  ticks exactly. Tick rates that do not divide 10¹² are rejected at CSR
  configuration time rather than rounded silently.
- **Count (4-bit)** — the VITA rolling packet count, per stream. This
  is the *only* sequence field (deviation notes below discuss the
  consequences).
- **Packet size** — total packet length in 32-bit words including the
  prologue; fixed per stream by CSR.
- **Stream ID** — one ID per configured stream (a channel *group*, not
  a channel — see payload ordering).

## Payload

- 16-bit I, 16-bit Q, two's complement, one sample per 32-bit word —
  I in the most significant half.
- Multi-channel streams carry the enabled channels **interleaved in
  ascending channel order** (the `util_cpack`/`upack` order): with
  channels {0, 2} enabled, samples alternate ch0, ch2.
- Standard payload is **2048 samples** (8192 bytes). Payload size is
  CSR-fixed per stream; the depacketizer rejects frames whose length
  disagrees with the configured size.
- The frame timestamp is the device time of **payload sample 0**;
  subsequent samples advance at the stream's sample period. In TX
  scheduled mode the timestamp is the earliest-air-time contract
  ({doc}`hdl-datapath-corundum-tx`).

## Overhead and rate math

Per-frame overhead: 14 + 20 + 8 + 28 + 4 = **74 bytes** against an
8192-byte payload → **0.90 %** — inside the ≤ 2 % budget from
{doc}`streaming-model` with margin.

| Scenario (per direction) | Sample rate on the wire | Frames/s | Throughput incl. overhead |
|---|---|---|---|
| 1 ch × 61.44 MSPS | 61.44 M samples/s | ≈ 30.0 k | ≈ 2.03 Gb/s |
| 2 ch × 61.44 MSPS (interleaved) | 122.88 M samples/s | ≈ 60.0 k | ≈ 4.05 Gb/s |
| 4 ch × 122.88 MSPS subset (ZU11EG) | 491.52 M samples/s | ≈ 240 k | ≈ 16.2 Gb/s — exceeds one 10 G lane; needs subsets or ≥ 25 G |

The 4-bit count at 60 k frames/s rolls over every ≈ 267 µs — a burst
loss longer than 16 frames is ambiguous to the counter alone. The
default TX gap policy (halt on any gap) makes this a non-issue for
coherent waveforms; RX capture tooling should treat count-consistent
long gaps as suspect when frame timestamps jump.

## Depacketizer validation (TX ingress)

Checks applied per frame, in order; failures counted per-stream and
surfaced through events ({doc}`api-c-core`):

1. UDP destination port matches a configured flow (else → host RX
   rings — the frame was never ours).
2. VRT type/C/indicator bits match v1 (else drop + `malformed` count).
3. Stream ID maps to an enabled stream (else drop + count).
4. Packet size equals the CSR-configured size (else drop + count).
5. 4-bit count is previous+1 (else gap policy: **halt** stream
   [default] or zero-fill + `gap` count).
6. Scheduled mode only: timestamp ≥ current device time + guard margin
   (else `late` count; stream halts — mirrors Tick's loud-late
   philosophy).

## CSR map (per stream, sketch)

| Register | Dir | Purpose |
|---|---|---|
| `stream_enable` | RX/TX | activate the stream |
| `stream_id` | RX/TX | VRT stream ID |
| `dst_mac_hi/lo`, `dst_ip`, `dst_port` | RX | frame destination |
| `src_mac_hi/lo`, `src_ip`, `src_port` | RX/TX | source / flow match |
| `payload_samples` | RX/TX | fixed payload size |
| `tsi_mode` | RX | integer-timestamp interpretation flag |
| `gap_policy` | TX | halt / zero-fill |
| `guard_ticks` | TX | scheduled-mode late threshold |
| `count_*` (seq gaps, malformed, late, drops) | RO | validation counters |

## Deviations from VITA-49.2 / DIFI (v1)

- **No context packets.** Stream properties (rate, frequency, format)
  are CSR/SDK-side configuration; a periodic DIFI-style context packet
  is a listed follow-on once the SDK's control plane stabilizes.
- **No trailer**, no per-sample event indicators.
- **Fixed payload size per stream** — legal in DIFI, but v1 rejects
  rather than accepts variable sizes.
- **IPv4 only, no VLAN**, point-to-point assumptions (no fabric
  ARP/ND; peers static by CSR).
- **4-bit sequence only** — no extended sequence field, with the
  mitigation described above.
