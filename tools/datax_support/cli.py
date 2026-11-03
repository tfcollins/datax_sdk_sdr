"""datax-support command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import vocab
from .check import check_manifest, load_manifest
from .render import render_fragments


def _cmd_check(args: argparse.Namespace) -> int:
    errors = check_manifest(Path(args.manifest), Path(args.repo_root))
    for err in errors:
        print(err, file=sys.stderr)
    if errors:
        print(f"{len(errors)} error(s) in {args.manifest}", file=sys.stderr)
        return 1
    print(f"{args.manifest}: ok")
    return 0


def _parse_local(pairs: list[str]) -> dict[str, dict]:
    manifests: dict[str, dict] = {}
    for pair in pairs:
        repo, _, path = pair.partition("=")
        if not repo or not path:
            raise SystemExit(f"--local expects <repo>=<path>, got {pair!r}")
        manifests[repo] = load_manifest(Path(path))
    return manifests


def write_fragments(fragments: dict[str, str], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in sorted(fragments.items()):
        target = out_dir / name
        target.write_text(text, encoding="utf-8")
        written.append(target)
    return written


def _cmd_render(args: argparse.Namespace) -> int:
    if args.sources:
        from .fetch import load_sources, manifests_from_sources

        manifests = manifests_from_sources(
            Path(args.sources), token_env=args.token_env, branch_tips=args.branch_tips
        )
        private = {s["repository"] for s in load_sources(Path(args.sources)).values() if s.get("private")}
    else:
        manifests = _parse_local(args.local or [])
        private = set(args.private or [])
    if not manifests:
        raise SystemExit("render: no manifests given (use --sources or --local)")
    fragments = render_fragments(manifests, vocab.load(), private_repositories=private)
    for path in write_fragments(fragments, Path(args.out)):
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="datax-support")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check one support manifest fail-closed")
    c.add_argument("manifest")
    c.add_argument("--repo-root", default=".", help="repo root holding .github/workflows/")
    c.set_defaults(func=_cmd_check)

    r = sub.add_parser("render", help="render manifests to MyST fragments")
    r.add_argument("--sources", help="sources.json pinning repo manifests")
    r.add_argument("--local", action="append", help="<repo>=<path> (repeatable)")
    r.add_argument("--private", action="append", help="with --local: private GitHub owner/name whose URLs get marked (repeatable)")
    r.add_argument("--out", required=True, help="output directory for fragments")
    r.add_argument("--token-env", default="SUPPORT_READ_TOKEN")
    r.add_argument("--branch-tips", action="store_true", help="fetch branch tips, not pins")
    r.set_defaults(func=_cmd_render)

    n = sub.add_parser("nightly", help="drift, red-workflow and dead-link report (advisory)")
    n.add_argument("--sources", required=True)
    n.add_argument("--generated", default="docs/_generated", help="committed fragments to diff against")
    n.add_argument("--out", required=True, help="markdown report path")
    n.add_argument("--token-env", default="SUPPORT_READ_TOKEN")
    n.set_defaults(func=_cmd_nightly)
    return p


def _cmd_nightly(args: argparse.Namespace) -> int:
    from .nightly import run_cli

    return run_cli(args.sources, args.generated, args.out, args.token_env)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
