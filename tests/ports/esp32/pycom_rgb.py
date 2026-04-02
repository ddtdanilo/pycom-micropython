# Test the RGB LED helper on Pycom boards.
# This test requires a Pycom board with WS2812 NeoPixel on GPIO0.

try:
    import board_config
except ImportError:
    print("SKIP")
    raise SystemExit

from pycom_rgb import LED

# Test 1: Initialization
led = LED()
print("init: OK")

# Test 2: Set color
led.color(255, 0, 0)
print("color red: OK")

led.color(0, 255, 0)
print("color green: OK")

led.color(0, 0, 255)
print("color blue: OK")

# Test 3: Off
led.off()
print("off: OK")

# Test 4: Heartbeat (1 cycle for speed)
led.heartbeat(color=(0, 0, 20), cycles=1)
print("heartbeat: OK")

print("all tests passed")
