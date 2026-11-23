DataX SDR SDK
=============

**A streaming-radiohead SDK for ADI SDR platforms.**

DataX SDR SDK is a planned SDR-optimized API layered over the existing ADI
IIO drivers and HDL reference designs. A small C core library
(``libdatax``) with Python bindings wraps four building blocks —
**libiio** for transport and control, with the DAQIRI high-rate receive
backend on its ``feature/daqiri-udp`` branch; **Tick** for FPGA-resident
timed commands; **vrt49** for VITA 49.2 framing, IP, daemon and host
backend over Corundum or direct Ethernet; and **hopcap**, the first
composite application that proves the stack on the ADRV9009-ZU11EG —
into one coherent SDR API. The radio becomes a *streaming radiohead*: a
stream endpoint with a small set of well-defined, software-controlled
functions, not a register playground.

.. admonition:: Status

   **Specification first, code following.** This site is the architecture
   proposal, API specification, and requirements definition for the SDK;
   every public API appears here before it is implemented (see
   :doc:`requirements-documentation`). The SDK core, ``libdatax``, exists:
   immediate streaming (P2) is validated on three boards and timed control
   (P3a) on the ADRV9009-ZU11EG. Timed streams (P3b) and later phases are
   planned (:doc:`roadmap`).

The gap this fills
------------------

* **UHD** gives SDR developers per-command time tags,
  ``set_time_next_pps``, and VITA-49 sample transport — but only on USRP
  hardware.
* **libiio / pyadi-iio** run on every ADI platform, but are buffer-based
  with immediate control writes: there is no scheduled-start primitive and
  no per-command time tag.
* **Tick** supplies exactly that missing primitive — an FPGA-resident
  timed-command scheduler with a libiio-visible control surface.

DataX SDR SDK wraps libiio + Tick + vrt49 behind a single
libiio-idiomatic C API with Python bindings, so "tune at time T", "capture
N samples starting at the next PPS", and "hop this sequence" are one-line
calls on any supported platform.

Supported targets
-----------------

.. list-table::
   :header-rows: 1
   :widths: 24 20 18 38

   * - Target
     - Infrastructure
     - SDK API (libdatax)
     - Notes
   * - ADRV9009-ZU11EG on ADRV2CRR-FMC (``tron``)
     - **Validated**
     - **Validated**: streaming, timed control
     - Tick scheduler and timed Talise FHM hop validated on silicon;
       vrt49 Corundum 10G VITA 49.2 path; hopcap runs the timed hop
       with hardware-gated capture end to end. libdatax streams and runs
       timed GPIO, FHM timed tunes, device time and MCS verification.
       See :doc:`platform-adrv9009-zu11eg`.
   * - ADRV9361-Z7035 on ADRV1CRR-FMC (``lablp``)
     - Integration artifacts
     - **Validated**: streaming
     - vrt49 1G SFP design with the vendored Tick scheduler and a
       fastlock hop controller; control and transport qualified on
       hardware, RF-measured hop settling unresolved. libdatax streams on
       the stock Kuiper image. See :doc:`platform-adrv9361-z7035`.
   * - ADRV9009 on ZC706 (``nemo``)
     - Integration artifacts
     - **Validated**: streaming
     - libdatax streams on the stock Kuiper image; Tick's scheduler was
       validated on it by hand, with no CI. No timed control yet. See
       :doc:`platform-adrv9009-zc706`.
   * - AD9081-FMCA-EBZ on ZCU102 (``mini2``)
     - Validated (Tick)
     - Not supported
     - Tick's primary validated base (58/58 hardware suite); vrt49
       reference design. libdatax has no AD9081 device family (opening it
       fails with ``ENOTSUP``). Listed because the SDK's Tier 1 contract
       tests inherit from it.

None of the lab's other boards has a libdatax device family. FMCDAQ3 on
VCU118 (``nuc``) and ADRV9002 on ZCU102 are vrt49 targets, with rows in
:doc:`support-matrix`. ADRV9371 on ZC706 (``bq``) has no row in any
repository: only labgrid's own boot check exercises it.

Status vocabulary follows the Tick project: *validated* (end-to-end on
hardware with evidence artifacts), *integration artifacts* (HDL/DT
collateral exists, not proven on silicon), *planned* (documented intent).
*Infrastructure* is what the tick, vrt49, libiio and hopcap repositories
prove on hardware; *SDK API* is what ``libdatax`` itself proves on the board
in its ``hw-test.yml``. Each platform page has a runbook (image, known-good
versions, how to run the suite, evidence). The per-repository view is :doc:`support-matrix`.

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   start-here
   out-of-box-experience
   background-prior-art
   application-domains
   architecture-proposal
   streaming-model
   hdl-datapath-corundum
   hdl-datapath-corundum-tx
   vrt-frame-format
   timing-synchronization
   non-goals

.. toctree::
   :maxdepth: 2
   :caption: API Specification

   api-design-goals
   api-object-model
   api-c-core
   api-python
   api-application-mapping

.. toctree::
   :maxdepth: 2
   :caption: Platforms

   platform-adrv9361-z7035
   platform-adrv9009-zu11eg
   platform-adrv9009-zc706
   support-matrix

.. toctree::
   :maxdepth: 2
   :caption: Requirements & Plan

   requirements-hardware
   requirements-test
   requirements-documentation
   requirements-support
   requirements-process
   checklists
   roadmap

.. toctree::
   :maxdepth: 1
   :caption: Download

   PDF version <https://tfcollins.github.io/datax_sdk_sdr/datax-sdr-sdk.pdf>

Where to start
--------------

* **New to SDR development?** Start with :doc:`start-here`.
* **Why another SDK?** Read :doc:`background-prior-art`.
* **What missions demand of it:** :doc:`application-domains`.
* **How it all fits together:** :doc:`architecture-proposal`.
* **What the API will look like:** :doc:`api-object-model` then
  :doc:`api-python`.
* **What it takes to ship:** :doc:`roadmap` and the requirements pages.
