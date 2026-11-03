"""Render support manifests into MyST fragments."""

from __future__ import annotations

from .vocab import STATUS_RANK, STATUS_TEXT

REPO_ORDER = ("tick", "vrt49", "libiio", "hopcap", "sdk")
NO_ROW = "—"


def _status_text(row: dict) -> str:
    text = STATUS_TEXT[row["status"]]
    if row.get("software_only"):
        text += " (software)"
    return text


def _platform_label(slug: str, pdata: dict, voc: dict) -> str:
    name = voc["platforms"].get(slug, {}).get("name", slug)
    place = pdata.get("labgrid_place")
    return f"{name} (`{place}`)" if place else name


def render_repo(project: str, manifest: dict, voc: dict) -> str:
    lines = [
        "| Platform | Feature | Status | Tier | Evidence |",
        "|---|---|---|---|---|",
    ]
    for platform in sorted(manifest["platforms"]):
        pdata = manifest["platforms"][platform]
        label = _platform_label(platform, pdata, voc)
        for feature in sorted(pdata["features"]):
            row = pdata["features"][feature]
            fname = voc["features"].get(feature, {}).get("name", feature)
            note = row.get("note")
            feature_cell = f"{fname} ({note})" if note else fname
            tier = row.get("tier")
            tier_cell = str(tier) if tier is not None else NO_ROW
            evidence = row.get("evidence")
            ev_cell = f"[evidence]({evidence})" if evidence else NO_ROW
            lines.append(
                f"| {label} | {feature_cell} | {_status_text(row)} | {tier_cell} | {ev_cell} |"
            )
    return "\n".join(lines) + "\n"


def _best_status(manifests: dict[str, dict], platform: str, features: list[str]) -> str:
    best: str | None = None
    for manifest in manifests.values():
        pdata = manifest["platforms"].get(platform)
        if not pdata:
            continue
        for feature in features:
            row = pdata["features"].get(feature)
            if row is None:
                continue
            if best is None or STATUS_RANK[row["status"]] > STATUS_RANK[best]:
                best = row["status"]
    return STATUS_TEXT[best] if best else NO_ROW


def render_capabilities(manifests: dict[str, dict], voc: dict) -> str:
    platforms = voc["capability_platforms"]
    header = "| Capability | " + " | ".join(voc["platforms"][p]["name"] for p in platforms) + " |"
    lines = [header, "|---|" + "---|" * len(platforms)]
    for cap, cdata in voc["capabilities"].items():
        cells = [_best_status(manifests, p, cdata["features"]) for p in platforms]
        lines.append(f"| `{cap}` | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def render_fragments(manifests: dict[str, dict], voc: dict) -> dict[str, str]:
    """Return {"support-<repo>.md": table, ..., "capability-infrastructure.md": table}."""
    ordered = {k: manifests[k] for k in REPO_ORDER if k in manifests}
    ordered.update({k: v for k, v in sorted(manifests.items()) if k not in ordered})
    out = {f"support-{repo}.md": render_repo(repo, m, voc) for repo, m in ordered.items()}
    out["capability-infrastructure.md"] = render_capabilities(ordered, voc)
    return out
