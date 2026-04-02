# Roadmap completo — Pycom LoRa Port

## Context

El port de Pycom LoPy/LoPy4 a MicroPython upstream ya tiene board definitions, driver SX127x custom, y un PR abierto (micropython/micropython#19026). El roadmap pendiente incluye: migrar al driver upstream de micropython-lib, OTA variants, LoRaWAN, C user module para ISR, y scripts de validación de hardware.

**Descubrimiento clave**: `lib/micropython-lib/micropython/lora/` ya tiene un stack LoRa upstream con driver SX127x superior (async/await, time-on-air, InvertIQ, mejor arquitectura). Debemos migrar a él.

---

## Phase 1: CANCELADA — Mantener driver custom

### Por qué se cancela

El driver upstream (`lora-sx127x`) en `lib/micropython-lib/micropython/lora/` **solo soporta SX1276** (version register 0x12). **No soporta SX1272** (version 0x22) que usa el LoPy.

- Línea 266-267 de `lora-sx127x/lora/sx127x.py`: `if version != 0x12: raise RuntimeError`
- El SX1272 tiene diferencias de registros: BW encoding, CR bits, CRC location, RSSI offset
- Nuestro `pycom_common/sx127x.py` maneja ambos chips en un driver unificado

### Decisión

Mantener nuestro driver custom (`pycom_common/sx127x.py` + `lora.py`). Es la única implementación en el ecosistema MicroPython que soporta SX1272+SX1276 unificado.

Futuro: contribuir soporte SX1272 al upstream como PR separado

---

## Phase 2: OTA Board Variants

### Qué hacer

1. **PYCOM_LOPY4 OTA variant**:
   - `ports/esp32/boards/PYCOM_LOPY4/mpconfigvariant_OTA.cmake`
   - `ports/esp32/boards/PYCOM_LOPY4/sdkconfig.ota`
   - `ports/esp32/boards/PYCOM_LOPY4/partitions-8MiB-ota.csv`

2. **PYCOM_LOPY OTA variant** (4MB — tight pero posible):
   - `ports/esp32/boards/PYCOM_LOPY/mpconfigvariant_OTA.cmake`
   - `ports/esp32/boards/PYCOM_LOPY/sdkconfig.ota`
   - Usar `ports/esp32/partitions-4MiB-ota.csv` existente

3. **Helper OTA en Python**: `pycom_common/ota.py`
   - Funciones: `check_update()`, `apply_update(url)`, `rollback()`
   - Usa `esp32.Partition` API (set_boot, get_next_update, mark_app_valid)
   - HTTP download + write a OTA partition

### Partition layout LoPy4 OTA (8MB)

```
otadata,  data, ota,     0x9000,   0x2000
phy_init, data, phy,     0xf000,   0x1000
ota_0,    app,  ota_0,   0x10000,  0x200000   # 2MB
ota_1,    app,  ota_1,   0x210000, 0x200000   # 2MB
nvs,      data, nvs,     0x410000, 0x6000
vfs,      data, fat,     0x420000, 0x3E0000   # ~3.9MB filesystem
```

### Referencia

- Patrón: `ports/esp32/boards/ESP32_GENERIC/mpconfigvariant_OTA.cmake`
- Partition 8MB OTA: `ports/esp32/boards/SIL_MANT1S/partitions-8MiB-ota.csv`
- OTA C API: `ports/esp32/esp32_partition.c` (set_boot, get_next_update, mark_app_valid)

---

## Phase 3: LoRaWAN MAC Layer

### Contexto

Ni el driver upstream ni el nuestro implementan LoRaWAN (solo raw LoRa modem). Necesitamos un MAC layer para OTAA/ABP y Class A.

### Qué hacer

1. **Portar/adaptar un LoRaWAN MAC** como frozen module:
   - Base: `lemariva/uPyLoRaWAN` o implementación propia minimal
   - Solo Class A inicialmente (TX → RX1 → RX2, timing windows)
   - OTAA join + ABP
   - AES-128 para MIC y payload encryption (usar `ucryptolib` de MicroPython)

2. **Crear `pycom_common/lorawan.py`**:
   - Class `LoRaWAN(modem, dev_eui, app_eui, app_key)` para OTAA
   - Class `LoRaWAN(modem, dev_addr, nwk_skey, app_skey)` para ABP
   - `join()` — OTAA join procedure
   - `send(port, data, confirmed=False)` — uplink
   - `recv()` — downlink (from RX windows)
   - MAC command handling (LinkADRReq, DutyCycleReq, RXParamSetupReq, DevStatusReq)

3. **Crear `pycom_common/lorawan_crypto.py`**:
   - AES-128-CMAC para MIC calculation
   - AES-128-CTR para payload encryption
   - Session key derivation (AppSKey, NwkSKey from AppKey)

4. **Tests**: Mock del modem para testear join flow, encrypt/decrypt, MAC parsing

### Riesgo: Timing

- Class A RX1 window: 1 segundo después de TX end (±20ms tolerancia)
- Class A RX2 window: 2 segundos después de TX end
- Python puede manejar esto si el modem ya está en RX antes del deadline
- Si no es suficiente → Phase 4 (C module)

---

## Phase 4: C User Module para ISR timing-critical

### Cuándo

Solo si Phase 3 muestra que Python no puede cumplir los timing de LoRaWAN Class A (RX1/RX2 windows). Se evalúa después de hardware testing.

### Qué hacer (si se necesita)

1. **Crear `ports/esp32/boards/pycom_common/cmodules/lorawan_timer/`**:
   - `lorawan_timer.c` — Timer de hardware ESP32 para RX windows
   - `micropython.cmake` — Build integration
   - Registra un timer que cambia el modem a RX mode en el momento exacto

2. **Integrar en el build**: Agregar `USER_C_MODULES` en mpconfigboard.cmake

### Referencia

- Ejemplo: `examples/usercmodule/cexample/`
- Build: `ports/esp32/esp32_common.cmake` línea 49 (include usermod.cmake)

---

## Phase 5: Scripts de validación de hardware

### Qué hacer

Crear scripts de test que el usuario ejecute en hardware real vía REPL:

1. **`pycom_common/test_hardware.py`** (frozen, ejecutable desde REPL):
   - Test de cada P-pin (P0-P23) como output/input
   - Test WiFi scan
   - Test BLE active
   - Test NeoPixel RGB
   - Test filesystem read/write
   - Test PSRAM (LoPy4)
   - Test SX127x chip detection y register r/w
   - Test LoRa send/recv entre dos boards

2. **Actualizar tests en `tests/ports/esp32/`** con los nuevos módulos

---

## Status (2026-04-02)

### Roadmap de desarrollo
- [x] **Phase 1**: CANCELADA — upstream `lora-sx127x` no soporta SX1272, se mantiene driver custom
- [x] **Phase 2**: OTA variants creados y compilados (LoPy 7% free, LoPy4 24% free)
- [x] **Phase 3**: LoRaWAN MAC implementado (OTAA/ABP, Class A, AES-128 crypto)
- [ ] **Phase 4**: C user module — pendiente, solo si Python timing insuficiente en hardware
- [x] **Phase 5**: Hardware validation script creado
- [x] **Builds**: 4 configuraciones compilan (LoPy, LoPy4, LoPy OTA, LoPy4 OTA)
- [x] **Firmware**: `pycom-lopy4-firmware.tar.gz` generado (1.0MB)

### PRs abiertos

| PR | Repo | Estado | Notas |
|----|------|--------|-------|
| [#19026](https://github.com/micropython/micropython/pull/19026) | micropython/micropython | Abierto, review de robert-hh | Board defs, driver, LoRaWAN, OTA, tests. 5 commits. Feedback aplicado. |
| [#116](https://github.com/micropython/micropython-media/pull/116) | micropython/micropython-media | Abierto, esperando review | Imágenes: pycom-lopy.png, pycom-lopy4.png |
| [#1102](https://github.com/micropython/micropython-lib/pull/1102) | micropython/micropython-lib | Abierto, esperando review | Paquetes: lora-sx127x-pycom, lora-lorawan |

### Flujo post-merge
1. Cuando #116 (media) se mergee → quitar .png del PR #19026
2. Cuando #1102 (lib) se mergee → en PR #19026:
   - Actualizar submodule `lib/micropython-lib`
   - Cambiar manifests: `freeze("pycom_common")` → `require("lora-sx127x-pycom")` + `require("lora-lorawan")` + `freeze("pycom_common")` (solo rgb, ota, test_hardware)
   - Quitar `sx127x.py`, `lorawan.py`, `lorawan_crypto.py` de `pycom_common/`
3. Cuando #19026 se mergee → robert-hh confirmó que compila y WiFi funciona

### Reviewer feedback (robert-hh)
- [x] Mover driver a micropython-lib → PR #1102
- [x] Agregar pines LoRa a pins.csv → Hecho, board_config.py eliminado
- [x] Agregar imágenes a micropython-media → PR #116
- [x] Fix ruff CI → const import y SPI import arreglados
- [ ] Trial build confirmado: compila con ESP-IDF v5.5.1, WiFi funciona, LoRa sin probar aún
