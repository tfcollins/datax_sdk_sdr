"""Fail-closed checks of one support manifest."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from . import vocab

RUN_URL_MARKERS = ("/actions/runs/", "/artifacts/")


def load_manifest(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_manifest(path: Path, repo_root: Path) -> list[str]:
    """Return a list of errors ("file:row: message"); empty means ok."""
    path = Path(path)
    repo_root = Path(repo_root)
    name = path.name
    try:
        manifest = load_manifest(path)
    except (OSError, ValueError) as exc:
        return [f"{name}: cannot read manifest: {exc}"]

    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(vocab.schema())
    for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{name}:{where}: {err.message}")
    if errors:
        return errors

    voc = vocab.load()
    workflows_dir = repo_root / ".github" / "workflows"
    for platform, pdata in manifest["platforms"].items():
        if platform not in voc["platforms"]:
            errors.append(f"{name}:{platform}: unknown platform '{platform}'")
        for feature, row in pdata["features"].items():
            loc = f"{name}:{platform}/{feature}"
            if feature not in voc["features"]:
                errors.append(f"{loc}: unknown feature '{feature}'")
            errors.extend(_check_row(loc, row, workflows_dir))
    return errors


def _check_row(loc: str, row: dict, workflows_dir: Path) -> list[str]:
    errs: list[str] = []
    status = row["status"]
    evidence = row.get("evidence", "")
    if evidence and any(m in evidence for m in RUN_URL_MARKERS):
        errs.append(f"{loc}: evidence must be a durable page, not a workflow run or artifact URL")
    if evidence and not evidence.startswith("https://"):
        errs.append(f"{loc}: evidence must start with https://")

    if status == "validated":
        min_tier = 1 if row.get("software_only") else 2
        tier = row.get("tier")
        if tier is None or tier < min_tier:
            need = "tier >= 1 (software_only)" if min_tier == 1 else "tier >= 2"
            errs.append(f"{loc}: validated requires {need}, got {tier}")
        if not evidence:
            errs.append(f"{loc}: validated requires a non-empty evidence URL")
        workflow = row.get("workflow")
        if not workflow:
            errs.append(f"{loc}: validated requires a workflow file name")
        elif not (workflows_dir / workflow).is_file():
            errs.append(f"{loc}: workflow '{workflow}' not found under {workflows_dir}")
    elif status == "integration-artifacts":
        if not evidence:
            errs.append(f"{loc}: integration-artifacts requires an evidence URL")
    elif status == "planned":
        if "tier" in row:
            errs.append(f"{loc}: a planned row must not carry a tier (nothing has run)")
    return errs
