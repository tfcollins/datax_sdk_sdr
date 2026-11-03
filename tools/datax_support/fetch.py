"""Fetch support manifests from the repositories pinned in sources.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

RAW = "https://raw.githubusercontent.com"
TIMEOUT = 20


def load_sources(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema") != 1 or "sources" not in data:
        raise SystemExit(f"{path}: not a sources.json (schema 1 with a 'sources' map)")
    return data["sources"]


def manifest_url(source: dict, branch_tips: bool = False) -> str:
    ref = source["branch"] if branch_tips else source["revision"]
    return f"{RAW}/{source['repository']}/{ref}/{source['path']}"


def fetch_manifest(source: dict, token: str | None, branch_tips: bool = False) -> dict:
    url = manifest_url(source, branch_tips)
    headers = {"User-Agent": "datax-support"}
    if source.get("private"):
        if not token:
            raise SystemExit(
                f"{source['repository']} is private and no token was given; "
                "set SUPPORT_READ_TOKEN (contents: read on that repository)"
            )
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=TIMEOUT) as resp:
        return json.load(resp)


def manifests_from_sources(
    path: Path, token_env: str = "SUPPORT_READ_TOKEN", branch_tips: bool = False
) -> dict[str, dict]:
    sources = load_sources(Path(path))
    token = os.environ.get(token_env) or None
    needs_token = [name for name, s in sources.items() if s.get("private")]
    if needs_token and not token:
        print(
            f"render: {', '.join(needs_token)} are private; set {token_env} "
            "(fine-grained PAT, contents: read)",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return {name: fetch_manifest(src, token, branch_tips) for name, src in sources.items()}
