from datetime import datetime, timedelta, timezone

from datax_support.nightly import Report, classify_runs

NOW = datetime(2026, 11, 3, 6, 0, tzinfo=timezone.utc)


def run(conclusion: str, days: int) -> dict:
    when = (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"conclusion": conclusion, "updated_at": when, "html_url": "https://x/run"}


def test_red_ignores_cancelled():
    runs = [run("cancelled", 0), run("cancelled", 1), run("success", 3)]
    assert classify_runs(runs, NOW) == "green"


def test_red_on_latest_failure():
    assert classify_runs([run("failure", 0), run("success", 2)], NOW) == "red"


def test_stale_after_30_days():
    assert classify_runs([run("success", 31)], NOW) == "stale"


def test_stale_when_no_runs():
    assert classify_runs([], NOW) == "stale"


def test_report_markdown_lists_sections():
    md = Report(
        drift={"tick": "--- a\n+++ b"},
        red=[("hopcap", "hw-test.yml", "red", "https://x/run")],
        dead_links=[],
    ).to_markdown()
    assert "## Drift" in md
    assert "## Red or stale workflows" in md
    assert "## Dead evidence links" in md
    assert not Report(drift={}, red=[], dead_links=[]).is_clean is False
    assert Report(drift={}, red=[], dead_links=[]).is_clean


import json
from pathlib import Path

from datax_support import nightly as mod

PRIV = {"repository": "tfcollins/tick", "branch": "main", "revision": "a", "path": "support.json", "private": True}
PUB = {"repository": "tfcollins/hopcap", "branch": "main", "revision": "b", "path": "support.json", "private": False}
TICK = {"schema": 1, "project": "tick", "platforms": {"pluto": {"features": {"fastlock-hop": {
    "status": "validated", "tier": 2, "workflow": "hardware.yml",
    "evidence": "https://tfcollins.github.io/tick/pluto-fastlock-hop.html"}}}}}
HOPCAP = {"schema": 1, "project": "hopcap", "platforms": {}}


def _sources(tmp_path, **srcs):
    p = tmp_path / "sources.json"
    p.write_text(json.dumps({"schema": 1, "sources": srcs}))
    return p


def test_dead_link_check_covers_public_urls_of_private_sources(tmp_path, monkeypatch):
    checked = []
    monkeypatch.setattr(mod, "fetch_manifest", lambda src, token, branch_tips=False: TICK)
    monkeypatch.setattr(mod, "workflow_runs", lambda src, wf, token: [run("success", 0)])
    monkeypatch.setattr(mod, "link_alive", lambda url: checked.append(url) or None)
    mod.nightly(_sources(tmp_path, tick=PRIV), tmp_path, token="t", now=NOW)
    assert checked == ["https://tfcollins.github.io/tick/pluto-fastlock-hop.html"]


def test_private_github_urls_are_not_link_checked(tmp_path, monkeypatch):
    priv_tick = json.loads(json.dumps(TICK))
    priv_tick["platforms"]["pluto"]["features"]["fastlock-hop"]["evidence"] = "https://github.com/tfcollins/tick/blob/main/README.md"
    checked = []
    monkeypatch.setattr(mod, "fetch_manifest", lambda src, token, branch_tips=False: priv_tick)
    monkeypatch.setattr(mod, "workflow_runs", lambda src, wf, token: [run("success", 0)])
    monkeypatch.setattr(mod, "link_alive", lambda url: checked.append(url) or None)
    mod.nightly(_sources(tmp_path, tick=PRIV), tmp_path, token="t", now=NOW)
    assert checked == []


def test_nightly_reports_fetch_failure_and_continues(tmp_path, monkeypatch):
    def fetch(src, token, branch_tips=False):
        if src["repository"] == "tfcollins/tick":
            raise OSError("HTTP Error 404: Not Found")
        return HOPCAP
    monkeypatch.setattr(mod, "fetch_manifest", fetch)
    monkeypatch.setattr(mod, "workflow_runs", lambda src, wf, token: [])
    monkeypatch.setattr(mod, "link_alive", lambda url: None)
    report = mod.nightly(_sources(tmp_path, tick=PRIV, hopcap=PUB), tmp_path, token="t", now=NOW)
    assert report.fetch_failures == [("tick", "HTTP Error 404: Not Found")]
    assert not report.is_clean
    assert "## Fetch failures" in report.to_markdown()


def test_workflow_runs_public_source_sends_no_token(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(mod, "fetch_manifest", lambda src, token, branch_tips=False: {
        "schema": 1, "project": "hopcap", "platforms": {"adrv9009-zu11eg": {"features": {"fhm-hop": {
            "status": "validated", "tier": 2, "workflow": "hw-test.yml",
            "evidence": "https://tfcollins.github.io/hopcap/example.html"}}}}})
    monkeypatch.setattr(mod, "workflow_runs", lambda src, wf, token: seen.append(token) or [run("success", 0)])
    monkeypatch.setattr(mod, "link_alive", lambda url: None)
    mod.nightly(_sources(tmp_path, hopcap=PUB), tmp_path, token="t", now=NOW)
    assert seen == [None]
