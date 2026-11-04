#!/usr/bin/env python3
"""Idempotent seed of the "DataX SDR" GitHub project and its planning backlog.

Creates the project, its fields, the backlog issues in datax_sdk_sdr, adds
them to the board and sets their field values. Re-running changes nothing.
Needs `gh` authenticated with the `project` scope.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

TITLE = "DataX SDR"
ISSUE_REPO = "datax_sdk_sdr"
LINKED_REPOS = ["datax_sdk_sdr", "tick", "vrt49", "libiio", "hopcap", "libdatax"]
SPEC = "specs/2026-11-03-support-matrix-and-planning-hub-design.md"

FIELDS = {
    "Codebase": ["sdk", "tick", "vrt49", "libiio", "hopcap", "libdatax"],
    "Platform": [
        "all", "ad9081-zcu102", "adrv9009-zu11eg", "adrv9009-zc706", "adrv9361-z7035",
        "adrv9002-zcu102", "fmcomms2-zcu102", "vcu118-daq3", "pluto", "host",
    ],
    "Phase": ["P0", "P1", "P2", "P3", "P4", "P5", "P6"],
    "Priority": ["P1", "P2", "P3"],
    "Requirement": None,  # text
    "Sprint": ["Now", "Next", "Later", "Blocked-lab"],
}

# Sprint by issue number in datax_sdk_sdr (owner decision 2026-11-04): Now = this week,
# Next = the first SDK code (P1), Later = evidence work as lab time allows,
# Blocked-lab = needs a physical or sudo action by the owner first.
SPRINT_BY_NUMBER = {
    2: "Now", 3: "Now", 4: "Now", 5: "Now",
    6: "Next",
    22: "Blocked-lab", 23: "Blocked-lab",
}
DEFAULT_SPRINT = "Later"

# title, repo, platform, phase, priority, requirement, body
BACKLOG = [
    ("Support matrix: add SUPPORT_READ_TOKEN and dispatch the first nightly", "sdk", "all", "P0", "P1", "REQ-TEST-042",
     "The `support-render` CI job and `support-nightly.yml` fetch tick and vrt49 manifests with a fine-grained PAT "
     "(Contents: read, Actions: read on those two repos) stored as the `SUPPORT_READ_TOKEN` secret. Until it exists the "
     "render job is red by design. Then `gh workflow run support-nightly.yml` once; its first issue is the honest starting backlog. "
     f"Source: {SPEC}, sub-project B."),
    ("Support matrix: merge the four support.json PRs and re-pin sources.json", "sdk", "all", "P0", "P1", "REQ-DOC-003",
     "tick #36, vrt49 #69, libiio #3 (against feature/daqiri-udp) and hopcap #3 each add a manifest and a checker step. "
     "After merging, set each `revision` in `sources.json` to the merge commit and run "
     "`datax-support render --sources sources.json --out docs/_generated` in the same commit."),
    ("datax-support: deferred minors from the final review", "sdk", "all", "P0", "P3", "",
     "From the sub-project B review: a 404 from the runs API reads as 'stale' not 'workflow missing'; the regen gate uses "
     "`git diff` and ignores untracked new fragments; a `|` in a manifest note breaks the table row; `tier` on a planned row "
     "is not rejected; the render job runs on fork PRs that lack the secret; a vacuous assert in test_nightly.py; "
     "`render_repo`'s unused `project` argument; `tools/datax_support/data/` has no `__init__.py`."),
    ("Docs: capability-matrix cell annotations and 'three building blocks' wording are stale after the roadmap re-baseline", "sdk", "all", "P0", "P3", "REQ-DOC-003",
     "`docs/api-object-model.md` cells still read 'P4 — new Tick port' and 'P3 — Tick HW validation'; `docs/index.rst` "
     "'Where to start' and `docs/background-prior-art.md` still say three building blocks beside the four-block lede. "
     "Deferred minors from the sub-project A review."),
    ("P1: libdatax skeleton — context/device over libiio, Python bindings, capability framework", "sdk", "all", "P1", "P1", "REQ-TEST-001, REQ-TEST-002",
     "First code task on the roadmap (`docs/roadmap.md` P1). Runs against any IIO device, no Tick or target hardware. "
     "Exit: REQ-TEST-001/002 passing; API matches `docs/api-c-core.md` or the doc is amended first (REQ-DOC-001)."),
    ("ZU11EG: timed-GPIO staircase with scope evidence against PPS", "tick", "adrv9009-zu11eg", "P3", "P2", "REQ-TEST-022, REQ-TEST-023",
     "Tick's `tron` suite validates the scheduler and the FHM hop by edge timing and PLL readback; it does not yet produce the "
     "scope capture of markers against a PPS-disciplined reference that REQ-TEST-023 requires for a timed claim. "
     "Implementing repo: tfcollins/tick."),
    ("ZU11EG: MCS and phase-coherence infrastructure row", "tick", "adrv9009-zu11eg", "P3", "P2", "REQ-TEST-032",
     "No repository claims an `mcs` feature row, so `MCS` and `PHASE_COHERENT` render '—' in the capability-infrastructure "
     "table. Decide where the multi-chip-sync procedure lives (tick or vrt49), run it on `tron`, publish the repeatability "
     "bound in the platform runbook."),
    ("hopcap: measure Talise settle time instead of configuring it", "hopcap", "adrv9009-zu11eg", "P3", "P2", "REQ-TEST-031",
     "hopcap STATUS.md 'Not done': the settle delay is a knob, not a measured figure, and the 62.8 µs excess on the priming "
     "hop's VRT-vs-Tick spacing is unexplained. A measured hop-settle feeds REQ-TEST-031 and flips the hopcap `timed-capture` "
     "row from planned. Implementing repo: tfcollins/hopcap."),
    ("hopcap: upstream VRT_FABRIC_HOP_ENABLE to vrt49 and --system-top to tick", "hopcap", "adrv9009-zu11eg", "P3", "P2", "",
     "hopcap STATUS.md 'Not done': `overlays/patches/` is empty because the assembler edits the staged tree directly. "
     "Landing the two upstream PRs lets hopcap consume both submodules unmodified."),
    ("tick: ZC706 FHM hop follow-up and a CI workflow that targets the ZC706", "tick", "adrv9009-zc706", "P3", "P3", "REQ-TEST-022",
     "tick's README calls the ZC706 scheduler 'validated on hardware' but no CI workflow targets that board, so its "
     "`support.json` row is integration-artifacts. The Talise FHM hop on the ZC706 is tick's own listed follow-up."),
    ("Z7035: RF-measured fastlock settle", "vrt49", "adrv9361-z7035", "P4", "P2", "REQ-TEST-031",
     "vrt49's ADRV9361 Tick tutorial states that control and Context/IQ transport passed qualification but an independent "
     "RF-measured hop settle has not been established. This is the gate from integration-artifacts to validated for the "
     "Z7035 `fastlock-hop` row. Implementing repo: tfcollins/vrt49."),
    ("Z7035: DMA-path timestamp tagger and sync_ext wiring, or decide the VRT path is the SDK streaming path", "vrt49", "adrv9361-z7035", "P4", "P3", "REQ-TEST-022",
     "The `adrv9361z7035_vrt49_sfp` design has the scheduler and hop controller but no `tick_stream_timestamp_tag` and no "
     "`CAPTURE_ARM`/`TRANSMIT_ARM` wiring into `data_offload`. Either add them for the DMA path or record the decision that "
     "the VRT framer path is the SDK's streaming path on this board (`docs/platform-adrv9361-z7035.md`, Remaining Tick work 2)."),
    ("Z7035: external PPS route for Tick pps_in", "vrt49", "adrv9361-z7035", "P4", "P3", "REQ-HW-002",
     "`tick_scheduler_0/pps_in` is tied low in the Z7035 block design, so Tick time is reset-relative only. "
     "REQ-HW-002 wants every timed acceptance test PPS-disciplined."),
    ("Z7035: platform runbook", "sdk", "adrv9361-z7035", "P4", "P3", "REQ-DOC-004",
     "A platform is not 'validated' until it has a runbook (setup, flashing, known-good versions, evidence links). "
     "The Z7035 has none on the SDK site."),
    ("vrt49: ADRV9002/ZCU102 4x10G exact-boot HIL last run failed; triage", "vrt49", "adrv9002-zcu102", "P5", "P2", "REQ-TEST-033",
     "`hdl-adrv9002-zcu102.yml` runs twice weekly on `mini2` with the receiver on nemo; the only recent run is a failure. "
     "Triage and either fix or downgrade the manifest row."),
    ("ZU11EG: TX through the vrt49 deframer exercised end to end", "vrt49", "adrv9009-zu11eg", "P6", "P3", "REQ-TEST-033",
     "The vrt49 deframer exists in HDL; hopcap exercises RX only. `TX_ARM` has no feature row. "
     "An end-to-end TX run on `tron` is the missing half of the P6 infrastructure on this board."),
    ("vrt49: VCU118 + DAQ3 UDP bitstream for the DAQIRI path", "vrt49", "vcu118-daq3", "P6", "P2", "REQ-TEST-033",
     "RoCEv2 full rate is validated on the VCU118; the UDP path to the libiio `daqiri:` backend is integration-artifacts "
     "because no bitstream carries it yet (`docs/roadmap.md` external dependencies)."),
    ("libiio: raw DPDK/ibverbs engines carrying UDP sample mode; labgrid place for the 100G NIC", "libiio", "host", "P6", "P2", "REQ-TEST-033",
     "The daqiri backend's raw queues are implemented but do not yet carry UDP sample mode; the `daqiri-hw` tier runs only on "
     "the lab host and the 100G NIC is not a labgrid place. Phase 2 plan: libiio `docs/superpowers/plans/2026-10-20-daqiri-backend-phase2-100g.md`."),
    ("libiio: upstream PR plan for the daqiri branch", "libiio", "host", "P6", "P3", "",
     "`feature/daqiri-udp` is 110+ commits over upstream `master`. Decide what goes upstream (module, iiod command, emulator) "
     "and what stays branch-only (CI/daqiri/, support.json). Roadmap external dependency."),
]


def gh(*args: str, check: bool = True) -> str:
    res = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        sys.exit(f"gh {' '.join(args)}\n{res.stderr.strip()}")
    return res.stdout


def gh_json(*args: str) -> dict:
    return json.loads(gh(*args, "--format", "json"))


def ensure_project(owner: str) -> tuple[int, str, str]:
    for p in gh_json("project", "list", "--owner", owner, "--limit", "100")["projects"]:
        if p["title"] == TITLE:
            return p["number"], p["id"], p["url"]
    p = gh_json("project", "create", "--owner", owner, "--title", TITLE)
    return p["number"], p["id"], p["url"]


def ensure_fields(number: int, owner: str) -> dict[str, dict]:
    existing = {f["name"]: f for f in gh_json("project", "field-list", str(number), "--owner", owner, "--limit", "50")["fields"]}
    for name, options in FIELDS.items():
        if name in existing:
            continue
        args = ["project", "field-create", str(number), "--owner", owner, "--name", name]
        if options is None:
            args += ["--data-type", "TEXT"]
        else:
            args += ["--data-type", "SINGLE_SELECT", "--single-select-options", ",".join(options)]
        gh(*args)
    return {f["name"]: f for f in gh_json("project", "field-list", str(number), "--owner", owner, "--limit", "50")["fields"]}


def link_repos(number: int, owner: str) -> None:
    for repo in LINKED_REPOS:
        gh("project", "link", str(number), "--owner", owner, "--repo", f"{owner}/{repo}", check=False)


def existing_issues(owner: str) -> dict[str, str]:
    out = gh("issue", "list", "-R", f"{owner}/{ISSUE_REPO}", "--state", "all", "--limit", "200", "--json", "title,url")
    return {i["title"]: i["url"] for i in json.loads(out)}


def ensure_issue(owner: str, title: str, body: str, known: dict[str, str]) -> tuple[str, bool]:
    if title in known:
        return known[title], False
    url = gh("issue", "create", "-R", f"{owner}/{ISSUE_REPO}", "--title", title, "--body", body).strip().splitlines()[-1]
    known[title] = url
    return url, True


def board_items(number: int, owner: str) -> dict[str, str]:
    items = gh_json("project", "item-list", str(number), "--owner", owner, "--limit", "200")["items"]
    return {i["content"].get("url", ""): i["id"] for i in items if i.get("content")}


def set_single(project_id: str, item_id: str, field: dict, value: str) -> None:
    option = next((o["id"] for o in field["options"] if o["name"] == value), None)
    if option is None:
        sys.exit(f"field {field['name']} has no option {value!r}")
    gh("project", "item-edit", "--project-id", project_id, "--id", item_id, "--field-id", field["id"], "--single-select-option-id", option)


def set_text(project_id: str, item_id: str, field: dict, value: str) -> None:
    gh("project", "item-edit", "--project-id", project_id, "--id", item_id, "--field-id", field["id"], "--text", value)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="tfcollins")
    args = ap.parse_args()
    owner = args.owner

    number, project_id, url = ensure_project(owner)
    fields = ensure_fields(number, owner)
    link_repos(number, owner)
    print(f"project: {url}")
    print(f"fields: {sum(1 for n in FIELDS if n in fields)}")

    known = existing_issues(owner)
    created = 0
    wanted: list[tuple[str, tuple]] = []
    for row in BACKLOG:
        title, repo, platform, phase, priority, requirement, body = row
        issue_url, new = ensure_issue(owner, title, body, known)
        created += new
        wanted.append((issue_url, (repo, platform, phase, priority, requirement)))
    # the pre-existing issue #1, added as-is with sensible fields
    if (one := f"https://github.com/{owner}/{ISSUE_REPO}/issues/1") in known.values():
        wanted.append((one, ("sdk", "all", "P0", "P3", "REQ-DOC-002")))
    print(f"issues created: {created}")

    items = board_items(number, owner)
    for issue_url, (repo, platform, phase, priority, requirement) in wanted:
        if issue_url in items:
            item_id = items[issue_url]
        else:  # item-add returns the new item; item-list may lag behind it
            item_id = gh_json("project", "item-add", str(number), "--owner", owner, "--url", issue_url)["id"]
        set_single(project_id, item_id, fields["Codebase"], repo)
        set_single(project_id, item_id, fields["Platform"], platform)
        set_single(project_id, item_id, fields["Phase"], phase)
        set_single(project_id, item_id, fields["Priority"], priority)
        if requirement:
            set_text(project_id, item_id, fields["Requirement"], requirement)
    # Sprint for every item on the board, by issue number
    for issue_url, item_id in board_items(number, owner).items():
        try:
            num = int(issue_url.rstrip("/").rsplit("/", 1)[-1])
        except ValueError:
            continue
        set_single(project_id, item_id, fields["Sprint"], SPRINT_BY_NUMBER.get(num, DEFAULT_SPRINT))
    print(f"items on board: {len(board_items(number, owner))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
