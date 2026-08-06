# Design: "Start Here" Onramp Page

Date: 2026-08-06
Status: approved design, pre-implementation
Location note: specs live at repo root (`specs/`), not under `docs/`,
because every `.md` under `docs/` is Sphinx source and an
out-of-toctree file fails the `-W` build.

## Problem

The documentation site opens with `background-prior-art.md` — an
ecosystem gap analysis argued through timing models — and gets denser
from there. A reader who is new to SDR development has no page that
explains, in their vocabulary, what makes SDR applications hard and
what this SDK intends to make easy. The ease-of-use motivation exists
but is scattered: line-count ceilings in `api-design-goals.md`,
worked examples in `api-python.md`, mission demands in
`application-domains.md`. There is no front door.

## Decisions (user-confirmed)

- **Form:** new front-door page(s); existing spec pages stay as-is.
- **Audience:** SDR newcomers — engineers new to SDR application
  development generally. The page teaches the problem space itself.
- **Success bar:** the reader leaves with problem intuition plus the
  SDK's promise. Conceptual; minimal code.
- **Approach:** one-page "cliff" narrative (Approach A), first page
  in Concepts.

## The page

- **File:** `docs/start-here.md`
- **Title:** `# Start Here: Why SDR Applications Are Hard`
- **Diátaxis quadrant:** explanation, declared in the lede
  (REQ-DOC-002).
- **Length:** ~130–160 lines, site conventions (MyST, `{doc}` roles
  only, bold run-in labels, GFM tables if any, hard wrap ~72–76).
- **Honesty:** the lede states the SDK is documentation-first — this
  page describes the experience being designed, not installable
  software.

### Narrative arc (sections in order)

1. **Lede** — what this page is, who it is for, quadrant, honesty
   line, links to the pages it feeds.
2. **The five-minute success** — with today's ADI tooling
   (pyadi-iio), a newcomer gets a spectrum plot in minutes: connect,
   tune, `rx()`, FFT. Genuine praise; this part works.
3. **The cliff** — every real project eventually says one of three
   sentences: "at exactly this time" (PPS-aligned capture, TDD
   window), "on all channels together" (phase-aligned array), or
   "without ever dropping a sample" (sustained capture). Each sounds
   like a small step from the demo; each is a wall.
4. **Why each is a wall** — one subsection per demand, plain
   language:
   - a general-purpose OS cannot promise *when* anything happens
     (millisecond scheduling jitter vs microsecond needs → timing
     must live in hardware);
   - independent radios share neither clock nor phase (coherence is
     a hardware ceremony — reference distribution, SYSREF, MCS — not
     a software flag);
   - data outruns casual software (native rates saturate what a
     Python loop can touch; sustained capture is a systems problem).
   Reframe: none of these are the application's algorithm. They are
   infrastructure, and today every project re-solves them badly.
5. **The diagram** — one mermaid graph: the smooth five-minute path,
   the three walls between "demo" and "deployable system", the SDK
   drawn as the bridge layer. Placed here, directly after the walls
   subsections, where all three walls have been named.
6. **What easy would look like** — the SDK's goal as user-experience
   promises: each of the three sentences becomes roughly one line of
   code, portable across supported radios (capability flags, no
   board names), failing loudly when the hardware cannot deliver.
   One short before/after contrast: the naive `sleep()`-then-capture
   sketch vs the ~6-line spec-level `start_at()` capture, abridged
   from and linked to {doc}`api-python`, labeled as the design
   target. Cite the line-count promises (REQ-API-001) rather than
   restating them.
7. **Where to go next** — three reader paths:
   - why existing tools don't do this → {doc}`background-prior-art`;
   - what missions demand of the system → {doc}`application-domains`;
   - the API being designed → {doc}`api-design-goals` then
     {doc}`api-python`.

## Integration

- `docs/index.rst`: add `start-here` as the FIRST entry in the
  Concepts toctree (before `background-prior-art`); add a new first
  bullet to "Where to start": "**New to SDR development?** Start
  with :doc:`start-here`." (bare `:doc:` is correct in RST).
- No edits to any existing page — the onramp links out; nothing
  links back in v1.

## Constraints

- REQ-DOC-009: no duplicated load-bearing tables; the code contrast
  is illustrative and links to its canonical home.
- Mermaid: `deterministicIds` already set site-wide; subgraph titles
  ≤ ~18 chars (known wrap-collision limit); `{doc}` roles only in
  `.md`.
- The PDF pipeline picks the page up automatically (singlehtml).

## Verification

1. `cd docs && make html` — passes `-W`.
2. `make linkcheck` — all internal refs resolve.
3. Light + dark screenshots of the page; diagram legible in both
   (dark via `localStorage.setItem("theme","dark")` seed).
4. `grep -n ':doc:' docs/start-here.md` returns nothing.
5. Sidebar shows Start Here first under Concepts; "Where to start"
   bullet resolves.
6. Ship per repo convention: commit -s, push, CI deploys site + PDF.

## Out of scope

- Rewriting the index lede or any existing page's framing
  (Approach C, not chosen).
- A separate Goals page (Approach B, not chosen).
- Runnable tutorial content — nothing ships yet; the page is honest
  about that.
