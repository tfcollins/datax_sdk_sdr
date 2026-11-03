# Manifest Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each of tick, vrt49, libiio and hopcap declares its hardware support in a `support.json` that its own CI checks fail-closed; the SDK renders those manifests into the support-matrix page and a nightly flags drift, red workflows and dead evidence links — sub-project B of the spec.

**Architecture:** One Python package in the SDK repo, `datax_support`, with two commands: `check` (schema + fail-closed rules against one manifest) and `render` (fetch manifests at pinned revisions from `sources.json`, write MyST fragments under `docs/_generated/`). Repos run `check` from a pinned SDK revision in their existing CI. The SDK's CI reruns `render` and fails on diff; a nightly reruns it against branch tips, queries workflow conclusions, link-checks evidence, and opens one tracking issue.

**Tech Stack:** Python 3.12, `jsonschema`, `pytest`; stdlib `urllib` for fetches; GitHub Actions; `gh` CLI in the nightly for the issue. Hand-edited YAML in five repos.

**Spec:** `specs/2026-11-03-support-matrix-and-planning-hub-design.md` — sub-project B, "Decisions from the builder check", "Left to the builder".

## Global Constraints

- Platform slugs: `ad9081-zcu102`, `adrv9009-zu11eg`, `adrv9009-zc706`, `adrv9361-z7035`, `adrv9002-zcu102`, `fmcomms2-zcu102`, `vcu118-daq3`, `pluto`, `host`.
- Feature slugs: `streaming-rx`, `streaming-tx`, `timed-gpio`, `timed-capture`, `stream-gate`, `timestamps`, `fhm-hop`, `fastlock-hop`, `mcs`, `vrt-udp-1g`, `vrt-udp-10g`, `vrt-udp-100g`, `vrt-rocev2-100g`, `vrt-dma`, `corundum-nic`, `daqiri-rx-socket`, `daqiri-rx-raw`, `iiod-udp-stream`.
- Status enum: `planned` | `integration-artifacts` | `validated`. Tier: integer 1, 2 or 3; absent when status is `planned`.
- Rules: `validated` ⇒ `tier >= 2`, non-empty `evidence`, `workflow` exists under `.github/workflows/` relative to the manifest's repo root (the check takes `--repo-root`); `integration-artifacts` ⇒ non-empty `evidence`. `evidence` must start with `https://` and must not contain `/actions/runs/` or `/artifacts/`. Optional `last_run` (URL) and `note` (string) are never checked.
- `validated` rows for libiio carry `"software_only": true`; the renderer prints "validated (software)" for them.
- Manifest file: `support.json` at repo root for tick, vrt49, hopcap; `CI/daqiri/support.json` for libiio (branch-only, owner decision 2).
- SDK repo is public (owner decision 1): repos fetch the checker without a token. The SDK fetches tick and vrt49 manifests with a fine-grained PAT in secret `SUPPORT_READ_TOKEN` (contents: read, actions: read on `tfcollins/tick` and `tfcollins/vrt49`); libiio and hopcap need none.
- Nightly is advisory (spec "Red semantics"): opens/updates one issue titled `support matrix: drift/red`; never a merge gate. Red = latest `success|failure` run of the row's workflow on the pinned branch concluded `failure`, or none in 30 days. `cancelled`/`skipped` ignored.
- Generated fragments are committed; `docs/_generated/` is in `exclude_patterns` so Sphinx `-W` does not complain about orphans, and pages pull them with the MyST `{include}` directive.
- All commits `git commit -s`. SDK pushes to `main` directly (repo convention). The four other repos: feature branch + PR, merged by the owner (their CI must pass first). Never poll CI in the foreground; use the watch-build skill.
- No lab host names or IPs in any manifest; labgrid place names are allowed.

## Review Focus

1. A manifest that says `validated` with an evidence URL pointing at a workflow run or artifact must be rejected — Task 2 test `test_check_rejects_run_url`.
2. A `check` run from a repo whose `.github/workflows/` lacks the named file must fail with the file name in the message — Task 2 test `test_check_missing_workflow_names_file`.
3. The renderer must produce byte-identical output for identical input so the regen-diff gate does not flap: sorted keys, no timestamps in fragments — Task 2 test `test_render_is_deterministic`.
4. The nightly must not report a repo as red when its only recent runs are `cancelled` (hopcap's current state) — Task 9 test `test_red_ignores_cancelled`.
5. A missing `SUPPORT_READ_TOKEN` must fail the SDK check loudly, not silently render an empty table — Task 8 test `test_render_fails_without_token_for_private_source`.

---

### Task 1: Schema and vocabulary

**Files:**
- Create: `support/schema.json`, `support/vocabulary.json`
- Create: `pyproject.toml` (package metadata only; code arrives in Task 2)

**Interfaces:**
- Produces: `support/schema.json` (JSON Schema draft 2020-12) and `support/vocabulary.json` with keys `platforms` (slug → `{"name": str}`), `features` (slug → `{"name": str}`), `capabilities` (matrix capability name → `{"features": [slug...]}`), `repos` (`tick`, `vrt49`, `libiio`, `hopcap`, `sdk`).

- [ ] **Step 1: Write `support/vocabulary.json`**

Platforms and features from Global Constraints, each with a human name (e.g. `"adrv9009-zu11eg": {"name": "ADRV9009-ZU11EG / ADRV2CRR-FMC"}`). Capabilities map the `api-object-model` matrix rows: `"Streaming (immediate)": ["streaming-rx","streaming-tx","vrt-dma"]`, `TIMED_COMMANDS: ["timed-gpio"]`, `RX_ARM: ["timed-capture"]`, `TX_ARM: ["streaming-tx"]` (note: `TX_ARM` has no feature yet; map to an empty list), `STREAM_GATE: ["stream-gate"]`, `TIMESTAMPS: ["timestamps"]`, `FASTLOCK_HOP: ["fastlock-hop"]`, `FHM_HOP: ["fhm-hop"]`, `MCS: ["mcs"]`, `PHASE_COHERENT: ["mcs"]`, `NET_OFFLOAD_NIC: ["corundum-nic"]`, `NET_OFFLOAD_SAMPLES: ["vrt-udp-10g","vrt-udp-1g","vrt-udp-100g","vrt-rocev2-100g"]`.

- [ ] **Step 2: Write `support/schema.json`**

Top level: `schema` (const 1), `project` (enum of repos), `platforms` (object; keys validated by the checker against the vocabulary, not the schema). Platform value: `carrier` (string, optional), `labgrid_place` (string, optional), `hdl_release` (string, optional), `features` (object of feature → row). Row: `status` (enum), `tier` (integer 1–3), `workflow` (string), `evidence` (string, `format: uri`), `last_run` (string), `note` (string), `software_only` (boolean). `additionalProperties: false` everywhere.

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[project]
name = "datax-support"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["jsonschema>=4.20"]
[project.scripts]
datax-support = "datax_support.cli:main"
[project.optional-dependencies]
test = ["pytest>=8"]
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
[tool.setuptools]
package-dir = {"" = "tools"}
packages = ["datax_support"]
[tool.setuptools.package-data]
datax_support = ["../../support/*.json"]
[tool.pytest.ini_options]
testpaths = ["tools/tests"]
```

Ruling for the builder: if setuptools refuses the `../../support` package-data path, copy the two JSON files into `tools/datax_support/data/` at build time via a `MANIFEST.in` + `include_package_data`, and have `vocab.py` load from the package first and from `support/` second.

- [ ] **Step 4: Validate the schema file itself**

Run: `python3 -c "import json, jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('support/schema.json'))); print('schema ok')"`
Expected: `schema ok`.

- [ ] **Step 5: Commit**

```bash
git add support/ pyproject.toml
git commit -s -m "support: manifest schema and vocabulary"
```

---

### Task 2: `datax_support` package — `check` and `render` on local files

**Files:**
- Create: `tools/datax_support/__init__.py`, `vocab.py`, `check.py`, `render.py`, `cli.py`
- Create: `tools/tests/conftest.py`, `tools/tests/test_check.py`, `tools/tests/test_render.py`, `tools/tests/fixtures/tick.support.json`, `tools/tests/fixtures/bad-*.json`

**Interfaces:**
- Produces: `check_manifest(path: Path, repo_root: Path) -> list[str]` (empty list = ok; each string is one error "file:row: message"); `render_fragments(manifests: dict[str, dict], vocab: dict) -> dict[str, str]` returning `{"support-tick.md": "...", ..., "capability-infrastructure.md": "..."}`; CLI `datax-support check <manifest> --repo-root <dir>` (exit 1 on errors, prints them) and `datax-support render --sources sources.json --out docs/_generated [--token-env SUPPORT_READ_TOKEN] [--branch-tips]` (Task 8 wires the fetch).
- `vocab.load() -> dict` reads `support/vocabulary.json`; `vocab.schema() -> dict`.

- [ ] **Step 1: Write the failing check tests**

```python
def test_check_accepts_fixture(tmp_repo):          # tmp_repo has .github/workflows/hardware.yml
    assert check_manifest(FIX/"tick.support.json", tmp_repo) == []

def test_check_rejects_unknown_feature_slug(tmp_repo):
    errs = check_manifest(FIX/"bad-feature.json", tmp_repo)
    assert any("unknown feature 'timed-gpoi'" in e for e in errs)

def test_check_validated_requires_tier_ge_2(tmp_repo):
    errs = check_manifest(FIX/"bad-tier.json", tmp_repo)
    assert any("tier >= 2" in e for e in errs)

def test_check_missing_workflow_names_file(tmp_repo):
    errs = check_manifest(FIX/"bad-workflow.json", tmp_repo)   # names nope.yml
    assert any("nope.yml" in e for e in errs)

def test_check_rejects_run_url(tmp_repo):
    errs = check_manifest(FIX/"bad-run-url.json", tmp_repo)    # evidence .../actions/runs/1
    assert any("workflow run or artifact" in e for e in errs)

def test_check_integration_artifacts_requires_evidence(tmp_repo):
    errs = check_manifest(FIX/"bad-ia-no-evidence.json", tmp_repo)
    assert any("evidence" in e for e in errs)

def test_check_planned_allows_no_tier(tmp_repo):
    assert check_manifest(FIX/"planned-only.json", tmp_repo) == []
```

`tick.support.json` fixture: project tick, platform `ad9081-zcu102` with `timed-gpio` validated tier 2 workflow `hardware.yml` evidence `https://tfcollins.github.io/tick/index.html`, and `pluto` with `fastlock-hop` integration-artifacts tier 1 evidence `https://tfcollins.github.io/tick/pluto-fastlock-hop.html`.

- [ ] **Step 2: Run, expect import failure**

Run: `python3 -m pytest tools/tests/test_check.py -q`
Expected: FAIL, `ModuleNotFoundError: datax_support`.

- [ ] **Step 3: Implement `vocab.py` and `check.py`**

`check_manifest` order: load JSON (a parse error is one error); `jsonschema` validation (each `ValidationError` → `"<path>: <message>"`); vocabulary checks for platform and feature slugs; rule checks per row. Message texts must contain the literal substrings the tests assert.

- [ ] **Step 4: Run, expect pass**

Run: `python3 -m pytest tools/tests/test_check.py -q`
Expected: 7 passed.

- [ ] **Step 5: Write the failing render tests**

```python
def test_render_writes_one_fragment_per_repo_plus_capability():
    out = render_fragments({"tick": tick_manifest}, vocab)
    assert set(out) == {"support-tick.md", "capability-infrastructure.md"}

def test_render_row_links_evidence_and_marks_software_only():
    md = render_fragments({"libiio": libiio_manifest}, vocab)["support-libiio.md"]
    assert "| validated (software) |" in md and "](https://github.com/tfcollins/libiio/" in md

def test_render_is_deterministic():
    a = render_fragments(manifests, vocab); b = render_fragments(dict(reversed(manifests.items())), vocab)
    assert a == b

def test_capability_fragment_best_status_across_repos():
    # tick has timed-gpio validated on adrv9009-zu11eg; capability TIMED_COMMANDS row for that platform says "validated"
    md = render_fragments(manifests, vocab)["capability-infrastructure.md"]
    assert "| `TIMED_COMMANDS` | integration artifacts | validated |" in md   # columns: Z7035, ZU11EG
```

- [ ] **Step 6: Run, expect failure**

Run: `python3 -m pytest tools/tests/test_render.py -q`
Expected: FAIL, `render_fragments` not defined.

- [ ] **Step 7: Implement `render.py`**

Per-repo fragment: a GFM table with header `| Platform | Feature | Status | Tier | Evidence |`, rows sorted by (platform slug, feature slug), platform shown by vocabulary name plus `labgrid_place` in backticks when present, evidence as `[evidence](url)`, status text with spaces (`integration artifacts`), `(software)` suffix when `software_only`. Capability fragment: header `| Capability | ADRV9361-Z7035 | ADRV9009-ZU11EG |`, one row per capability in vocabulary order; cell = best status over all repos' rows for any mapped feature on that platform (`validated` > `integration artifacts` > `planned` > `—` when no row). No dates or generator stamps in output.

- [ ] **Step 8: Run, expect pass**

Run: `python3 -m pytest tools/tests -q`
Expected: 11 passed.

- [ ] **Step 9: Implement `cli.py` (argparse, subcommands `check` and `render`; `render` in this task reads manifests from `--local <repo>=<path>` pairs; Task 8 adds `--sources`) and verify**

Run: `pip install -e ".[test]" && datax-support check tools/tests/fixtures/tick.support.json --repo-root tools/tests/fixtures/repo-ok && echo ok`
Expected: `ok`.

- [ ] **Step 10: Commit**

```bash
git add tools/ pyproject.toml
git commit -s -m "support: datax-support check and render"
```

---

### Task 3: SDK CI for the tool

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

Trigger: `push` (all branches), `pull_request`, `workflow_dispatch`. One job `tool` on `ubuntu-latest`: checkout, setup-python 3.12, `pip install -e ".[test]"`, `python -m pytest -q`, then `datax-support check` over every file under `tools/tests/fixtures/*.support.json` with `--repo-root tools/tests/fixtures/repo-ok`.

- [ ] **Step 2: Lint**

Run: `actionlint .github/workflows/ci.yml` (if `actionlint` is absent: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`)
Expected: no output / no exception.

- [ ] **Step 3: Commit and push, then watch**

```bash
git add .github/workflows/ci.yml
git commit -s -m "ci: run datax-support tests and fixture checks"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```

Use the watch-build skill on the `ci.yml` run. Expected: green.

---

### Task 4: tick `support.json` and CI check

**Files (in `/home/tcollins/dev/datax-sdr/tick`, branch `support-manifest`):**
- Create: `support.json`
- Modify: `.github/workflows/ci.yml` `verify` job (add one step after "Install lint and test dependencies")

- [ ] **Step 1: Write `support.json`**

Rows (status / tier / workflow / evidence):
- `ad9081-zcu102` (`labgrid_place` `mini2`, `hdl_release` `hdl_2026_r1`): `timed-gpio` validated 2 `hardware.yml` `https://tfcollins.github.io/tick/example-timed-gpio-staircase.html`; `timed-capture` validated 2 `hardware.yml` `https://tfcollins.github.io/tick/example-timed-capture.html`.
- `adrv9009-zu11eg` (`tron`, `hdl_2026_r1`): `timed-gpio` validated 2 `tron-repeat-hil.yml` `https://tfcollins.github.io/tick/adrv9009-zu11eg-bringup.html`; `fhm-hop` validated 2 `tron-repeat-hil.yml` `https://tfcollins.github.io/tick/adrv9009-fhm-hop.html`, `note` "edge timing and PLL readback; no RF settle measurement".
- `adrv9009-zc706` (`nemo`, `hdl_2023_r2`): `timed-gpio` validated 2 `hardware.yml` `https://tfcollins.github.io/tick/adrv9009-zc706-hop.html`; `fhm-hop` planned.
- `pluto`: `fastlock-hop` integration-artifacts 1 evidence `https://tfcollins.github.io/tick/pluto-fastlock-hop.html`.

- [ ] **Step 2: Check locally against the SDK checkout**

Run: `cd ~/dev/datax-sdr/tick && python3 -m venv /tmp/claude-1000/-home-tcollins-dev-datax-sdr/28e6a489-f1fc-438e-b87a-72f62f1cc2d0/scratchpad/venv-support && $_/bin/pip install -q -e ~/dev/datax-sdr/datax_sdk_sdr && $_/bin/datax-support check support.json --repo-root . && echo ok`
Expected: `ok`.

- [ ] **Step 3: Add the CI step**

```yaml
      - name: Check support manifest
        run: |
          python -m pip install "git+https://github.com/tfcollins/datax_sdk_sdr@${DATAX_SDK_REV}"
          datax-support check support.json --repo-root .
        env:
          DATAX_SDK_REV: <sha of the SDK commit from Task 3>
```

- [ ] **Step 4: Commit on a branch, push, open PR, watch CI**

```bash
git checkout -b support-manifest
git add support.json .github/workflows/ci.yml
git commit -s -m "support.json: declare hardware support for the SDK support matrix"
GH_ACCOUNT_AUTOSWITCH=0 git push -u origin support-manifest
gh pr create --fill
```

Watch with the watch-build skill. Expected: `verify` job green including the new step. Leave the PR for the owner to merge; record its URL in the ledger.

---

### Task 5: vrt49 `support.json` and CI check

**Files (in `/home/tcollins/dev/datax-sdr/vrt49`, branch `support-manifest`):**
- Create: `support.json`
- Modify: `.github/workflows/hdl-sim.yml` `software` job (add the step after `python -m pip install pytest pyyaml`)

- [ ] **Step 1: Write `support.json`**

Evidence URLs are `https://github.com/tfcollins/vrt49/blob/main/doc/source/...` (private; accepted). Rows:
- `adrv9009-zu11eg` (`tron`): `vrt-udp-10g` validated 2 `hdl-corundum.yml` `.../tutorials/hw-results-zu11eg.md`; `corundum-nic` validated 2 `hdl-corundum.yml` same; `stream-gate` integration-artifacts 1 `.../projects/adrv9009zu11eg.md` (note: fabric hop gating is exercised by hopcap); `timestamps` validated 2 `hw-test.yml` `.../tutorials/hw-results-zu11eg.md`.
- `adrv9361-z7035`: `vrt-udp-1g` integration-artifacts 2 `hdl-adrv9361-sfp.yml` `.../projects/adrv9361z7035_sfp.md`; `timed-gpio` integration-artifacts 2 `.../tutorials/adrv9361-tick-examples.md`; `fastlock-hop` integration-artifacts 2 same, `note` "control and transport qualified; RF settle unresolved"; `vrt-dma` integration-artifacts 1 `.../projects/adrv9361z7035_ccfmc.md`.
- `adrv9002-zcu102` (`mini2`): `vrt-udp-10g` integration-artifacts 2 `hdl-adrv9002-zcu102.yml` `.../how-to/adrv9002-zcu102-4x10g.md`.
- `ad9081-zcu102`: `vrt-udp-10g` integration-artifacts 1 `.../projects/ad9081_zcu102.md`.
- `fmcomms2-zcu102`: `vrt-dma` integration-artifacts 1 `.../projects/fmcomms2_zcu102.md`.
- `vcu118-daq3`: `vrt-rocev2-100g` validated 2 `hdl-vivado.yml` `.../how-to/vcu118-rocev2.md`; `vrt-udp-100g` integration-artifacts 1 `.../how-to/daqiri-receiver.md`.

- [ ] **Step 2: Check locally** (same venv as Task 4): `datax-support check support.json --repo-root .` → `ok`.

- [ ] **Step 3: Add the CI step** (same YAML as Task 4, inside the container job; `python` is set up by `setup-python`).

- [ ] **Step 4: Branch, commit, push, PR, watch** (same commands as Task 4; the `software` job runs on the `mini2` self-hosted runner, so allow for queueing). Record the PR URL.

---

### Task 6: libiio `CI/daqiri/support.json` and CI check

**Files (in `/home/tcollins/dev/datax-sdr/libiio`, branch from `feature/daqiri-udp` named `daqiri-support-manifest`):**
- Create: `CI/daqiri/support.json`
- Modify: `.github/workflows/daqiri.yml` `unit-no-daqiri` job (add a step after "Unit tests")

- [ ] **Step 1: Write the manifest**

Project `libiio`. Platform `host`: `daqiri-rx-socket` validated 1 `software_only: true` workflow `daqiri.yml` evidence `https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/doc/source/daqiri-backend.md`; `iiod-udp-stream` validated 1 `software_only: true` `daqiri.yml` `https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md`; `daqiri-rx-raw` integration-artifacts 1 same README.

Ruling pinned here: `validated` normally requires `tier >= 2`; the check relaxes it to `tier >= 1` when `software_only` is true. Add this to `check.py` and a test `test_check_software_only_allows_tier_1` in Task 2's file (do it in this task; one commit in the SDK repo).

- [ ] **Step 2: Check locally**: `datax-support check CI/daqiri/support.json --repo-root .` → `ok`.

- [ ] **Step 3: Add the CI step** (`python3 -m pip install "git+..."` then `datax-support check CI/daqiri/support.json --repo-root .`; ubuntu-latest has Python 3 without setup-python).

- [ ] **Step 4: Branch, commit, push, PR against `feature/daqiri-udp`, watch.** Commit message must follow libiio's branch style (`daqiri: ...` prefix). Record PR URL.

---

### Task 7: hopcap `support.json` and CI check

**Files (in `/home/tcollins/dev/datax-sdr/hopcap`, branch `support-manifest`):**
- Create: `support.json`
- Modify: `.github/workflows/ci.yml` `unit` job (add a step after the pip install)
- Modify: `README.md:3` (the stale "nothing is hardware-validated yet" line; the final reviewer of sub-project A flagged it)

- [ ] **Step 1: Write the manifest**

Platform `adrv9009-zu11eg` (`tron`, `hdl_2026_r1`): `fhm-hop` validated 2 `hw-test.yml` `https://tfcollins.github.io/hopcap/reports/2026-10-23-tron-first-run.html`; `stream-gate` validated 2 `hw-test.yml` same; `timestamps` validated 2 `hw-test.yml` `https://tfcollins.github.io/hopcap/reports/2026-10-25-tron-vrt-timestamps.html`; `vrt-udp-10g` validated 2 `hw-test.yml` first-run report; `timed-capture` planned, `note` "Talise settle time is a configured knob, not a measurement".

- [ ] **Step 2: Fix README line 3** to: "**Status: end to end on `tron` (2026-10-26): Tick-timed FHM hop, hardware-gated VRT49 capture over QSFP, sample-exact VRT timestamps. See `STATUS.md`.**"

- [ ] **Step 3: Check locally**, add the CI step, branch, commit, push, PR, watch (as Task 4). Record PR URL.

---

### Task 8: SDK `sources.json`, fetch, committed fragments, regen gate

**Files:**
- Create: `sources.json`
- Modify: `tools/datax_support/render.py` (add `fetch_manifest(source: dict, token: str | None) -> dict`), `cli.py` (`--sources`, `--token-env`, `--branch-tips`)
- Create: `docs/_generated/support-tick.md`, `support-vrt49.md`, `support-libiio.md`, `support-hopcap.md`, `capability-infrastructure.md`
- Modify: `docs/conf.py` (`exclude_patterns += ["_generated"]`), `docs/support-matrix.md` (replace the four hand tables with `{include}` directives), `docs/api-object-model.md` (add an `{include}` of `capability-infrastructure.md` under the matrix note)
- Modify: `.github/workflows/ci.yml` (new job `support-render`)
- Test: `tools/tests/test_fetch.py`

**Interfaces:**
- `sources.json`: `{"schema": 1, "sources": {"tick": {"repository": "tfcollins/tick", "branch": "main", "revision": "<sha>", "path": "support.json", "private": true, "why": "..."}, "vrt49": {...}, "libiio": {"branch": "feature/daqiri-udp", "path": "CI/daqiri/support.json", "private": false}, "hopcap": {...}}}`.
- Fetch URL: `https://raw.githubusercontent.com/<repository>/<revision-or-branch>/<path>`, header `Authorization: Bearer <token>` when `private` is true.

- [ ] **Step 1: Write the failing fetch tests** (monkeypatch `urllib.request.urlopen`)

```python
def test_fetch_uses_pinned_revision_and_bearer_token(fake_urlopen):
    fetch_manifest(src_private, token="t")
    assert fake_urlopen.url.endswith("/tfcollins/tick/abc123/support.json")
    assert fake_urlopen.headers["Authorization"] == "Bearer t"

def test_render_fails_without_token_for_private_source():
    with pytest.raises(SystemExit) as e:  # via cli main(["render", "--sources", ...]) with env unset
        ...
    assert "SUPPORT_READ_TOKEN" in captured.err

def test_branch_tips_uses_branch_not_revision(fake_urlopen):
    fetch_manifest(src_private, token="t", branch_tips=True)
    assert "/main/" in fake_urlopen.url
```

- [ ] **Step 2: Run, expect failure**; **Step 3: implement**; **Step 4: run, expect 15 passed** (`python3 -m pytest tools/tests -q`).

- [ ] **Step 5: Owner action, ask now if not yet done:** create a fine-grained PAT (repos `tfcollins/tick`, `tfcollins/vrt49`; permissions Contents: read, Actions: read; 1-year expiry) and add it as secret `SUPPORT_READ_TOKEN` on `tfcollins/datax_sdk_sdr`:

```
! gh secret set SUPPORT_READ_TOKEN -R tfcollins/datax_sdk_sdr
```

For the local render below, export it in the shell that runs the command; do not write it to any file.

- [ ] **Step 6: Write `sources.json`** pinned to the PR head SHAs from Tasks 4–7 (branch-tip SHAs until merged; `why`: "support-manifest PR #N").

- [ ] **Step 7: Render and wire the docs**

Run: `SUPPORT_READ_TOKEN=... datax-support render --sources sources.json --out docs/_generated`
Expected: five files written. Then edit `conf.py`, `support-matrix.md` (keep lede and closing section; replace each repo's table with ```` ```{include} _generated/support-<repo>.md``` ````), `api-object-model.md`.

Run: `cd docs && python3 -m sphinx -W -b html . _build/html -q`
Expected: exit 0.

- [ ] **Step 8: Add the `support-render` job to `ci.yml`**

Steps: checkout, setup-python, `pip install -e .`, `datax-support render --sources sources.json --out docs/_generated` with `env: SUPPORT_READ_TOKEN: ${{ secrets.SUPPORT_READ_TOKEN }}`, then `git diff --exit-code docs/_generated` (message: "generated fragments are stale: run datax-support render and commit").

- [ ] **Step 9: Commit, push, watch** (`ci.yml` and `docs.yml` both green; `support-matrix.html` still serves).

```bash
git add sources.json tools/ docs/ .github/workflows/ci.yml
git commit -s -m "support: render the matrix from pinned repo manifests; regen gate in CI"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```

---

### Task 9: Nightly drift and red check

**Files:**
- Create: `tools/datax_support/nightly.py`, `.github/workflows/support-nightly.yml`
- Modify: `cli.py` (subcommand `nightly --sources sources.json --out report.md`)
- Test: `tools/tests/test_nightly.py`

**Interfaces:**
- `classify_runs(runs: list[dict], now: datetime) -> str` returns `"green"`, `"red"` or `"stale"`; `runs` are GitHub API workflow-run objects (`conclusion`, `updated_at`).
- `nightly(sources, token, now) -> Report` with fields `drift: dict[repo, unified diff]`, `red: list[(repo, workflow, status, url)]`, `dead_links: list[(repo, url, code)]`; `Report.is_clean`, `Report.to_markdown()`.

- [ ] **Step 1: Failing tests**

```python
def test_red_ignores_cancelled():
    runs = [run("cancelled", days=0), run("cancelled", days=1), run("success", days=3)]
    assert classify_runs(runs, NOW) == "green"
def test_red_on_latest_failure():
    assert classify_runs([run("failure", 0), run("success", 2)], NOW) == "red"
def test_stale_after_30_days():
    assert classify_runs([run("success", 31)], NOW) == "stale"
def test_report_markdown_lists_sections():
    md = Report(drift={"tick": "--- a\n+++ b"}, red=[("hopcap","hw-test.yml","red","u")], dead_links=[]).to_markdown()
    assert "## Drift" in md and "## Red or stale workflows" in md and "## Dead evidence links" in md
```

- [ ] **Step 2: Run, expect failure**; **Step 3: implement** (`urllib` for GitHub API `GET /repos/{repo}/actions/workflows/{file}/runs?branch={branch}&per_page=30` with the token; HEAD request per evidence URL with a 10 s timeout, 2xx/3xx ok; drift = render against branch tips vs committed `docs/_generated`); **Step 4: run, expect 19 passed**.

- [ ] **Step 5: Write `support-nightly.yml`**

`on: schedule: cron "0 6 * * *"` and `workflow_dispatch`; `permissions: contents: read, issues: write`; steps: checkout, setup-python, `pip install -e .`, `datax-support nightly --sources sources.json --out report.md` with `SUPPORT_READ_TOKEN`; then a step that runs only if `report.md` is not clean: find an open issue titled `support matrix: drift/red` with `gh issue list --search`, `gh issue edit --body-file report.md` if found else `gh issue create --title "support matrix: drift/red" --body-file report.md --label support-matrix`; if clean and an issue is open, add a comment "clean on <date>" and close it. `GH_TOKEN: ${{ github.token }}`.

- [ ] **Step 6: Lint, commit, push, dispatch once, watch**

```bash
git add tools/ .github/workflows/support-nightly.yml
git commit -s -m "support: nightly drift, red-workflow and dead-link check"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
gh workflow run support-nightly.yml -R tfcollins/datax_sdk_sdr
```

Expected: the run is green; an issue is opened listing today's known reds (hopcap cancelled runs are ignored; ADRV9002 last failure and dispatch-only tick `hardware.yml` staleness are expected entries). Record the issue URL.

---

### Task 10: Make the SDK repo public and close out

- [ ] **Step 1: Flip visibility (owner decision 1 in the spec; outward-facing, do it last so the repo goes public with the pipeline in place)**

Run: `gh repo edit tfcollins/datax_sdk_sdr --visibility public --accept-visibility-change-consequences`
Expected: `✓ Edited repository tfcollins/datax_sdk_sdr`. Then re-run Task 4's tick CI by re-pushing the branch (its `pip install git+https://...` needed the public repo if the runner lacked credentials; confirm it is green now).

- [ ] **Step 2: Spec status**: `Status: approved; sub-projects A and B implemented 2026-11-DD`. Add the four PR URLs and the nightly issue URL under a `## Implementation record` heading.

- [ ] **Step 3: Commit and push**

```bash
git add specs/2026-11-03-support-matrix-and-planning-hub-design.md
git commit -s -m "docs: record sub-project B as implemented"
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```
