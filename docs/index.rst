DataX SDR SDK
=============

**A streaming-radiohead SDK for ADI SDR platforms.**

DataX SDR SDK is a planned SDR-optimized API layered over the existing ADI
IIO drivers and HDL reference designs. A small C core library
(``libdatax``) with Python bindings wraps three proven building blocks —
**libiio** for transport and control, **Tick** for FPGA-resident timed
commands, and **Corundum** for the high-speed network plane — into one
coherent SDR API. The radio becomes a *streaming radiohead*: a stream
endpoint with a small set of well-defined, software-controlled functions,
not a register playground.

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

DataX SDR SDK wraps libiio + Tick + Corundum behind a single
libiio-idiomatic C API with Python bindings, so "tune at time T", "capture
N samples starting at the next PPS", and "hop this sequence" are one-line
calls on any supported platform.

Supported targets
-----------------

.. list-table::
   :header-rows: 1
   :widths: 28 22 50

   * - Target
     - Status
     - Notes
   * - ADRV9009-ZU11EG on ADRV2CRR-FMC
     - Planned — integration artifacts exist
     - Upstream HDL ships a Corundum QSFP+ NIC variant (``CORUNDUM=1``).
       Tick integration artifacts (TCL/XDC/dtsi, Talise FHM GPIO hop)
       exist but are **not hardware-validated**. See
       :doc:`platform-adrv9009-zu11eg`.
   * - ADRV9361-Z7035
     - Planned — new work required
     - No Tick port and no Corundum wrapper exist today; the Tick Pluto
       port (AD936x fastlock GPIO hopping) is the direct analogue. See
       :doc:`platform-adrv9361-z7035`.

Status vocabulary follows the Tick project: *validated* (end-to-end on
hardware with evidence artifacts), *integration artifacts* (HDL/DT
collateral exists, not proven on silicon), *planned* (documented intent).

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   background-prior-art
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

   api-object-model
   api-c-core
   api-python

.. toctree::
   :maxdepth: 2
   :caption: Platforms

   platform-adrv9361-z7035
   platform-adrv9009-zu11eg

.. toctree::
   :maxdepth: 2
   :caption: Requirements & Plan

   requirements-hardware
   requirements-test
   requirements-documentation
   requirements-support
   roadmap

Where to start
--------------

* **Why another SDK?** Read :doc:`background-prior-art`.
* **How it all fits together:** :doc:`architecture-proposal`.
* **What the API will look like:** :doc:`api-object-model` then
  :doc:`api-python`.
* **What it takes to ship:** :doc:`roadmap` and the requirements pages.
