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


def is_private_url(url: str, private_repositories: set[str]) -> bool:
    """True for a github.com URL inside one of the private repositories (owner/name)."""
    return any(
        url == f"https://github.com/{repo}" or url.startswith(f"https://github.com/{repo}/")
        for repo in private_repositories
    )


def render_repo(project: str, manifest: dict, voc: dict, private_repositories: set[str] | None = None) -> str:
    """One GFM table for a repository; evidence inside a private repository is marked (owner decision 1)."""
    private_repositories = private_repositories or set()
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
            if evidence:
                suffix = " (private repository)" if is_private_url(evidence, private_repositories) else ""
                ev_cell = f"[evidence]({evidence}){suffix}"
            else:
                ev_cell = NO_ROW
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


def render_by_platform(manifests: dict[str, dict], voc: dict, private_repositories: set[str] | None = None) -> str:
    """One table over every repository, grouped by platform (vocabulary order), then feature, then project."""
    private_repositories = private_repositories or set()
    rows: list[tuple[int, str, str, str]] = []  # (platform rank, feature slug, project, line)
    platform_rank = {slug: i for i, slug in enumerate(voc["platforms"])}
    # one label per platform: the place comes from whichever manifest names it
    places: dict[str, str] = {}
    for manifest in manifests.values():
        for platform, pdata in manifest["platforms"].items():
            if pdata.get("labgrid_place") and platform not in places:
                places[platform] = pdata["labgrid_place"]
    for project in sorted(manifests):
        manifest = manifests[project]
        for platform, pdata in manifest["platforms"].items():
            label = _platform_label(platform, {"labgrid_place": places.get(platform)}, voc)
            for feature, row in pdata["features"].items():
                fname = voc["features"].get(feature, {}).get("name", feature)
                note = row.get("note")
                feature_cell = f"{fname} ({note})" if note else fname
                tier = row.get("tier")
                tier_cell = str(tier) if tier is not None else NO_ROW
                evidence = row.get("evidence")
                if evidence:
                    suffix = " (private repository)" if is_private_url(evidence, private_repositories) else ""
                    ev_cell = f"[evidence]({evidence}){suffix}"
                else:
                    ev_cell = NO_ROW
                line = f"| {label} | {feature_cell} | {project} | {_status_text(row)} | {tier_cell} | {ev_cell} |"
                rows.append((platform_rank.get(platform, len(platform_rank)), feature, project, line))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    header = [
        "| Platform | Feature | Project | Status | Tier | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    return "\n".join(header + [r[3] for r in rows]) + "\n"


def render_platform_rows(manifests: dict[str, dict], voc: dict, private_repositories: set[str] | None = None) -> str:
    """One row per platform; one column per status, listing "feature (project, Tn)" items linked to evidence."""
    private_repositories = private_repositories or set()
    statuses = ("validated", "integration-artifacts", "planned")
    per_platform: dict[str, dict[str, list[tuple[str, str, str]]]] = {}
    places: dict[str, str] = {}
    for project in sorted(manifests):
        for platform, pdata in manifests[project]["platforms"].items():
            if pdata.get("labgrid_place") and platform not in places:
                places[platform] = pdata["labgrid_place"]
            buckets = per_platform.setdefault(platform, {s: [] for s in statuses})
            for feature, row in pdata["features"].items():
                fname = voc["features"].get(feature, {}).get("name", feature)
                evidence = row.get("evidence")
                if evidence:
                    mark = " (private)" if is_private_url(evidence, private_repositories) else ""
                    name = f"[{fname}]({evidence}){mark}"
                else:
                    name = fname
                tier = row.get("tier")
                tag = f"{project}, T{tier}" if tier is not None else project
                extra = " (software)" if row.get("software_only") else ""
                buckets[row["status"]].append((feature, project, f"{name} ({tag}){extra}"))
    platform_rank = {slug: i for i, slug in enumerate(voc["platforms"])}
    lines = ["| Platform | Validated | Integration artifacts | Planned |", "|---|---|---|---|"]
    for platform in sorted(per_platform, key=lambda p: platform_rank.get(p, len(platform_rank))):
        label = _platform_label(platform, {"labgrid_place": places.get(platform)}, voc)
        cells = []
        for status in statuses:
            items = sorted(per_platform[platform][status])
            cells.append("<br>".join(i[2] for i in items) if items else NO_ROW)
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def render_fragments(
    manifests: dict[str, dict], voc: dict, private_repositories: set[str] | None = None
) -> dict[str, str]:
    """Return {"support-<repo>.md": table, ..., "capability-infrastructure.md": table}.

    `private_repositories` are GitHub owner/name pairs whose URLs get the
    "(private repository)" mark next to the evidence link.
    """
    ordered = {k: manifests[k] for k in REPO_ORDER if k in manifests}
    ordered.update({k: v for k, v in sorted(manifests.items()) if k not in ordered})
    out = {
        f"support-{repo}.md": render_repo(repo, m, voc, private_repositories)
        for repo, m in ordered.items()
    }
    out["support-by-platform.md"] = render_by_platform(ordered, voc, private_repositories)
    out["support-platforms.md"] = render_platform_rows(ordered, voc, private_repositories)
    out["capability-infrastructure.md"] = render_capabilities(ordered, voc)
    return out
