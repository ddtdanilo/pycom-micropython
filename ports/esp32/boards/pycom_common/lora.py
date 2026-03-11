"""
High-level LoRa radio interface for Pycom boards.

Usage:
    from lora import LoRa

    radio = LoRa(frequency=868e6, sf=7, bw=125000, tx_power=14)
    radio.send(b'Hello')
    data = radio.recv(timeout=5000)
    print(radio.rssi, radio.snr)
"""

from machine import Pin, SPI
from sx127x import SX127x


class LoRa:
    """High-level LoRa radio for Pycom LoPy/LoPy4 boards."""

    def __init__(
        self,
        frequency=868000000,
        sf=7,
        bw=125000,
        cr=5,
        tx_power=14,
        preamble_length=8,
        sync_word=0x12,
        crc=True,
        implicit_header=False,
    ):
        """
        Initialize the LoRa radio with board-auto-detected pin config.

        Args:
            frequency: Carrier frequency in Hz (default 868 MHz)
            sf: Spreading factor 6-12 (default 7)
            bw: Bandwidth in Hz (default 125000)
            cr: Coding rate denominator 5-8 (default 5 = 4/5)
            tx_power: Transmit power in dBm (default 14)
            preamble_length: Preamble length in symbols (default 8)
            sync_word: Sync word (0x12=private, 0x34=LoRaWAN)
            crc: Enable CRC (default True)
            implicit_header: Use implicit header mode (default False)
        """
        import board_config as cfg

        reset_pin = None
        if cfg.LORA_RESET >= 0:
            reset_pin = Pin(cfg.LORA_RESET, Pin.OUT)

        spi = SPI(
            1,
            baudrate=10000000,
            polarity=0,
            phase=0,
            sck=Pin(cfg.LORA_SCLK),
            mosi=Pin(cfg.LORA_MOSI),
            miso=Pin(cfg.LORA_MISO),
        )

        self._radio = SX127x(
            spi=spi,
            cs_pin=Pin(cfg.LORA_CS),
            dio0_pin=Pin(cfg.LORA_DIO0),
            reset_pin=reset_pin,
            chip=cfg.LORA_CHIP,
        )

        # Apply configuration
        self._radio.set_frequency(int(frequency))
        self._radio.set_spreading_factor(sf)
        self._radio.set_bandwidth(bw)
        self._radio.set_coding_rate(cr)
        self._radio.set_tx_power(tx_power)
        self._radio.set_preamble_length(preamble_length)
        self._radio.set_sync_word(sync_word)
        self._radio.set_crc(crc)
        self._radio.set_implicit_header(implicit_header)

    def send(self, data):
        """Transmit data bytes. Blocks until complete."""
        if isinstance(data, str):
            data = data.encode()
        self._radio.send(data)

    def recv(self, timeout=0):
        """
        Receive a packet.

        Args:
            timeout: Timeout in ms. 0 = hardware timeout (single RX).

        Returns:
            bytes or None if timeout/error.
        """
        return self._radio.recv(timeout_ms=timeout)

    def on_recv(self, callback):
        """
        Register async receive callback.

        callback(data_bytes) is called on packet reception.
        Pass None to stop listening.
        """
        self._radio.on_recv(callback)

    @property
    def rssi(self):
        """Last received packet RSSI in dBm."""
        return self._radio.rssi

    @property
    def snr(self):
        """Last received packet SNR in dB."""
        return self._radio.snr

    def sleep(self):
        """Put radio into low-power sleep mode."""
        self._radio.sleep()

    def standby(self):
        """Put radio into standby mode."""
        self._radio.standby()
