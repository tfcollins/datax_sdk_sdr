import json

from datax_support import vocab
from datax_support.render import render_fragments

TICK = {
    "schema": 1,
    "project": "tick",
    "platforms": {
        "adrv9009-zu11eg": {
            "labgrid_place": "tron",
            "features": {
                "timed-gpio": {
                    "status": "validated",
                    "tier": 2,
                    "workflow": "tron-repeat-hil.yml",
                    "evidence": "https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html",
                }
            },
        },
        "pluto": {
            "features": {
                "fastlock-hop": {
                    "status": "integration-artifacts",
                    "tier": 1,
                    "evidence": "https://tfcollins.github.io/tick/pluto-fastlock-hop.html",
                }
            }
        },
    },
}

VRT49 = {
    "schema": 1,
    "project": "vrt49",
    "platforms": {
        "adrv9361-z7035": {
            "features": {
                "timed-gpio": {
                    "status": "integration-artifacts",
                    "tier": 2,
                    "evidence": "https://github.com/tfcollins/vrt49/blob/main/doc/source/tutorials/adrv9361-tick-examples.md",
                }
            }
        }
    },
}

LIBIIO = {
    "schema": 1,
    "project": "libiio",
    "platforms": {
        "host": {
            "features": {
                "daqiri-rx-socket": {
                    "status": "validated",
                    "tier": 1,
                    "software_only": True,
                    "workflow": "daqiri.yml",
                    "evidence": "https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/doc/source/daqiri-backend.md",
                }
            }
        }
    },
}

MANIFESTS = {"tick": TICK, "vrt49": VRT49, "libiio": LIBIIO}


def test_render_writes_one_fragment_per_repo_plus_capability():
    out = render_fragments({"tick": TICK}, vocab.load())
    assert set(out) == {"support-tick.md", "support-by-platform.md", "support-platforms.md", "capability-infrastructure.md"}


def test_render_row_links_evidence_and_marks_software_only():
    md = render_fragments({"libiio": LIBIIO}, vocab.load())["support-libiio.md"]
    assert "| validated (software) |" in md
    assert "](https://github.com/tfcollins/libiio/" in md


def test_render_is_deterministic():
    a = render_fragments(MANIFESTS, vocab.load())
    b = render_fragments(dict(reversed(list(MANIFESTS.items()))), vocab.load())
    assert a == b
    # a round trip through JSON must not change anything either
    c = render_fragments(json.loads(json.dumps(MANIFESTS)), vocab.load())
    assert a == c


def test_capability_fragment_best_status_across_repos():
    md = render_fragments(MANIFESTS, vocab.load())["capability-infrastructure.md"]
    assert "| `TIMED_COMMANDS` | integration artifacts | validated |" in md
    assert "| `MCS` | — | — |" in md


def test_render_marks_private_repo_evidence():
    priv = {"tfcollins/vrt49", "tfcollins/tick"}
    out = render_fragments({"vrt49": VRT49, "tick": TICK}, vocab.load(), private_repositories=priv)
    assert "(private repository)" in out["support-vrt49.md"]
    # tick's evidence is on its public Pages site: no mark even though the repo is private
    assert "(private repository)" not in out["support-tick.md"]
    md_pub = render_fragments({"vrt49": VRT49}, vocab.load(), private_repositories=set())["support-vrt49.md"]
    assert "(private repository)" not in md_pub


def test_render_by_platform_groups_projects_under_one_platform():
    hopcap = {"schema": 1, "project": "hopcap", "platforms": {"adrv9009-zu11eg": {"labgrid_place": "tron", "features": {
        "fhm-hop": {"status": "validated", "tier": 2, "workflow": "hw-test.yml",
                    "evidence": "https://tfcollins.github.io/hopcap/example.html"}}}}}
    tick_zu = {"schema": 1, "project": "tick", "platforms": {"adrv9009-zu11eg": {"labgrid_place": "tron", "features": {
        "fhm-hop": {"status": "validated", "tier": 2, "workflow": "tron-repeat-hil.yml",
                    "evidence": "https://tfcollins.github.io/tick/adrv9009-fhm-hop.html"},
        "timed-gpio": {"status": "validated", "tier": 2, "workflow": "tron-repeat-hil.yml",
                       "evidence": "https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html"}}}}}
    out = render_fragments({"hopcap": hopcap, "tick": tick_zu, "vrt49": VRT49}, vocab.load())
    md = out["support-by-platform.md"]
    lines = [l for l in md.splitlines() if l.startswith("| ")]
    assert lines[0] == "| Platform | Feature | Project | Status | Tier | Evidence |"
    rows = lines[1:]
    # platforms follow vocabulary order: ZU11EG before Z7035; within a platform, feature then project
    assert rows[0].startswith("| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Talise FHM hop | hopcap |")
    assert rows[1].startswith("| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | Talise FHM hop | tick |")
    assert rows[2].startswith("| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | timed GPIO | tick |")
    assert rows[3].startswith("| ADRV9361-Z7035 | timed GPIO | vrt49 |")


def test_render_platform_rows_one_per_platform():
    hopcap = {"schema": 1, "project": "hopcap", "platforms": {"adrv9009-zu11eg": {"labgrid_place": "tron", "features": {
        "fhm-hop": {"status": "validated", "tier": 2, "workflow": "hw-test.yml",
                    "evidence": "https://tfcollins.github.io/hopcap/example.html"},
        "timed-capture": {"status": "planned"}}}}}
    tick_zu = {"schema": 1, "project": "tick", "platforms": {"adrv9009-zu11eg": {"labgrid_place": "tron", "features": {
        "fhm-hop": {"status": "validated", "tier": 2, "workflow": "tron-repeat-hil.yml",
                    "evidence": "https://tfcollins.github.io/tick/adrv9009-fhm-hop.html"}}}}}
    out = render_fragments({"hopcap": hopcap, "tick": tick_zu, "vrt49": VRT49}, vocab.load())
    md = out["support-platforms.md"]
    rows = [l for l in md.splitlines() if l.startswith("| ")]
    assert rows[0] == "| Platform | Validated | Integration artifacts | Planned |"
    assert len(rows) == 1 + 2  # header + ZU11EG + Z7035
    zu = rows[1]
    assert zu.startswith("| ADRV9009-ZU11EG / ADRV2CRR-FMC (`tron`) | ")
    cells = [c.strip() for c in zu.strip("|").split(" | ")]
    validated, ia, planned = cells[1], cells[2], cells[3]
    assert "[Talise FHM hop](https://tfcollins.github.io/hopcap/example.html) (hopcap, T2)" in validated
    assert "[Talise FHM hop](https://tfcollins.github.io/tick/adrv9009-fhm-hop.html) (tick, T2)" in validated
    assert "<br>" in validated  # two items, one per line
    assert ia == "—"
    assert planned == "timed capture (hopcap)"
