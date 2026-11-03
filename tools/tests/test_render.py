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
    assert set(out) == {"support-tick.md", "capability-infrastructure.md"}


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
