# MicroPython Port for Pycom LoRa Devices

## Overview

Pycom's MicroPython fork was archived Sep 2024 (last commit Feb 2022), based on
ancient MicroPython ~v1.9 / ESP-IDF v3.x. This port adds board definitions and a
LoRa driver to upstream MicroPython v1.27.0 (ESP-IDF v5.5.1) for Pycom hardware.

### Target Hardware

| Board | Module | Flash | PSRAM | LoRa  | CS     | Reset   | DIO0   |
|-------|--------|-------|-------|-------|--------|---------|--------|
| LoPy  | L01    | 4MB   | None  | SX1272| GPIO17 | GPIO18  | GPIO23 |
| LoPy4 | L04    | 8MB   | 4MB   | SX1276| GPIO18 | None    | GPIO23 |

SPI bus (all): MOSI=GPIO27, MISO=GPIO19, SCLK=GPIO5, Mode 0, 10 MHz.

### Design Decisions

- 2 board defs (PYCOM_LOPY, PYCOM_LOPY4) — same electronics within each pair
- Pure Python LoRa driver (frozen module), C module later if needed
- New `LoRa` class API (not Pycom's `AF_LORA` socket pattern)
- RGB LED via standard `neopixel` module (WS2812 on GPIO0)
- Shared modules in `ports/esp32/boards/pycom_common/`

---

## Done

### Phase 1: Board Definitions and Basic Boot

- [x] Clone upstream MicroPython, checkout v1.27.0
- [x] **PYCOM_LOPY board** — mpconfigboard.h, cmake, sdkconfig, pins.csv, board.json, manifest.py, board_config.py
- [x] **PYCOM_LOPY4 board** — same files + custom 8MB partition table + SPIRAM sdkconfig
- [x] **Pin mapping** — 24 P-pins (P0-P23) mapped to GPIOs for both boards

### Phase 2: LoRa Driver (Raw LoRa / P2P)

- [x] **sx127x.py** — unified SX1272/SX1276 SPI driver
  - SPI register r/w, chip auto-detect via version register (0x22/0x12)
  - BW/CR encoding differences handled per chip
  - RSSI: SX1272=-139+raw, SX1276=-157+raw (HF)
  - DIO0 IRQ with flag disambiguation (GPIO23 is diode-OR)
  - HW reset (LoPy GPIO18) / soft reset (LoPy4)
  - send(), recv(timeout), on_recv(callback)
- [x] **lora.py** — high-level API: `LoRa(frequency, sf, bw, ...)` with send/recv/on_recv
- [x] **pycom_rgb.py** — RGB LED helper: color(), off(), heartbeat()
- [x] **board_config.py** for each board (pin constants)
- [x] **Manifests** freeze pycom_common + board modules

---

## Pending

### Phase 1 — Build & Hardware Validation

- [ ] Install ESP-IDF v5.5.1
- [ ] `git submodule update --init --recursive`
- [ ] `make BOARD=PYCOM_LOPY` compiles
- [ ] `make BOARD=PYCOM_LOPY4` compiles
- [ ] REPL over UART
- [ ] Pin toggle: `machine.Pin('P3', Pin.OUT).value(1)` → GPIO4
- [ ] WiFi: `network.WLAN(network.STA_IF).scan()` returns APs
- [ ] BLE: `bluetooth.BLE().active(True)` works
- [ ] NeoPixel on GPIO0 lights up
- [ ] Filesystem r/w persists across reboot
- [ ] LoPy4: PSRAM in `micropython.mem_info()`
- [ ] Verify all 24 P-pins with multimeter/logic analyzer

### Phase 2 — LoRa Hardware Testing

- [ ] SX1272 chip detection on LoPy
- [ ] SX1276 chip detection on LoPy4
- [ ] Point-to-point TX/RX between two boards (868 MHz SF7)
- [ ] RSSI/SNR readings
- [ ] Async recv via on_recv() callback
- [ ] RGB LED test on hardware

### Phase 3 — LoRaWAN and Optimizations (Future)

- [ ] Port `lemariva/uPyLoRaWAN` as frozen LoRaWAN MAC (OTAA/ABP)
- [ ] C user module for timing-critical ISR (Class A RX windows)
- [ ] OTA via board variant (`BOARD_VARIANT=OTA`)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| 4MB flash tight with WiFi+BLE+LoRa | Omit BLE in LoPy sdkconfig if needed |
| Python ISR latency on DIO0 | OK for raw LoRa; C module for LoRaWAN |
| GPIO23 diode-OR of DIO0/1/2 | Read IRQ flags register to disambiguate |
| Old Pycom bootloader in flash | Erase flash completely before first deploy |
| SX1272 vs SX1276 register diffs | Both chip paths implemented; test independently |

## File Tree

```
ports/esp32/boards/
├── pycom_common/
│   ├── sx127x.py           # SX1272/SX1276 radio driver
│   ├── lora.py             # High-level LoRa API
│   └── pycom_rgb.py        # RGB LED helper
├── PYCOM_LOPY/
│   ├── board.json
│   ├── manifest.py
│   ├── mpconfigboard.cmake
│   ├── mpconfigboard.h
│   ├── pins.csv
│   ├── sdkconfig.board
│   └── modules/
│       └── board_config.py
└── PYCOM_LOPY4/
    ├── board.json
    ├── manifest.py
    ├── mpconfigboard.cmake
    ├── mpconfigboard.h
    ├── partitions.csv
    ├── pins.csv
    ├── sdkconfig.board
    └── modules/
        └── board_config.py
```

## References

- Upstream ESP32 port template: `ports/esp32/boards/ESP32_GENERIC/`
- Upstream LoRa board: `ports/esp32/boards/LILYGO_TTGO_LORA32/`
- Archived Pycom source: `github.com/pycom/pycom-micropython-sigfox`
- Community SX127x driver: `github.com/Wei1234c/SX127x_driver_for_MicroPython_on_ESP8266`
- SX1276 datasheet: Semtech DS_SX1276-7-8-9_W_APP_V7
- SX1272 datasheet: Semtech DS_SX1272/73_V4
