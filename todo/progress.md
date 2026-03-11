# MicroPython Port for Pycom LoRa Devices — Progress

## Phase 1: Board Definitions and Basic Boot

### Step 1.1 — Fork and setup
- [x] Clone upstream MicroPython
- [x] Checkout v1.27.0
- [ ] Install ESP-IDF v5.5.1
- [ ] `git submodule update --init --recursive`

### Step 1.2 — Create PYCOM_LOPY board
- [x] `mpconfigboard.h` — board name, MCU, LoRa HW constants (CS=GPIO17, RESET=GPIO18, CHIP=1272)
- [x] `mpconfigboard.cmake` — IDF_TARGET=esp32, sdkconfig defaults
- [x] `sdkconfig.board` — 4MB flash (uses default partition table)
- [x] `pins.csv` — 24 Pycom P-pins mapped to GPIOs
- [x] `board.json` — metadata (mcu=esp32, features=[BLE, WiFi, LoRa])
- [x] `manifest.py` — includes base + pycom_common + board modules
- [x] `modules/board_config.py` — LoRa pin constants for SX1272

### Step 1.3 — Create PYCOM_LOPY4 board
- [x] `mpconfigboard.h` — LoRa HW constants (CS=GPIO18, RESET=-1, CHIP=1276)
- [x] `mpconfigboard.cmake` — adds sdkconfig.spiram
- [x] `sdkconfig.board` — 8MB flash, custom partition table
- [x] `partitions.csv` — ~2MB firmware + ~6MB VFS
- [x] `pins.csv` — identical to PYCOM_LOPY
- [x] `board.json` — metadata with SPIRAM feature
- [x] `manifest.py` — includes base + pycom_common + board modules
- [x] `modules/board_config.py` — LoRa pin constants for SX1276

### Step 1.4 — Pin mapping
- [x] All 24 P-pins defined in pins.csv for both boards
- [ ] Verify on hardware with multimeter/logic analyzer

### Step 1.5 — Build and validate
- [ ] `make BOARD=PYCOM_LOPY` compiles successfully
- [ ] `make BOARD=PYCOM_LOPY4` compiles successfully
- [ ] REPL works over UART
- [ ] Pin toggling works (`machine.Pin('P3', Pin.OUT).value(1)`)
- [ ] WiFi scan works
- [ ] BLE activates
- [ ] NeoPixel on GPIO0 works
- [ ] Filesystem persists across reboots
- [ ] PSRAM detected on LoPy4

---

## Phase 2: LoRa Driver (Raw LoRa / Point-to-Point)

### Step 2.1 — Shared module directory
- [x] Created `ports/esp32/boards/pycom_common/`

### Step 2.2 — SX127x driver
- [x] `sx127x.py` — unified SPI driver for SX1272/SX1276
  - [x] SPI register read/write
  - [x] Chip auto-detection via version register
  - [x] Bandwidth encoding differences (SX1272 vs SX1276)
  - [x] Coding rate encoding differences
  - [x] RSSI calculation differences
  - [x] DIO0 interrupt handler with IRQ flags disambiguation
  - [x] Hardware reset (LoPy) / soft reset (LoPy4)
  - [x] send() — blocking TX
  - [x] recv() — blocking RX with timeout
  - [x] on_recv() — async RX via DIO0 interrupt
  - [ ] Test on real SX1272 hardware
  - [ ] Test on real SX1276 hardware

### Step 2.3 — High-level LoRa module
- [x] `lora.py` — simple LoRa class with send/recv/on_recv
  - [x] Auto-detects board config from board_config module
  - [x] Configurable: frequency, SF, BW, CR, TX power, preamble, sync word, CRC
  - [ ] Test point-to-point communication between two boards

### Step 2.4 — Board-specific config modules
- [x] `PYCOM_LOPY/modules/board_config.py`
- [x] `PYCOM_LOPY4/modules/board_config.py`

### Step 2.5 — RGB LED helper
- [x] `pycom_rgb.py` — color(), off(), heartbeat()
- [ ] Test on hardware

### Step 2.6 — Update manifests
- [x] Both boards freeze pycom_common + board modules

---

## Phase 3: LoRaWAN and Optimizations (Future)
- [ ] Port uPyLoRaWAN as frozen Python LoRaWAN MAC layer
- [ ] Optional C user module for timing-critical ISR handling
- [ ] OTA support via board variant

---

## File Tree (implemented)

```
ports/esp32/boards/
├── pycom_common/
│   ├── sx127x.py          ✅
│   ├── lora.py            ✅
│   └── pycom_rgb.py       ✅
├── PYCOM_LOPY/
│   ├── board.json         ✅
│   ├── manifest.py        ✅
│   ├── mpconfigboard.cmake ✅
│   ├── mpconfigboard.h    ✅
│   ├── pins.csv           ✅
│   ├── sdkconfig.board    ✅
│   └── modules/
│       └── board_config.py ✅
└── PYCOM_LOPY4/
    ├── board.json         ✅
    ├── manifest.py        ✅
    ├── mpconfigboard.cmake ✅
    ├── mpconfigboard.h    ✅
    ├── partitions.csv     ✅
    ├── pins.csv           ✅
    ├── sdkconfig.board    ✅
    └── modules/
        └── board_config.py ✅
```

## Notes
- LoPy uses default `partitions-4MiBplus.csv` (4MB flash, no custom table needed)
- LoPy4 needs custom partition table for 8MB flash with explicit VFS partition
- `neopixel` is already included in the base ESP32 manifest — no need to add separately
- pins.csv format follows upstream MicroPython convention (name,GPIO)
