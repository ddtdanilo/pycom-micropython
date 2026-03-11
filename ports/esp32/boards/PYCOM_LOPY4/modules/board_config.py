"""Board-specific hardware configuration for Pycom LoPy4 / L04."""

# LoRa radio (SX1276) pin assignments
LORA_MOSI = 27
LORA_MISO = 19
LORA_SCLK = 5
LORA_CS = 18
LORA_DIO0 = 23
LORA_RESET = -1  # No hardware reset on LoPy4
LORA_CHIP = 1276
