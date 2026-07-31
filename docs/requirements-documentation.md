# Documentation Requirements

This site is the contract. The discipline that keeps it one:

- **REQ-DOC-001 — Spec before implementation.** Every public C symbol
  and Python API appears in {doc}`api-c-core` / {doc}`api-python`
  *before* it is implemented. API changes are doc PRs first.
- **REQ-DOC-002 — Diátaxis organization.** Tutorials, how-to guides,
  reference, explanation — the structure this site already follows
  (mirroring Tick's docs); new pages declare their quadrant.
- **REQ-DOC-003 — Honest status vocabulary.** *validated / integration
  artifacts / planned*, used identically everywhere (index table,
  platform pages, capability matrix). A capability or platform may not
  be described above its evidence level (REQ-TEST-023).
- **REQ-DOC-004 — Runbooks gate "validated".** A platform is not
  "validated" until it has a runbook (setup, flashing, known-good
  versions, evidence links) — Tick's `mini2` runbook is the model.
- **REQ-DOC-005 — Theme-aware diagrams.** Poster diagrams are inline
  SVG with CSS-variable theming (dark + light verified); flow diagrams
  are Mermaid. No raster screenshots of diagrams.
- **REQ-DOC-006 — Runnable examples.** Once code exists, every example
  in the docs is executed in CI (Tier 1 where possible, Tier 2 for
  hardware examples). Spec-level examples are marked as such until then.
- **REQ-DOC-007 — Build gates.** `sphinx -W` (warnings are errors) and
  linkcheck green on every push; the Pages deploy is the artifact.
- **REQ-DOC-008 — Changelog discipline.** User-visible changes (API,
  capability matrix, platform status) land with a changelog entry from
  the first tagged release onward.
- **REQ-DOC-009 — Canonical tables.** Load-bearing tables live in
  exactly one place and are linked, never duplicated — the capability
  matrix lives in {doc}`api-object-model`.
