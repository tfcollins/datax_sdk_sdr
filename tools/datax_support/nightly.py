"""Nightly drift, red-workflow and dead-link check (advisory)."""

from __future__ import annotations

import difflib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import vocab
from .fetch import fetch_manifest, load_sources
from .render import render_fragments

API = "https://api.github.com"
STALE_AFTER = timedelta(days=30)
DECISIVE = ("success", "failure")
LINK_TIMEOUT = 10


def classify_runs(runs: list[dict], now: datetime) -> str:
    """'green', 'red' or 'stale' from GitHub workflow-run objects, newest first."""
    decisive = [r for r in runs if r.get("conclusion") in DECISIVE]
    if not decisive:
        return "stale"
    latest = max(decisive, key=lambda r: r["updated_at"])
    when = datetime.strptime(latest["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if now - when > STALE_AFTER:
        return "stale"
    return "red" if latest["conclusion"] == "failure" else "green"


@dataclass
class Report:
    drift: dict[str, str] = field(default_factory=dict)
    red: list[tuple[str, str, str, str]] = field(default_factory=list)
    dead_links: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (self.drift or self.red or self.dead_links)

    def to_markdown(self) -> str:
        out = ["# Support matrix nightly", ""]
        out.append("Clean." if self.is_clean else "Findings below. This check is advisory; see the spec's red semantics.")
        out += ["", "## Drift", ""]
        if self.drift:
            for repo, diff in sorted(self.drift.items()):
                out += [f"### {repo}", "", "```diff", diff.rstrip(), "```", ""]
        else:
            out.append("none")
        out += ["", "## Red or stale workflows", ""]
        if self.red:
            out += [f"- {repo} `{wf}`: **{state}** {url}" for repo, wf, state, url in self.red]
        else:
            out.append("none")
        out += ["", "## Dead evidence links", ""]
        if self.dead_links:
            out += [f"- {repo}: {url} ({code})" for repo, url, code in self.dead_links]
        else:
            out.append("none")
        return "\n".join(out) + "\n"


def _api_get(path: str, token: str | None) -> dict:
    headers = {"User-Agent": "datax-support", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"{API}{path}", headers=headers), timeout=20) as resp:
        return json.load(resp)


def workflow_runs(source: dict, workflow: str, token: str | None) -> list[dict]:
    path = f"/repos/{source['repository']}/actions/workflows/{workflow}/runs?branch={source['branch']}&per_page=30"
    try:
        return _api_get(path, token).get("workflow_runs", [])
    except HTTPError as exc:
        if exc.code == 404:
            return []
        raise


def link_alive(url: str) -> str | None:
    """None when the URL answers 2xx/3xx, else the status code or error text."""
    try:
        with urlopen(Request(url, method="HEAD", headers={"User-Agent": "datax-support"}), timeout=LINK_TIMEOUT) as resp:
            return None if resp.status < 400 else str(resp.status)
    except HTTPError as exc:
        if exc.code == 405:  # HEAD not allowed; try GET
            try:
                with urlopen(Request(url, headers={"User-Agent": "datax-support"}), timeout=LINK_TIMEOUT) as resp:
                    return None if resp.status < 400 else str(resp.status)
            except (HTTPError, URLError) as exc2:
                return str(getattr(exc2, "code", exc2))
        return str(exc.code)
    except URLError as exc:
        return str(exc.reason)


def nightly(sources_path: Path, generated_dir: Path, token: str | None, now: datetime | None = None) -> Report:
    now = now or datetime.now(timezone.utc)
    sources = load_sources(sources_path)
    report = Report()

    manifests = {name: fetch_manifest(src, token, branch_tips=True) for name, src in sources.items()}
    fresh = render_fragments(manifests, vocab.load())
    for name, text in fresh.items():
        committed_path = generated_dir / name
        committed = committed_path.read_text(encoding="utf-8") if committed_path.exists() else ""
        if committed != text:
            diff = "".join(difflib.unified_diff(committed.splitlines(True), text.splitlines(True), f"committed/{name}", f"branch-tip/{name}"))
            report.drift[name] = diff

    checked: set[tuple[str, str]] = set()
    for repo, manifest in manifests.items():
        src = sources[repo]
        for pdata in manifest["platforms"].values():
            for row in pdata["features"].values():
                wf = row.get("workflow")
                if row["status"] == "validated" and wf and (repo, wf) not in checked:
                    checked.add((repo, wf))
                    runs = workflow_runs(src, wf, token if src.get("private") else token)
                    state = classify_runs(runs, now)
                    if state != "green":
                        url = runs[0]["html_url"] if runs else f"https://github.com/{src['repository']}/actions/workflows/{wf}"
                        report.red.append((repo, wf, state, url))
                ev = row.get("evidence")
                if ev and not src.get("private"):
                    code = link_alive(ev)
                    if code is not None:
                        report.dead_links.append((repo, ev, code))
    return report


def run_cli(sources: str, generated: str, out: str, token_env: str) -> int:
    token = os.environ.get(token_env) or None
    try:
        report = nightly(Path(sources), Path(generated), token)
    except SystemExit:
        raise
    except Exception as exc:  # network or API failure is itself a finding
        print(f"nightly: {exc}", file=sys.stderr)
        return 2
    Path(out).write_text(report.to_markdown(), encoding="utf-8")
    print("clean" if report.is_clean else "findings")
    return 0
