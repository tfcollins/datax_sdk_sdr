# Design: Out-of-Box Experience Page

Date: 2026-08-07
Status: approved design, pre-implementation
Location note: specs live at repo root (`specs/`), not under `docs/`
(Sphinx `-W` rejects orphan pages).

## Problem

The site explains why SDR is hard ({doc}`start-here`), what missions
demand, and what the API will be — but nothing defines what
*arriving* should feel like: how a user goes from an unopened box to
a first timed capture, and which repeatable processes guarantee that
path stays short, documented, and tested as the SDK grows. Pieces
exist (REQ-DOC-006 runnable examples, REQ-DOC-004 runbooks,
REQ-SUP-030 `datax-report`, REQ-TEST-024 release pinning) but no page
owns the experience or the machinery.

## Decisions (user-confirmed)

- **Scope:** the full path — unbox to first capture, including board
  provisioning (the hardest part of embedded-SDR OOBE).
- **Form:** one page — journey narrative closing with a numbered
  REQ-OOBE block (the `application-domains.md` pattern).
- **Approach:** staged journey, with explicit weight on the
  *processes* that make each stage real.

## The page

- **File:** `docs/out-of-box-experience.md`
- **Title:** `# The Out-of-Box Experience: From Unboxing to First
  Capture`
- **Quadrant:** explanation (REQ-DOC-002), declared in the lede.
- **Length:** ~170–200 lines. Site conventions: MyST, `{doc}` roles
  only, bold run-in labels, hard wrap ~72–76, one mermaid diagram.
- **Honesty:** everything on the page is *planned* — the SDK is
  documentation-first; the page defines the target experience and
  the processes that will enforce it.

### Structure

1. **Lede** — what the page owns; links {doc}`start-here`,
   {doc}`requirements-documentation`, {doc}`requirements-test`,
   {doc}`requirements-support`.
2. **Five stages**, each with three run-in labels — **The promise:**
   (what the user experiences), **What makes it work:** (the
   artifact/mechanism), **The process behind it:** (the repeatable
   machinery):
   - **Unbox** — one documentation entry point lists exactly what is
     needed before anything is installed. Process: platform runbook
     discipline (extends REQ-DOC-004).
   - **Provision the board** — one downloaded, versioned image per
     platform (bitstream + kernel + rootfs + on-board libraries,
     mutually compatible). Process: CI image-build pipeline emitting
     a version manifest (same pinning REQ-TEST-024 demands),
     published per release.
   - **Install the host SDK** — `pip install datax`, pure-Python
     wheel, no compiler. Process: packaging CI (wheel build +
     clean-container install smoke test per release candidate) and
     a board↔host version handshake: `datax.Context()` fails loudly
     and specifically on mismatch, naming the fix (extends
     REQ-API-008; `datax doctor` builds on `datax-report`,
     REQ-SUP-030).
   - **First capture** — measured time-to-first-capture: provisioned
     board + installed host → first timed capture in ≤ 15 minutes
     following the tutorial verbatim. Process: the newcomer
     walkthrough — before each release, someone who did not build
     the SDK executes the tutorial on real hardware; every stumble
     is filed as a defect against docs or API, never the newcomer.
   - **First real application** — examples gallery: one runnable
     example per archetype in {doc}`api-application-mapping`, each
     CI-executed (Tier 1 mock / Tier 2 hardware), each doubling as
     the acceptance test that the API stayed easy (extends
     REQ-DOC-006).
3. **Diagram** — one mermaid `graph LR`: the five stages as a
   pipeline with each stage's guarding process attached beneath
   (runbook, image CI + manifest, packaging CI + handshake,
   walkthrough gate, example CI). Subgraph titles ≤ ~18 chars.
4. **`## Requirements (REQ-OOBE)`** — nine items, format
   `- **REQ-OOBE-NNN — Title.** Body.` with `{doc}`/REQ cross-links:
   - 001 — One versioned, matched image per platform, with manifest.
   - 002 — Manifest pinning identical to test-result pinning
     (REQ-TEST-024): HDL release, Vivado, kernel commit, library
     versions, bitstream hash.
   - 003 — Pure-Python host install; clean-container install test in
     CI per release candidate.
   - 004 — Version handshake fails loudly and specifically; the
     error names the incompatibility and the fix (REQ-API-008).
   - 005 — `datax doctor`: one command that diagnoses board↔host
     state (builds on `datax-report`, REQ-SUP-030).
   - 006 — Time-to-first-capture ≤ 15 minutes on a provisioned
     board, measured per release via the walkthrough.
   - 007 — Newcomer walkthrough as a release gate; stumbles are
     filed defects against docs or API.
   - 008 — Examples gallery: one CI-run example per archetype, each
     with a named owner.
   - 009 — Tutorials are gated like examples: a tutorial that cannot
     be executed verbatim is a failing test (gives REQ-DOC-002's
     tutorials quadrant teeth).
5. **Closing trace** (~5 lines) — each stage names the requirements
   that guard it (its REQ-OOBE items, or the existing REQ it
   extends — Unbox is guarded by REQ-DOC-004 alone); a stage with no
   guarding requirement, or a requirement guarding nothing, is a
   spec bug (REQ-DOC-001).

## Integration

- `docs/index.rst`: add `out-of-box-experience` to the Concepts
  toctree immediately after `start-here`.
- `docs/start-here.md`: one bullet added to "Where to go next":
  "**What should arriving feel like?** The target experience and the
  processes that guard it, in {doc}`out-of-box-experience`."
- No "Where to start" bullet (avoid list bloat). No edits to the
  requirements pages — REQ-OOBE cites them (REQ-DOC-009).

## Verification

1. `cd docs && python3 -m sphinx -W -b html . _build/html` passes.
2. `python3 -m sphinx -b linkcheck . _build/linkcheck` — no broken.
3. `grep -n ':doc:' docs/out-of-box-experience.md` and
   `grep -n ':::'` — both empty.
4. Light + dark screenshots read; diagram contained, titles legible.
5. Sidebar shows the page second under Concepts.
6. Ship: commit -s, push, CI deploys site + PDF.

## Out of scope

- Building any of the processes (image pipeline, packaging CI,
  doctor tool) — this page specifies them; implementation phases
  belong to the roadmap.
- Restructuring existing requirements pages.
- New "Where to start" entries.
