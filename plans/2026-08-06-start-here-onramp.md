# "Start Here" Onramp Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a newcomer-facing front-door page (`docs/start-here.md`) that explains why SDR applications are hard and what the SDK promises, per `specs/2026-08-06-start-here-onramp-design.md`.

**Architecture:** One new MyST markdown page at the head of the Concepts toctree, one mermaid diagram, one before/after code contrast, two small `index.rst` edits. No other page changes.

**Tech Stack:** Sphinx 7+ / MyST / sphinxcontrib-mermaid / adi_doctools cosmic theme; headless `google-chrome` for visual verification.

## Global Constraints

- Cross-references in `.md` use `` {doc}`page-name` `` ONLY — bare `:doc:` renders as literal text silently. In `index.rst` (RST), `:doc:` is correct.
- Build gate: `python3 -m sphinx -W -b html . _build/html` from `docs/` must pass; a page missing from every toctree fails the build.
- Mermaid: subgraph titles ≤ ~18 characters (longer titles wrap into the nodes); `deterministicIds` is already configured site-wide in `conf.py` — do not touch.
- Prose hard-wrapped at ~72–76 columns; single H1; bold run-in labels, no admonitions.
- Commits: `git commit -s` (sign-off required). Push with `GH_ACCOUNT_AUTOSWITCH=0 git push origin main`.
- Never poll CI in foreground — background `gh run watch`.

---

### Task 1: Author the page, integrate it, verify the build

**Files:**
- Create: `docs/start-here.md`
- Modify: `docs/index.rst` (Concepts toctree, lines ~65–78; "Where to start" list, lines ~106+)

**Interfaces:**
- Consumes: existing doc targets `background-prior-art`, `application-domains`, `api-design-goals`, `api-python`, `roadmap`, `timing-synchronization`, `streaming-model` (all exist).
- Produces: doc target `start-here` referenced by `index.rst` only.

- [ ] **Step 1: Write `docs/start-here.md` with exactly this content**

````markdown
# Start Here: Why SDR Applications Are Hard

The front door to this documentation, written for engineers new to
SDR application development. It explains, before any architecture,
what makes real SDR applications hard and what this SDK promises to
make easy. This page is *explanation*. One honest note up front:
the project is documentation-first today ({doc}`roadmap`) — this
page describes the experience being designed, not software you can
install yet.

## The five-minute success

Modern SDR hardware ships with genuinely good tooling. With an ADI
radio and pyadi-iio, a newcomer goes from unboxing to spectrum plot
in minutes: connect to the board, set a center frequency, call
`rx()`, FFT the samples, plot. It works on the first try more often
than not, and it is honestly one of the best onramps in embedded
engineering.

That success is real — and it is exactly where the easy part ends.

## The cliff

Every real project eventually needs to say one of three sentences
that the five-minute toolchain cannot say:

- **"At exactly this time."** Start the capture on a GPS pulse
  edge. Transmit only inside your assigned time slot. Fire the next
  hop of a frequency scan at a precise boundary.
- **"On all channels together."** Capture an antenna array where
  the phase relationship *between* channels is the measurement
  itself.
- **"Without ever dropping a sample."** Record for hours, where one
  silent gap quietly invalidates the whole run.

Each sounds like a small step from the working demo. Each is a
wall, and they are walls for different reasons.

### Why "at exactly this time" is a wall

Your program runs on Linux, and a general-purpose OS makes no
promise about *when* anything happens. Between `sleep()` returning
and your capture call reaching the hardware lie scheduler wakeups,
USB or network round-trips, and driver queues — milliseconds of
jitter on a good day. Radio timelines care about microseconds and
nanoseconds. No amount of careful Python closes that gap: the only
fix is to move the *when* into hardware that counts sample clocks,
and let software decide the *what* ahead of time
({doc}`timing-synchronization`).

### Why "on all channels together" is a wall

Two radios — even two channels of one radio — do not naturally
share a clock, a sampling instant, or a phase reference. Making
inter-channel phase *mean something* is a hardware ceremony:
distribute one reference, align sampling edges, synchronize the
converters, and verify the result. Skip a step and the data looks
plausible while the phase is garbage. No software flag fixes an
array that was never aligned.

### Why "without ever dropping a sample" is a wall

A modest 61.44 MSPS complex stream is about 2 Gb/s. Sustaining that
through buffers, buses, and disks is a systems problem — and worse,
the failure mode is silence: a buffer overflows, samples vanish,
and the math downstream just gets quietly wrong. At these rates,
"the app will keep up" is not a plan ({doc}`streaming-model`).

### The reframe

Notice what none of these walls are: your algorithm. They are
infrastructure — timing, synchronization, data movement — and
today every serious SDR project re-solves them from scratch,
badly, on a deadline, before writing the first line of the code it
actually set out to write.

```{mermaid}
graph LR
    DEMO[the five-minute demo —<br/>connect · tune · rx · plot]
    subgraph WALLS ["the three walls"]
        W1["at exactly this time"]
        W2["all channels together"]
        W3["never drop a sample"]
    end
    SDK[this SDK —<br/>the walls become verbs]
    APP[a deployable system —<br/>your algorithm, not plumbing]
    DEMO --> W1 --> SDK
    DEMO --> W2 --> SDK
    DEMO --> W3 --> SDK
    SDK --> APP
```

## What easy would look like

The SDK's goal, stated as the experience it owes you: each wall
becomes roughly one line of code. Timed capture is `start_at(T)`.
Coherence is `run_mcs()` and a capability flag you can check.
Sustained capture is a stream object whose overflow is a loud
event, never a silent gap. The same code runs on every supported
radio — applications branch on capability flags, never board names
— and when the hardware cannot deliver a guarantee, the call fails
loudly at submit instead of pretending.

The contrast, concretely. What you would naively write today:

```python
target = time.time() + 1.0
time.sleep(target - time.time())   # lands... eventually
samples = sdr.rx()                 # late by an unknowable amount —
                                   # and when was sample 0, exactly?
```

What this SDK is being designed to let you write:

```python
dev.time.align_next_pps(epoch=0)            # device time = 0 at PPS
with dev.rx_stream(channels=[0]) as rx:
    rx.start_at(dev.time.seconds(1.0))      # hardware-exact start
    samples, ts = rx.recv()                 # ts = first-sample time
```

Abridged from the worked examples in {doc}`api-python` — the design
target this documentation exists to pin down, with measurable
ceilings on how short these programs must stay
({doc}`api-design-goals`, REQ-API-001).

## Where to go next

- **Why don't existing tools already do this?** The ecosystem gap —
  what UHD, libiio, and Tick each solve — is {doc}`background-prior-art`.
- **What do real missions demand?** Radar, EW, direction finding,
  and communications, worked from mission to requirement, in
  {doc}`application-domains`.
- **What is the API being designed?** The focused verb set and its
  acceptance bar in {doc}`api-design-goals`, then the Python
  experience in {doc}`api-python`.
````

- [ ] **Step 2: Add the page to the Concepts toctree**

In `docs/index.rst`, the Concepts toctree currently begins:

```rst
   background-prior-art
   application-domains
```

Change to:

```rst
   start-here
   background-prior-art
   application-domains
```

- [ ] **Step 3: Add the "Where to start" bullet**

In `docs/index.rst`, before the line
`* **Why another SDK?** Read :doc:\`background-prior-art\`.`, add:

```rst
* **New to SDR development?** Start with :doc:`start-here`.
```

- [ ] **Step 4: Build and run regression checks**

```bash
cd docs && python3 -m sphinx -W -b html . _build/html
python3 -m sphinx -b linkcheck . _build/linkcheck
grep -n ':doc:' start-here.md   # must print nothing
grep -n ':::' start-here.md     # must print nothing
```

Expected: both sphinx runs succeed (`build succeeded`), both greps
empty, no `broken` lines in `_build/linkcheck/output.txt`.

- [ ] **Step 5: Commit (local)**

```bash
git add docs/start-here.md docs/index.rst
git commit -s -m "Start Here onramp: newcomer framing of the problem and goals"
```

### Task 2: Visual verification, light and dark

**Files:**
- No source changes expected; fixes (if any) amend Task 1's files.

**Interfaces:**
- Consumes: `docs/_build/html/start-here.html` from Task 1.
- Produces: verified screenshots; go/no-go for Task 3.

- [ ] **Step 1: Capture light and dark screenshots**

```bash
cd docs/_build/html
SCRATCH=<session scratchpad dir>
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata \
  --window-size=1280,4000 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/sh-light.png "file://$PWD/start-here.html"
sed 's|<head>|<head><script>localStorage.setItem("theme","dark");</script>|' \
  start-here.html > __dark-check.html
google-chrome --headless=new --disable-gpu --user-data-dir=/tmp/chromedata2 \
  --window-size=1280,4000 --virtual-time-budget=12000 \
  --screenshot=$SCRATCH/sh-dark.png "file://$PWD/__dark-check.html"
rm __dark-check.html
```

- [ ] **Step 2: Read both screenshots and check**

The claim must come from the pixels: page renders styled in both
themes; the mermaid diagram sits in its own container with legible
subgraph title ("the three walls" must not overlap nodes); both
code blocks render highlighted; no literal `:doc:` text anywhere.
If the subgraph title collides, shorten it below 18 characters and
re-run Task 1 steps 4–5 (amend the commit).

- [ ] **Step 3: Check sidebar order on the index**

```bash
grep -o 'href="start-here.html"[^>]*>[^<]*' _build/html/index.html
```

Expected: at least one match titled "Start Here: Why SDR
Applications Are Hard"; visually confirm in the light screenshot of
index.html that Start Here is the FIRST Concepts entry.

### Task 3: Ship and verify deployed

**Files:**
- No new changes; pushes Task 1's commit.

**Interfaces:**
- Consumes: the local commit from Task 1.
- Produces: live page at
  `https://tfcollins.github.io/datax_sdk_sdr/start-here.html`.

- [ ] **Step 1: Push**

```bash
GH_ACCOUNT_AUTOSWITCH=0 git push origin main
```

- [ ] **Step 2: Watch the Publish Docs workflow in the background**

```bash
RUN=$(GH_ACCOUNT_AUTOSWITCH=0 gh run list --limit 1 \
  --json databaseId,headSha \
  --jq '.[0] | select(.headSha[0:7]=="<pushed sha>") | .databaseId')
GH_ACCOUNT_AUTOSWITCH=0 gh run watch $RUN --exit-status --interval 20
```

Run via background Bash; report conclusion once. If it fails with a
billing error, report once — do not retry-loop.

- [ ] **Step 3: Verify the deployed page**

Screenshot
`https://tfcollins.github.io/datax_sdk_sdr/start-here.html`, read
it, confirm the diagram renders. Confirm the PDF picked the page up:

```bash
curl -s https://tfcollins.github.io/datax_sdk_sdr/datax-sdr-sdk.pdf \
  -o /tmp/deployed.pdf && pdftotext -f 1 -l 8 /tmp/deployed.pdf - \
  | grep -c "Why SDR Applications Are Hard"
```

Expected: count ≥ 1.
