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

   **Documentation-first phase.** This site is the architecture proposal,
   API specification, and requirements definition for the SDK. No SDK code
   exists yet; every public API appears here before it is implemented
   (see :doc:`requirements-documentation`).

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
     - SDK API
     - Notes
   * - ADRV9009-ZU11EG on ADRV2CRR-FMC (``tron``)
     - **Validated**
     - Planned
     - Tick scheduler and timed Talise FHM hop validated on silicon;
       vrt49 Corundum 10G VITA 49.2 path; hopcap runs the timed hop
       with hardware-gated capture end to end, nightly. See
       :doc:`platform-adrv9009-zu11eg` and :doc:`support-matrix`.
   * - ADRV9361-Z7035 on ADRV1CRR-FMC
     - Integration artifacts
     - Planned
     - vrt49 1G SFP design with the vendored Tick scheduler and a
       fastlock hop controller; control and transport qualified on
       hardware, RF-measured hop settling unresolved. See
       :doc:`platform-adrv9361-z7035`.
   * - AD9081-FMCA-EBZ on ZCU102 (``mini2``)
     - Validated (Tick)
     - Not an SDK target
     - Tick's primary validated base (58/58 hardware suite); vrt49
       reference design. Listed because the SDK's Tier 1 contract
       tests inherit from it. See :doc:`support-matrix`.

Status vocabulary follows the Tick project: *validated* (end-to-end on
hardware with evidence artifacts), *integration artifacts* (HDL/DT
collateral exists, not proven on silicon), *planned* (documented intent).
*Infrastructure* is what the tick, vrt49, libiio and hopcap repositories
prove on hardware; *SDK API* is ``libdatax``, which exists on no platform
yet. The per-repository view is :doc:`support-matrix`.

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
