#!/usr/bin/env python3
# Usage: GH_TOKEN=... python3 tools/seed_p3b.py [--dry]. Edit task text here, not on GitHub, then re-run (dedupe by exact title).
"""Idempotent: P3b stages (sub-issues of datax_sdk_sdr#28) and tasks (sub-issues of stages,
filed in the implementing repo), added to project 4 with fields set. Dedupe by exact title."""
import json, subprocess, sys

OWNER = "tfcollins"
PROJECT = 4
PARENT = ("datax_sdk_sdr", 28)
SPEC = "https://github.com/tfcollins/libdatax/blob/main/docs/superpowers/specs/2026-11-23-libdatax-p3b-timed-streams-design.md"
DRY = "--dry" in sys.argv

def gh(*a, inp=None):
    r = subprocess.run(["gh", *a], capture_output=True, text=True, input=inp)
    if r.returncode:
        sys.exit(f"gh {' '.join(a[:4])}…\n{r.stderr.strip()}")
    return r.stdout

def find_issue(repo, title):
    out = json.loads(gh("issue", "list", "-R", f"{OWNER}/{repo}", "--state", "all", "--limit", "200",
                        "--search", f'"{title}" in:title', "--json", "number,title"))
    for i in out:
        if i["title"] == title:
            return i["number"]
    return None

def ensure_issue(repo, title, body):
    n = find_issue(repo, title)
    if n:
        cur = json.loads(gh("issue", "view", str(n), "-R", f"{OWNER}/{repo}", "--json", "body"))["body"]
        if cur.strip() != body.strip() and not DRY:
            gh("issue", "edit", str(n), "-R", f"{OWNER}/{repo}", "--body-file", "-", inp=body)
            print(f"  updated {repo}#{n} {title}")
        else:
            print(f"  exists {repo}#{n} {title}")
        return n
    if DRY:
        print(f"  DRY create {repo}: {title}")
        return None
    url = gh("issue", "create", "-R", f"{OWNER}/{repo}", "--title", title, "--body-file", "-", inp=body).strip()
    n = int(url.rsplit("/", 1)[1])
    print(f"  created {repo}#{n} {title}")
    return n

def node(repo, n):
    d = json.loads(gh("api", f"repos/{OWNER}/{repo}/issues/{n}"))
    return d["id"], d["html_url"]

def link_sub(parent_repo, parent_n, repo, n):
    subs = json.loads(gh("api", f"repos/{OWNER}/{parent_repo}/issues/{parent_n}/sub_issues?per_page=100"))
    dbid, _ = node(repo, n)
    if any(s["id"] == dbid for s in subs):
        return
    if DRY:
        return
    gh("api", "-X", "POST", f"repos/{OWNER}/{parent_repo}/issues/{parent_n}/sub_issues",
       "-F", f"sub_issue_id={dbid}")

_fields = None
_pid = None
def fields():
    global _fields, _pid
    if _fields is None:
        _fields = {f["name"]: f for f in json.loads(gh("project", "field-list", str(PROJECT), "--owner", OWNER,
                                                       "--limit", "50", "--format", "json"))["fields"]}
        _pid = json.loads(gh("project", "view", str(PROJECT), "--owner", OWNER, "--format", "json"))["id"]
    return _fields

def set_fields(repo, n, vals):
    if DRY:
        return
    _, url = node(repo, n)
    if "Status" in vals and json.loads(gh("api", f"repos/{OWNER}/{repo}/issues/{n}"))["state"] == "closed":
        vals = {**vals, "Status": "Done"}  # never reopen a finished task on the board
    q = ('query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){'
         'projectItems(first:10){nodes{id project{number}}}}}}')
    nodes = json.loads(gh("api", "graphql", "-f", f"query={q}", "-f", f"o={OWNER}", "-f", f"r={repo}", "-F", f"n={n}"))[
        "data"]["repository"]["issue"]["projectItems"]["nodes"]
    item = next((x["id"] for x in nodes if x["project"]["number"] == PROJECT), None)
    if item is None:
        r = subprocess.run(["gh", "project", "item-add", str(PROJECT), "--owner", OWNER, "--url", url, "--format", "json"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            item = json.loads(r.stdout)["id"]
        else:  # auto-add raced us; the item exists but the issue query lags
            import time
            for _ in range(10):
                time.sleep(3)
                nodes = json.loads(gh("api", "graphql", "-f", f"query={q}", "-f", f"o={OWNER}", "-f", f"r={repo}",
                                      "-F", f"n={n}"))["data"]["repository"]["issue"]["projectItems"]["nodes"]
                item = next((x["id"] for x in nodes if x["project"]["number"] == PROJECT), None)
                if item:
                    break
            if not item:
                sys.exit(f"no project item for {repo}#{n}: {r.stderr.strip()}")
    f = fields()
    for name, val in vals.items():
        fld = f[name]
        if "options" in fld:
            opt = next(o["id"] for o in fld["options"] if o["name"] == val)
            gh("project", "item-edit", "--id", item, "--project-id", _pid, "--field-id", fld["id"],
               "--single-select-option-id", opt)
        else:
            gh("project", "item-edit", "--id", item, "--project-id", _pid, "--field-id", fld["id"], "--text", val)

CODEBASE = {"datax_sdk_sdr": "sdk", "libdatax": "libdatax", "tick": "tick", "vrt49": "vrt49", "hopcap": "hopcap"}

# (key, title, sprint, status, requirement, body, tasks[(repo, title, priority, status, requirement, body)])
STAGES = [
 ("S0", "P3b S0 — design and API amendments", "Now", "Done", "REQ-DOC-001",
  "Write the P3b design, run the builder check, and amend the SDK API pages before any code (REQ-DOC-001).\n\n"
  "Exit: the spec is committed in libdatax, and `streaming-model.md`, `api-c-core.md`, `api-object-model.md` "
  "and `api-python.md` describe the ZU11EG DMA gate, the oneshot tagger and the stop/cancel rule.",
  [("libdatax", "P3b S0: design spec and builder check", "P1", "Done", "",
    "Spec: `docs/superpowers/specs/2026-11-23-libdatax-p3b-timed-streams-design.md`. Builder check answered, "
    "and its answers folded into the spec."),
   ("datax_sdk_sdr", "P3b S0: amend the streaming and API pages for DMA-gate timed streams", "P1", "Todo", "REQ-DOC-001",
    "Per the spec section \"API and doc amendments\":\n"
    "- `streaming-model.md`: the per-board mechanism (on the ZU11EG, a cpack-side gate and a oneshot tagger; `data_offload` stays on the AD9081)\n"
    "- `api-c-core.md`: `start_at` and `queue_stream_gate` semantics, errors, stop/cancel, the timestamp rule, the latency bound\n"
    "- `api-object-model.md`: the capability definitions (decision 8)\n"
    "- `api-python.md`: `start_at`, `recv` timestamps, `gate_on`/`gate_off`, `LateError`\n"
    "- event names follow the code (`DATAX_EVT_STREAM_OVERFLOW`/`UNDERFLOW`)")]),
 ("S1", "P3b S1 — spike gates G1–G6", "Now", "Implementing", "",
  "Retire the design's risks before committing HDL. Spec section \"Spike gates (S1)\".\n\n"
  "- G1: which image base (hopcap-sfp plus stock TX first, Tick's tron build second); WNS ≥ 0 and netlist checks green\n"
  "- G2: in simulation, the gate in front of cpack with `axi_dmac` (FIFO source, `SYNC_TRANSFER_START`)\n"
  "- G3: in simulation, the tagger adapter at the cpack width\n"
  "- G4: chip B's EMIO bit and the IOBUF split\n"
  "- G5: execute-now `STREAM_GATE` on the fake Tick and in Tick's Python model\n"
  "- G6: whether short RX blocks (AXIS tlast) survive the kernel, iiod and libiio v1; this decides RX mid-stream gating\n\n"
  "No step needs `tron`: the boot check of the candidate image moves to S4.",
  [("tick", "P3b S1 G2/G3: simulate the DMA gate and FIFO tag adapter against axi_dmac + util_cpack2", "P1", "Todo", "REQ-TEST-022",
    "G2: (a) the first word after the gate opens is the first sample after the opening; (b) later transfers don't wait for another `sync`; "
    "(c) on TX, closing and reopening mid-buffer pauses axi_tx_fifo reads with no underflow or stall, and on RX, a close at stop leaves no stuck transfer; (d) list every `adc_valid` consumer, including the vrt49 tap. "
    "G3: header in the first 32 bytes after each opening, matching `tick.capture.parse_capture_header`, and a reopening re-tags. "
    "Fail on (c) for TX means `STREAM_GATE` ships start-only. Spec decisions 1 to 3."),
   ("libdatax", "P3b S1 G6: can short RX blocks (AXIS tlast) reach libiio v1 through the kernel and iiod?", "P2", "Todo", "",
    "A code read. Does an AXIS-source axi_dmac transfer that ends early on tlast report its length through the ADI kernel's IIO dmaengine block path, iiod's block protocol and the libiio v1 `iio_block` dequeue? "
    "Pass brings RX mid-stream gating into P3b (an AXIS route in S2, short-block handling in S3). Fail moves RX gating to a follow-up. Spec decision 5."),
   ("hopcap", "P3b S1 G1: build the timed-dma candidate image and close timing", "P1", "Todo", "",
    "Candidate A: hopcap-sfp plus vrt49 `VRT_DAC_TX_ENABLE=0` (stock TX DMA to `axi_tx_fifo`) plus the P3b blocks. "
    "Pass: WNS ≥ 0 and netlist checks green. After two failed attempts (a seed or strategy change), build candidate B, Tick's tron build "
    "plus the PPS selector upstreamed. Spec decision 6."),
   ("hopcap", "P3b S1 G4: confirm chip B's EMIO bit and write the IOBUF split patch", "P2", "Todo", "",
    "`adrv9009_gpio_00_b` (pin AM11) sits mid-range in the 61-bit EMIO IOBUF, near bit 58, and vrt49's comments label both `00_b` and `01_b` 58. "
    "Confirm the bit from the pinned `system_top` and the constraints, then split the IOBUF around it (no narrowing). Spec decision 7."),
   ("libdatax", "P3b S1 G5: execute-now STREAM_GATE on the fake Tick and the Tick model", "P2", "Todo", "",
    "A `LATE_EXECUTE_NOW` descriptor with timestamp 0 executes on the next pass and completes `EXECUTED`. Estimate the `ip:` round trips "
    "`start_at` setup costs from P3a's per-attribute cost, then confirm the figure in S4. Spec decision 4.")]),
 ("S2", "P3b S2 — HDL, kernel and the timed-dma image", "Next", "Todo", "",
  "Build the image that carries the P2, P3a and P3b surfaces together. The RTL lives in tick and reaches hopcap through a pin bump. "
  "Spec decisions 2, 3, 6, 7 and 8.",
  [("tick", "P3b S2: tick_dma_gate RTL (pass = !mode | level) with tests", "P1", "Todo", "REQ-TEST-022",
    "Gates 0 and 1 are the RX and TX level, 2 and 3 the RX and TX timed mode. The reset state is forced open. Two-flop CDC into the device clock. "
    "RX re-routes only cpack's `fifo_wr_en` pin and adds `pack_reset` on cpack's reset pin. TX holds reads until the first opening, then mutes. OPEN_DELAY is 12. Start from the G2/G3 prototype on `p3b-spike-gate`. iverilog tests in tick's style."),
   ("tick", "P3b S2: tick_fifo_tag_adapter (FIFO interface to tagger AXIS, oneshot per release) with tests", "P1", "Todo", "REQ-TEST-022",
    "Presents cpack's `packed_fifo_wr` to `tick_stream_timestamp_tag` with tready = 1 and a synthetic tlast while RX mode is 0, so the tagger re-arms for each start_at. "
    "Tests against the Python codec."),
   ("tick", "P3b S2: stream_gate_map device-tree property and IIO attribute in the Tick driver", "P2", "Todo", "",
    "A read-only attribute that names what each gate bit drives (`rx-dma`, `tx-dma`, `rx-mode`, `tx-mode`, `fhm-b`). When the property is absent, nothing is wired. "
    "libdatax probes capabilities from it (spec decision 8)."),
   ("vrt49", "P3b S2: VRT_DAC_TX_ENABLE build switch restoring stock TX DMA to axi_dacfifo", "P1", "Todo", "",
    "Guard the `vrt49_dac_tx` insertion in `system_bd_vrt49.tcl` (around :632-654) the way `ROCE_ENABLE` is guarded. The default of 1 keeps today's behaviour. "
    "`test_adrv9009_tx_bd_contract.py` learns the switch."),
   ("hopcap", "P3b S2: timed-dma profile with DMA gate, tagger, chip-B FHM route and netlist checks", "P1", "Todo", "",
    "The assembler profile sets `VRT_DAC_TX_ENABLE=0`, sources the gate and tagger fragment, and applies the chip-B split. "
    "`check_hop_netlist.py` asserts both gates, the tagger and the chip-B route. Pins and provenance stay green."),
   ("hopcap", "P3b S2: timed-dma device tree, kernel and boot set with SHA256SUMS", "P1", "Todo", "",
    "Adds `adi,stream-gate-map` on the Tick node and chip B's FHM GPIO pin, then builds the boot set with hashes ready for libdatax `images.json`.")]),
 ("S3", "P3b S3 — libdatax timed streams on the fake Tick (Tier 1)", "Next", "Todo", "REQ-TEST-002, REQ-TEST-003",
  "The libdatax surface, tested in CI without a board. Spec decisions 4, 5, 8 and 9. Runs in parallel with S2. It needs S2 only for the exact attribute names.",
  [("libdatax", "P3b S3: fake Tick gate state, stream_gate_map and fake gated RX source with golden tag vectors", "P1", "Todo", "REQ-TEST-003",
    "Per-gate pass state and execute-now. A fake RX source produces blocks only while the gate passes, stamps block 0 with a header "
    "byte-identical to `tick.capture`, and can inject an overflow. The golden vectors are pinned like the P3a traces."),
   ("libdatax", "P3b S3: datax_stream_start_at for RX and TX (close, arm, open at T; late; stop cancels)", "P1", "Todo", "REQ-TEST-022",
    "Guard-margin rejection, then execute-now close, then buffer arm, then open at T with LATE_DROP. A late arm fails the stream. "
    "stop() flushes the arm and forces the gate open. Untimed start() forces it open first."),
   ("libdatax", "P3b S3: datax_sched_queue_stream_gate and gated bursts", "P1", "Todo", "REQ-TEST-022",
    "Level bit only. Needs a stream started with start_at, otherwise -EINVAL. TX only on this image: RX returns -ENOTSUP, because G6 failed and RX gating moved to tfcollins/datax_sdk_sdr#39. "
    "While the TX gate is closed it mutes: the DAC outputs zero and the cyclic buffer keeps playing, time-aligned (G2). Python `gate_on`/`gate_off`."),
   ("libdatax", "P3b S3: RX block timestamps (header parse and strip, derived, discontinuity)", "P1", "Todo", "REQ-TEST-022",
    "Block 0 carries capture_tick, applies the epoch offset, strips 32 bytes and reduces valid_samples. "
    "Later blocks get derived timestamps. After an overflow, blocks read 0 with discontinuous set until the next start_at. Python BlockInfo.timestamp_ticks is 0 when unknown, as in C."),
   ("libdatax", "P3b S3: capability probe for RX_ARM, TX_ARM, STREAM_GATE, TIMESTAMPS and chip-B FHM", "P2", "Todo", "REQ-TEST-042",
    "Probe from `stream_gate_map`, the Tick bitmap (0x08, 0x40) and the `capture_tag_*` attributes. Every flag stays false without the map, so the hopcap-sfp image does not regress."),
   ("libdatax", "P3b S3: chip-B timed tunes (an FHM pipeline per chip)", "P2", "Todo", "",
    "`queue_tune` on channels 2 and 3 emits on Tick GPIO bit 1, with independent one-ahead staging per chip. A hop on one chip clears PHASE_COHERENT."),
   ("libdatax", "P3b S3: Python start_at, recv timestamps, gate_on/gate_off, LateError", "P2", "Todo", "",
    "Follows the amended `api-python.md`: `recv()` keeps returning (samples, BlockInfo), with BlockInfo.timestamp_ticks 0 when unknown, as in C.")]),
 ("S4", "P3b S4 — hardware suite on tron", "Next", "Todo", "REQ-TEST-022, REQ-TEST-023, REQ-TEST-024",
  "Needs `tron` (back on the network 2026-11-23 20:49 EST) and the S2 image plus S3 code. Reserve the place, which is shared with the vrt49 hw-test. Spec decision 10.",
  [("libdatax", "P3b S4: timed-dma entry in images.json, tron-run.sh and the hw-test.yml image option", "P1", "Todo", "REQ-TEST-024",
    "A new boot set pinned by hash. A `p3b` marker skips the suite on every other image. Workflow input `image` gains `timed-dma`."),
   ("libdatax", "P3b S4: p3b suite (timed capture, loopback alignment, gated burst, chip-B hop)", "P1", "Todo", "REQ-TEST-022, REQ-TEST-023",
    "Timed capture: block 0 timestamp_ticks equals T + (1 + stripped frames)/fs, and `edge_capture_ticks` equals T. Loopback: TX and RX start_at at the same T, with the first-sample offset identical within ±1 sample over 10 runs. "
    "Gated burst: TX gates a tone on/off/on at 20 ms, and the edges in the continuous RX stream land at the commanded times plus the loopback offset, ±1 sample. Chip B: a timed tune with PLL readback. Evidence JSON."),
   ("libdatax", "P3b S4: P2 and P3a regression on the timed-dma image", "P1", "Todo", "REQ-TEST-021",
    "The full P2 suite, with TX running on this image, plus the P3a suite. Throughput and overflows are recorded, not asserted.")]),
 ("S5", "P3b S5 — phase exit", "Later", "Todo", "REQ-TEST-042, REQ-DOC-004",
  "Evidence, manifest rows and the matrix flip, once S4 is green on `tron`.",
  [("libdatax", "P3b S5: phase-exit evidence and support.json rows", "P1", "Todo", "REQ-TEST-042",
    "`docs/evidence/p3b/`, rows for `rx-arm`, `tx-arm`, `stream-gate`, `timestamps` and chip-B FHM, plus `hw-test.yml` coverage."),
   ("datax_sdk_sdr", "P3b S5: matrix flip, ZU11EG runbook and platform page for the timed-dma image", "P2", "Todo", "REQ-DOC-004",
    "Re-render the support matrix, flip the ZU11EG cells, and add the timed-dma image to the runbook and the known-good versions.")]),
]

def main():
    prepo, pn = PARENT
    for key, title, sprint, status, req, body, tasks in STAGES:
        print(f"{key}: {title}")
        sbody = f"{body}\n\nSpec: {SPEC}\nParent: tfcollins/datax_sdk_sdr#28"
        sn = ensure_issue("datax_sdk_sdr", title, sbody)
        if sn:
            link_sub(prepo, pn, "datax_sdk_sdr", sn)
            set_fields("datax_sdk_sdr", sn, {"Codebase": "sdk", "Platform": "adrv9009-zu11eg", "Phase": "P3",
                                             "Priority": "P1", "Sprint": sprint, "Status": status, "Requirement": req or "—"})
        for repo, ttitle, prio, tstatus, treq, tbody in tasks:
            full = f"{tbody}\n\nStage: tfcollins/datax_sdk_sdr#{sn} ({key}). Spec: {SPEC}"
            tn = ensure_issue(repo, ttitle, full)
            if tn and sn:
                link_sub("datax_sdk_sdr", sn, repo, tn)
                set_fields(repo, tn, {"Codebase": CODEBASE[repo], "Platform": "adrv9009-zu11eg", "Phase": "P3",
                                      "Priority": prio, "Sprint": sprint, "Status": tstatus, "Requirement": treq or "—"})

if __name__ == "__main__":
    main()
