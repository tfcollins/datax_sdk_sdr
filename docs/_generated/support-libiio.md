| Platform | Feature | Status | Tier | Evidence |
|---|---|---|---|---|
| host | DAQIRI receive, raw DPDK/ibverbs (DPDK and ibverbs raw queues implemented; not yet carrying sample mode; lab-host-only tier) | integration artifacts | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |
| host | DAQIRI receive, socket engine (UDP sample mode through the DAQIRI socket engine; unit, emulator and loopback tiers in CI) | validated (software) | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/doc/source/daqiri-backend.md) |
| host | iiod UDP stream setup (IIOD_OP_UDP_STREAM_SETUP and iiod-emu --udp) | validated (software) | 1 | [evidence](https://github.com/tfcollins/libiio/blob/feature/daqiri-udp/tests/daqiri/README.md) |
