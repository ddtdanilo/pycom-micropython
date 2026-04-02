# Plan: PR de Pycom LoRa Boards a MicroPython Upstream

## Objetivo

Enviar PR al repositorio upstream `micropython/micropython` con:
- Board definitions para Pycom LoPy (SX1272) y LoPy4 (SX1276)
- Driver SX127x LoRa en Python (frozen module)
- Tests unitarios que corran sin hardware
- Todo formateado según estándares del upstream

## Requisitos del Upstream (de CODECONVENTIONS.md)

- **Formato commits**: `esp32/boards/PYCOM_LOPY: Add board definition.`
- **Signed-off-by**: `Signed-off-by: Danilo D <danilodt@gmail.com>` (DCO)
- **Python format**: `ruff format` (line-length 99)
- **C format**: `tools/codeformat.py` (uncrustify v0.71/0.72)
- **Spell check**: `codespell` v2.4.1
- **NO AI co-author**: Nunca

## Pasos

### 1. Fix Code Issues
- [ ] pycom_rgb.py: Corregir docstring ejemplo de import
- [ ] Verificar que no hay debug prints ni TODOs

### 2. Code Formatting
- [ ] `ruff format` en todos los .py de pycom_common/ y modules/
- [ ] `tools/codeformat.py` en archivos .h
- [ ] `codespell` pasa limpio

### 3. Write Tests
- [ ] Crear tests unitarios para el driver SX127x:
  - Mock de SPI/Pin (sin hardware)
  - RSSI calculation: SX1272 (-139+raw) vs SX1276 HF (-157+raw) vs SX1276 LF (-164+raw)
  - BW encoding por chip
  - CR encoding por chip
  - SF validation
  - Config parameters (frequency, power, etc.)
- [ ] Ubicación: `tests/ports/esp32/` (patrón existente)
- [ ] Verificar que pasan con `python tests/run-tests.py`

### 4. Prepare Commits
- [ ] Reorganizar en commits limpios:
  1. `esp32/boards/pycom_common: Add SX127x LoRa driver for Pycom boards.`
  2. `esp32/boards/PYCOM_LOPY: Add Pycom LoPy board definition.`
  3. `esp32/boards/PYCOM_LOPY4: Add Pycom LoPy4 board definition.`
  4. `tests/ports/esp32: Add tests for Pycom SX127x LoRa driver.`
- [ ] Cada commit con `Signed-off-by: Danilo D <danilodt@gmail.com>`
- [ ] Author: `Danilo D <danilodt@gmail.com>`

### 5. Verify CI Locally
- [ ] `tools/verifygitlog.py` pasa
- [ ] `ruff format --check` pasa
- [ ] `codespell` pasa
- [ ] Tests pasan

### 6. Create PR
- [ ] Push branch al fork
- [ ] `gh pr create` hacia micropython/micropython
- [ ] PR body con Summary, Testing, y trade-offs
- [ ] Seguir `.github/pull_request_template.md`

## Archivos Críticos

```
ports/esp32/boards/pycom_common/sx127x.py    # Driver SX1272/SX1276
ports/esp32/boards/pycom_common/lora.py      # High-level LoRa API
ports/esp32/boards/pycom_common/pycom_rgb.py # RGB LED helper
ports/esp32/boards/PYCOM_LOPY/*              # Board definition LoPy
ports/esp32/boards/PYCOM_LOPY4/*             # Board definition LoPy4
tests/ports/esp32/test_sx127x.py             # Tests (por crear)
```
