# Project Guidelines

## Git Commits
- Never add AI as co-author in commits. No `Co-Authored-By` lines for AI tools.
- Claude/AI must NEVER appear as author or committer. Always use the project owner's identity:
  - Author: `Danilo D <danilodt@gmail.com>`
  - Committer: `Danilo D <danilodt@gmail.com>`
  - Always set `GIT_COMMITTER_NAME="Danilo D"` and `GIT_COMMITTER_EMAIL="danilodt@gmail.com"` when committing.
  - Always use `--author="Danilo D <danilodt@gmail.com>"` on every commit.

## Upstream PRs — Estado actual

### PR Principal: micropython/micropython#19026
- **Branch**: `pycom-lora-upstream` (en fork `ddtdanilo/micropython`)
- **Estado**: Abierto, 43/44 CI checks pasan (ruff fixed, pendiente re-run)
- **Reviewer**: robert-hh (contributor, hizo trial build exitoso en LoPy4)
- **Contenido**: Board definitions (PYCOM_LOPY, PYCOM_LOPY4), SX127x driver, LoRaWAN MAC, OTA variants, tests
- **Feedback aplicado**: Pines LoRa en pins.csv, board_config.py eliminado, imágenes, ruff fixes
- **Pendiente post-merge de los otros PRs**: Cambiar freeze() → require(), quitar drivers de pycom_common/

### PR Imágenes: micropython/micropython-media#116
- **Branch**: `add-pycom-boards` (en fork `ddtdanilo/micropython-media`)
- **Contenido**: pycom-lopy.png, pycom-lopy4.png en boards/
- **Estado**: Abierto, esperando review

### PR Drivers: micropython/micropython-lib#1102
- **Branch**: `add-pycom-lora` (en fork `ddtdanilo/micropython-lib`)
- **Contenido**: lora-sx127x-pycom (SX1272/SX1276 unificado), lora-lorawan (LoRaWAN 1.0.x MAC)
- **Estado**: Abierto, esperando review

## Branches locales
- `pycom-lora-port`: Branch original con todo el desarrollo
- `pycom-lora-upstream`: Branch del PR anterior (8 commits, ya reemplazada)
- `pycom-lora-v2`: Branch actual del PR (5 commits limpios, reestructurados)

## Build
- ESP-IDF v5.4 en `~/esp/esp-idf`
- Activar: `export IDF_PATH=$HOME/esp/esp-idf && eval "$(python3 $IDF_PATH/tools/idf_tools.py export)"`
- Build: `make -C ports/esp32 BOARD=PYCOM_LOPY4 -j4`
- OTA: `make -C ports/esp32 BOARD=PYCOM_LOPY4 BOARD_VARIANT=OTA -j4`

## Notas técnicas
- El driver upstream `lora-sx127x` (micropython-lib) NO soporta SX1272 — solo SX1276 (version 0x12). Nuestro driver es el único que soporta ambos.
- micropython-lib es un submodule git — no se pueden agregar archivos directamente en el repo principal
- micropython-media es un repo separado para imágenes de boards
- Commits upstream requieren: formato `path: Description.`, `Signed-off-by:`, `tools/verifygitlog.py`
