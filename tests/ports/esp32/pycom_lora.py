# Test the high-level LoRa API on Pycom LoPy/LoPy4 boards.
# This test requires a Pycom board with SX1272 or SX1276 radio.

try:
    import board_config
except ImportError:
    print("SKIP")
    raise SystemExit

from lora import LoRa

# Test 1: Default initialization
radio = LoRa()
print("init default: OK")

# Test 2: Custom parameters
radio = LoRa(
    frequency=868000000,
    sf=9,
    bw=250000,
    cr=6,
    tx_power=10,
    preamble_length=12,
    sync_word=0x34,
    crc=True,
    implicit_header=False,
)
print("init custom: OK")

# Test 3: RSSI and SNR properties
_ = radio.rssi
_ = radio.snr
print("properties: OK")

# Test 4: Power modes
radio.sleep()
radio.standby()
print("power modes: OK")

# Test 5: Send (TX) - transmit a test packet
radio.send(b"test")
print("send bytes: OK")

radio.send("test string")
print("send string: OK")

# Test 6: Receive with short timeout (no packet expected)
result = radio.recv(timeout=100)
print("recv timeout:", result is None)

# Test 7: Async callback registration and deregistration
received = []


def on_packet(data):
    received.append(data)


radio.on_recv(on_packet)
print("on_recv set: OK")

radio.on_recv(None)
print("on_recv clear: OK")

print("all tests passed")
