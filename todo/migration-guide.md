# Migration Guide: Pycom Firmware 1.20.x → MicroPython Upstream

This guide helps Pycom LoPy/LoPy4 users migrate from the old Pycom firmware
(based on MicroPython ~v1.9, ESP-IDF v3.x) to upstream MicroPython v1.27.0+
(ESP-IDF v5.4+) with the new Pycom board definitions.

---

## Quick Reference

| Feature | Pycom 1.20.x | MicroPython Upstream |
|---------|--------------|---------------------|
| Base version | MicroPython ~v1.9 (2017) | v1.27.0+ (2025) |
| ESP-IDF | v3.x | v5.4+ |
| LoRa API | `network.LoRa` + sockets | `sx127x.SX127x` (direct driver) |
| LoRaWAN | Built-in (C) | `lorawan.LoRaWAN` (Python) |
| RGB LED | `pycom.rgbled()` | `pycom_rgb.LED()` |
| NVS storage | `pycom.nvs_set/get()` | `esp32.NVS()` |
| OTA updates | `pycom.ota_start/write/finish()` | `ota.OTA()` |
| Pin names | `Pin('P12')` | `Pin('P12')` (same!) |
| WiFi | `network.WLAN(mode=WLAN.STA)` | `network.WLAN(network.STA_IF)` |

---

## 1. LoRa — Raw P2P Communication

### Before (Pycom)

```python
from network import LoRa
import socket

lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868,
            frequency=868000000, sf=7, bandwidth=LoRa.BW_125KHZ,
            coding_rate=LoRa.CODING_4_5, tx_power=14)

# Send
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setblocking(True)
s.send(b'Hello')

# Receive
s.setblocking(False)
data = s.recv(64)

# Stats
print(lora.stats().rssi)
print(lora.stats().snr)
```

### After (Upstream)

```python
from machine import Pin, SPI
from sx127x import SX127x

spi = SPI(1, baudrate=10_000_000, polarity=0, phase=0,
          sck=Pin("LORA_SCLK"), mosi=Pin("LORA_MOSI"),
          miso=Pin("LORA_MISO"))

# Reset pin: LoPy has one, LoPy4 does not
try:
    reset = Pin("LORA_RESET", Pin.OUT)
except ValueError:
    reset = None

radio = SX127x(spi, cs_pin=Pin("LORA_CS"),
               dio0_pin=Pin("LORA_DIO0"), reset_pin=reset)

radio.set_frequency(868_000_000)
radio.set_spreading_factor(7)
radio.set_bandwidth(125_000)
radio.set_coding_rate(5)
radio.set_tx_power(14)

# Send
radio.send(b'Hello')

# Receive (blocking with timeout)
data = radio.recv(timeout_ms=5000)

# Receive (async callback)
def on_packet(data):
    print("Got:", data)
radio.on_recv(on_packet)

# Stats
print(radio.rssi)
print(radio.snr)

# Power management
radio.sleep()
radio.standby()
```

### Key Differences

- No socket abstraction — call `send()` / `recv()` directly on the driver
- Pin names (`LORA_CS`, etc.) are defined in `pins.csv`, no `board_config` needed
- SPI is initialized explicitly (Pycom did it internally in C)
- `radio.recv(timeout_ms=5000)` replaces `s.setblocking()` + `s.recv()`
- RSSI/SNR are properties, not inside a `stats()` tuple

---

## 2. LoRaWAN

### Before (Pycom)

```python
from network import LoRa
import socket

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# OTAA Join
lora.join(activation=LoRa.OTAA,
          auth=(dev_eui, app_eui, app_key),
          timeout=0)
while not lora.has_joined():
    time.sleep(2.5)

# Send data
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)  # DR5 = SF7
s.setblocking(True)
s.send(bytes([1, 2, 3]))

# Receive downlink
s.setblocking(False)
data = s.recv(64)

# Persist join state across deep sleep
lora.nvram_save()
# After waking up:
lora.nvram_restore()
```

### After (Upstream)

```python
from machine import Pin, SPI
from sx127x import SX127x
from lorawan import LoRaWAN

# Initialize radio (same as raw LoRa above)
spi = SPI(1, baudrate=10_000_000, polarity=0, phase=0,
          sck=Pin("LORA_SCLK"), mosi=Pin("LORA_MOSI"),
          miso=Pin("LORA_MISO"))
try:
    reset = Pin("LORA_RESET", Pin.OUT)
except ValueError:
    reset = None
radio = SX127x(spi, cs_pin=Pin("LORA_CS"),
               dio0_pin=Pin("LORA_DIO0"), reset_pin=reset)

# OTAA Join
wan = LoRaWAN(radio, mode=LoRaWAN.OTAA,
              dev_eui=bytes.fromhex('0011223344556677'),
              app_eui=bytes.fromhex('0011223344556677'),
              app_key=bytes.fromhex('00112233445566778899AABBCCDDEEFF'))
wan.join(timeout=30000)
print("Joined:", wan.joined)

# Send uplink (port 1)
wan.send(1, bytes([1, 2, 3]))

# Send and check for downlink
downlink = wan.send(1, bytes([4, 5, 6]))
if downlink:
    print("Downlink:", downlink)

# ABP (alternative)
wan = LoRaWAN(radio, mode=LoRaWAN.ABP,
              dev_addr=0x01020304,
              nwk_skey=bytes.fromhex('00112233445566778899AABBCCDDEEFF'),
              app_skey=bytes.fromhex('00112233445566778899AABBCCDDEEFF'))
wan.send(1, b'Hello ABP')
```

### Key Differences

- No socket API — use `wan.send(port, data)` and `wan.recv()` directly
- Data rate set via `radio.set_spreading_factor()` instead of `SO_DR` socket option
- `wan.join(timeout=30000)` blocks; no need to poll `has_joined()`
- `wan.joined` property replaces `lora.has_joined()`
- `nvram_save()` / `nvram_restore()` not yet implemented

### LoRaWAN Feature Comparison

| Feature | Pycom 1.20.x | Upstream |
|---------|-------------|----------|
| OTAA | Yes | Yes |
| ABP | Yes | Yes |
| Class A | Yes | Yes |
| Class C | Yes | Not yet |
| Multi-region | EU868, US915, AU915, AS923, CN470, IN865 | EU868 (others easy to add) |
| ADR | Yes | Not yet |
| Channel management | `add_channel()`, `remove_channel()` | Not yet |
| Confirmed uplinks | Yes | Yes (`confirmed=True`) |
| NVRAM persistence | `nvram_save/restore/erase()` | Not yet |
| MAC commands | Full | Basic (LinkADR, DutyCycle, RXParam, DevStatus) |

---

## 3. RGB LED

### Before (Pycom)

```python
import pycom

pycom.heartbeat(False)       # Disable blue heartbeat
pycom.rgbled(0xFF0000)       # Red
pycom.rgbled(0x00FF00)       # Green
pycom.rgbled(0x0000FF)       # Blue
pycom.rgbled(0x000000)       # Off
pycom.heartbeat(True)        # Re-enable heartbeat
```

### After (Upstream)

```python
from pycom_rgb import LED

led = LED()                  # GPIO0 NeoPixel
led.color(255, 0, 0)        # Red
led.color(0, 255, 0)        # Green
led.color(0, 0, 255)        # Blue
led.off()                   # Off
led.heartbeat(cycles=3)     # Blue pulsing heartbeat

# Or use neopixel directly
from neopixel import NeoPixel
from machine import Pin
np = NeoPixel(Pin("NEOPIXEL", Pin.OUT), 1)
np[0] = (255, 0, 0)
np.write()
```

### Key Differences

- Color is `(r, g, b)` tuple instead of single `0xRRGGBB` hex value
- `pycom_rgb.LED` is a helper class; you can also use `neopixel` directly
- Named pin `NEOPIXEL` is available in `pins.csv`

---

## 4. NVS (Non-Volatile Storage)

### Before (Pycom)

```python
import pycom

pycom.nvs_set('counter', 42)
val = pycom.nvs_get('counter')    # 42
pycom.nvs_erase('counter')
pycom.nvs_erase_all()
```

### After (Upstream)

```python
from esp32 import NVS

nvs = NVS("app")                   # Namespace
nvs.set_i32("counter", 42)
nvs.commit()

val = nvs.get_i32("counter")       # 42
nvs.erase_key("counter")
nvs.commit()

# For strings/blobs
nvs.set_blob("name", "hello")
buf = bytearray(10)
nvs.get_blob("name", buf)
```

### Key Differences

- Must specify a namespace (`NVS("app")`)
- Separate methods for integers (`set_i32/get_i32`) and blobs (`set_blob/get_blob`)
- Must call `commit()` to persist changes
- No `erase_all()` — erase keys individually

---

## 5. OTA Firmware Updates

### Before (Pycom)

```python
import pycom

pycom.ota_start()
# Write firmware in 4KB chunks
with open('/flash/firmware.bin', 'rb') as f:
    while True:
        chunk = f.read(4096)
        if not chunk:
            break
        pycom.ota_write(chunk)
pycom.ota_finish()
# Reboot into new firmware
import machine
machine.reset()
```

### After (Upstream)

Requires `BOARD_VARIANT=OTA` firmware build.

```python
from ota import OTA

updater = OTA()
print("Running:", updater.current_partition)
print("Target:", updater.target_partition)

# From HTTP URL (downloads + writes + reboots)
updater.apply_update("http://server/micropython.bin")

# Or from local file
updater.apply_update_from_file("/firmware.bin")

# After reboot, validate the new firmware
OTA.validate()  # Call early in boot.py!

# Rollback to previous firmware
updater.rollback()
```

### Key Differences

- Higher-level API: `apply_update(url)` handles download + write + reboot
- Uses ESP-IDF native OTA (`esp32.Partition` API)
- Must call `OTA.validate()` after successful boot, or bootloader rolls back
- Partition layout: `ota_0` / `ota_1` (each ~2MB on LoPy4)

---

## 6. WiFi

### Before (Pycom)

```python
from network import WLAN

wlan = WLAN(mode=WLAN.STA)
wlan.connect('MySSID', auth=(WLAN.WPA2, 'password'))
while not wlan.isconnected():
    time.sleep(0.5)
print(wlan.ifconfig())
nets = wlan.scan()
```

### After (Upstream)

```python
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('MySSID', 'password')
while not wlan.isconnected():
    time.sleep(0.5)
print(wlan.ifconfig())
nets = wlan.scan()
```

### Key Differences

- `WLAN(network.STA_IF)` instead of `WLAN(mode=WLAN.STA)`
- Must call `wlan.active(True)` explicitly
- Password is a positional arg, not inside `auth=()` tuple
- `scan()`, `isconnected()`, `ifconfig()`, `disconnect()` — identical
- No `smartConfig()`, `promiscuous()`, `send_raw()`, `wifi_on_boot()`

---

## 7. Pins

### Before (Pycom)

```python
from machine import Pin

p = Pin('P12', mode=Pin.OUT)
p.value(1)
p.toggle()
p.hold(True)                     # Persist through deep sleep
p.callback(Pin.IRQ_RISING, handler=my_func)
```

### After (Upstream)

```python
from machine import Pin

p = Pin('P12', Pin.OUT)          # Same pin names!
p.value(1)
p.value(not p.value())           # No toggle(), manual flip
# p.hold() — not available
p.irq(trigger=Pin.IRQ_RISING, handler=my_func)
```

### Key Differences

- Same P0-P23 pin names (defined in `pins.csv`)
- Additional named pins: `LORA_CS`, `LORA_MOSI`, `LORA_MISO`, `LORA_SCLK`, `LORA_DIO0`, `LORA_RESET` (LoPy only), `NEOPIXEL`
- No `pin.toggle()` — use `pin.value(not pin.value())`
- No `pin.hold()` — was Pycom-specific for deep sleep state retention
- `pin.callback()` → `pin.irq()` (standard MicroPython)

---

## 8. SPI

### Before (Pycom)

```python
from machine import SPI

spi = SPI(0, mode=SPI.MASTER, baudrate=10000000,
          pins=('P10', 'P11', 'P12'))
```

### After (Upstream)

```python
from machine import SPI, Pin

spi = SPI(1, baudrate=10000000,
          sck=Pin('P10'), mosi=Pin('P11'), miso=Pin('P12'))
```

### Key Differences

- Bus ID `1` instead of `0`
- Keyword arguments for pins instead of `pins=()` tuple
- No `mode=SPI.MASTER` (master is the default and only mode)
- Methods identical: `write()`, `read()`, `readinto()`, `write_readinto()`

---

## 9. Features Not Available in Upstream

These Pycom-specific features have no equivalent in upstream MicroPython:

| Feature | Notes |
|---------|-------|
| `pycom.wifi_on_boot()` | Configure in `boot.py` manually |
| `pycom.lte_modem_en_on_boot()` | LTE not applicable to LoPy/LoPy4 |
| `pycom.smart_config_on_boot()` | Not available |
| `pycom.pybytes_on_boot()` | Pybytes platform no longer online |
| `pycom.sigfox_info()` | Sigfox not supported |
| `pycom.bootmgr()` | Use `esp32.Partition` API |
| `pycom.pulses_get()` | Use `machine.time_pulse_us()` (partial) |
| `pycom.wdt_on_boot()` | Use `machine.WDT()` in `boot.py` |
| `lora.mesh()` / `lora.cli()` | OpenThread mesh not available |
| `lora.ischannel_free()` | CAD not yet implemented |
| `WLAN.promiscuous()` | Monitor mode not available |
| `WLAN.send_raw()` | Raw frame injection not available |
| `WLAN.smartConfig()` | SmartConfig not available |
| `pin.hold()` | Deep sleep pin state retention not available |
| `pin.toggle()` | Use `pin.value(not pin.value())` |

---

## 10. What You Gain

Moving to upstream MicroPython gives you:

- **Python 3.11+ features**: f-strings, walrus operator, match/case, exception groups
- **Stable asyncio**: Full async/await with proper task scheduling
- **Better networking**: TLS 1.3, WPA3, updated mbedTLS
- **BLE 5.0**: NimBLE stack with improved API
- **Package manager**: `mip.install("package")` from REPL
- **Active maintenance**: Thousands of bug fixes since 2017
- **PSRAM integration**: Unified heap with SPIRAM on LoPy4
- **Community support**: Full upstream MicroPython documentation and forums
