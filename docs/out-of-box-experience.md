# The Out-of-Box Experience: From Unboxing to First Capture

What arriving should feel like. {doc}`start-here` explains why SDR
applications are hard; this page defines the experience a new user
gets from an unopened box to a first timed capture — and, stage by
stage, the repeatable processes that keep that experience true as
the SDK grows. This page is *explanation*, and everything on it is
*planned*: the project is documentation-first, so this is the
target the processes below exist to enforce. The requirement
machinery it extends lives in {doc}`requirements-documentation`,
{doc}`requirements-test`, and {doc}`requirements-support`.

## Stage 1 — Unbox

**The promise:** before anything is installed, one documentation
entry point lists exactly what this platform needs — the board and
carrier, the reference and PPS source, cables, SD card, and the one
image file to download. No forum archaeology.

**What makes it work:** the platform runbook — setup, flashing,
known-good versions, evidence links — one per platform.

**The process behind it:** runbook discipline already gates the
word "validated" (REQ-DOC-004, {doc}`requirements-documentation`):
a platform without a current runbook cannot claim validated status,
so the entry point cannot rot silently.

## Stage 2 — Provision the board

**The promise:** one downloaded, versioned image per platform.
Bitstream, kernel, rootfs, and on-board libraries arrive together
and are guaranteed mutually compatible — the user never assembles
that stack by hand.

**What makes it work:** a per-release image artifact with a version
manifest: HDL release, Vivado version, kernel commit, library
versions, bitstream hash.

**The process behind it:** a CI image-build pipeline produces the
image and its manifest on every release — the same pinning the
test requirements already demand for results (REQ-TEST-024,
{doc}`requirements-test`), now applied to what users download
(REQ-OOBE-001, REQ-OOBE-002).

## Stage 3 — Install the host SDK

**The promise:** `pip install datax`. A pure-Python wheel — no
compiler, no vendor-SDK scavenger hunt — and the first
`datax.Context()` call either works or says exactly what is wrong
and how to fix it.

**What makes it work:** ctypes bindings over the C ABI keep the
wheel pure Python ({doc}`api-python`); a board↔host version
handshake runs at context creation; `datax doctor` — one command —
diagnoses board and host state, building on the `datax-report`
tool (REQ-SUP-030, {doc}`requirements-support`).

**The process behind it:** packaging CI builds the wheel and
installs it from scratch in a clean container on every release
candidate (REQ-OOBE-003); the handshake fails loudly and names the
fix, never a cryptic errno (REQ-API-008, {doc}`api-design-goals`;
REQ-OOBE-004, REQ-OOBE-005).

## Stage 4 — First capture

**The promise:** from a provisioned board and an installed host to
a first timed capture in fifteen minutes or less, following the
tutorial verbatim — no side quests.

**What makes it work:** one canonical first-capture tutorial whose
every command is copy-pasteable, ending at the timed-capture
example from {doc}`api-python`.

**The process behind it:** the newcomer walkthrough. Before each
release, someone who did not build the SDK executes the tutorial
verbatim on real hardware, timed. Every stumble is filed as a
defect against the docs or the API — never against the newcomer
(REQ-OOBE-006, REQ-OOBE-007). This is the out-of-box analogue of
the line-count ceilings in {doc}`api-design-goals` (REQ-API-001):
ease of use measured, not asserted.

## Stage 5 — First real application

**The promise:** when the tutorial ends, the next step is visible —
a gallery with one runnable example per application archetype:
scan, coherent capture, TDD frame, record and replay, multi-node,
characterization ({doc}`api-application-mapping`).

**What makes it work:** an `examples/` gallery, each example owned,
documented, and small enough to read whole (the REQ-API-001
ceilings apply to gallery code too).

**The process behind it:** every gallery example runs in CI —
Tier 1 against the mocked context, Tier 2 on hardware where the
archetype needs it ({doc}`requirements-test`) — extending
REQ-DOC-006 from "examples in docs run" to "the gallery is the
acceptance suite that proves the API stayed easy" (REQ-OOBE-008).
Tutorials get the same gate: a tutorial that cannot be executed
verbatim is a failing test (REQ-OOBE-009).

The journey and its guards:

```{mermaid}
graph LR
    S1[unbox] --> S2[provision] --> S3[install]
    S3 --> S4[first capture] --> S5[first real app]
    P1[runbook gate] -.-> S1
    P2[image CI +<br/>version manifest] -.-> S2
    P3[packaging CI +<br/>version handshake] -.-> S3
    P4[newcomer walkthrough,<br/>timed, per release] -.-> S4
    P5[example gallery CI] -.-> S5
```

## Requirements (REQ-OOBE)

Distilled from the stages above; each item extends named
requirements in the existing web.

- **REQ-OOBE-001 — One image per platform.** Each release publishes
  a single board image per platform — bitstream, kernel, rootfs,
  and on-board libraries built together and mutually compatible.
  The platform runbook (REQ-DOC-004) names exactly one image.
- **REQ-OOBE-002 — Manifest pinning.** Every image carries a
  version manifest — HDL release, Vivado version, kernel commit,
  library versions, bitstream hash — the same fields REQ-TEST-024
  requires of test results ({doc}`requirements-test`).
- **REQ-OOBE-003 — Pure-Python host install.** The host package
  installs with `pip` alone, no compiler; packaging CI installs the
  wheel from scratch in a clean container on every release
  candidate.
- **REQ-OOBE-004 — Loud version handshake.** Context creation
  validates board↔host compatibility; a mismatch error names both
  versions and the corrective action (extends REQ-API-008,
  {doc}`api-design-goals`) — never a bare errno.
- **REQ-OOBE-005 — One-command diagnosis.** `datax doctor` reports
  board and host state in one command, building on `datax-report`
  (REQ-SUP-030, {doc}`requirements-support`).
- **REQ-OOBE-006 — Fifteen minutes to first capture.** Provisioned
  board + installed host → first timed capture ≤ 15 minutes,
  following the tutorial verbatim; measured per release by the
  walkthrough.
- **REQ-OOBE-007 — Newcomer walkthrough as release gate.** Before
  each release, someone who did not build the SDK executes the
  first-capture tutorial verbatim on real hardware; every stumble
  is filed as a defect against the docs or the API, never the
  newcomer.
- **REQ-OOBE-008 — The gallery is the acceptance suite.** One
  runnable example per archetype in {doc}`api-application-mapping`,
  each with a named owner, each executed in CI (Tier 1 mock, Tier 2
  hardware where needed); a red example blocks the release.
- **REQ-OOBE-009 — Tutorials gated like examples.** A tutorial that
  cannot be executed verbatim is a failing test — this gives the
  tutorials quadrant of REQ-DOC-002 the same teeth REQ-DOC-006
  gives examples.

## What guards what

Stage 1 is guarded by REQ-DOC-004; stage 2 by REQ-OOBE-001/002;
stage 3 by REQ-OOBE-003/004/005; stage 4 by REQ-OOBE-006/007;
stage 5 by REQ-OOBE-008/009. A stage with no guarding requirement,
or a requirement guarding nothing, is a spec bug handled per
REQ-DOC-001: the spec changes first.
