# einkdriver.py - driver for the Horizons Crux badge e-ink panels.
#
# These are surplus shelf-label panels (UC81xx-family controller) with NO
# factory waveform in OTP, so the waveform (LUT) is supplied from here.
# Quirks discovered during bring-up (do not "simplify" these away):
#   - BUSY (GP5) idles HIGH and the refresh waveform loops forever, so the
#     refresh is TIMED: start it, wait drive_ms, then hard-reset the panel.
#   - RAM data only lands when every data byte gets its own CS window, and
#     each plane write must be committed with 0x11 (DATA_STOP) + 0x92.
#   - Panels are mixed stock: 2.66" = 152x296, 2.9" = 128x296.

from machine import Pin, SoftSPI
import framebuf
import utime

BUSY_PIN = 5
RST_PIN = 6
DC_PIN = 7
CS_PIN = 8
SCK_PIN = 9
MOSI_PIN = 10


class EPD:
    def __init__(self, width=152, height=296, drive_ms=350, clear_ms=800):
        self.width = width            # sources (portrait width): 152 or 128
        self.height = height          # gates: 296
        self.row = width // 8
        self.drive_ms = drive_ms      # draw pass: short so blacks stay dark
        self.clear_ms = clear_ms      # clear pass: longer to fully wipe ghosts
        self.rst = Pin(RST_PIN, Pin.OUT)
        self.dc = Pin(DC_PIN, Pin.OUT)
        self.cs = Pin(CS_PIN, Pin.OUT)
        self.busy = Pin(BUSY_PIN, Pin.IN)
        self.spi = SoftSPI(baudrate=4_000_000, polarity=0, phase=0,
                           sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(28))
        # portrait, 1 bit per pixel, 1 = white
        self.buf = bytearray(b'\xff' * (self.row * height))
        self.fb = framebuf.FrameBuffer(self.buf, width, height, framebuf.MONO_HLSB)

    def _cmd(self, c, *dat):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytearray([c]))
        self.cs(1)
        for d in dat:
            self.cs(1); self.dc(1); self.cs(0)
            self.spi.write(bytearray([d]))
            self.cs(1)

    def _data(self, buf):
        # one CS window per byte - required by this controller
        self.dc(1)
        w = self.spi.write
        cs = self.cs
        b = bytearray(1)
        for v in buf:
            b[0] = v
            cs(1); cs(0)
            w(b)
        cs(1)

    def reset(self):
        self.rst(1); utime.sleep_ms(20)
        self.rst(0); utime.sleep_ms(20)
        self.rst(1); utime.sleep_ms(20)

    def _init_panel(self):
        self.reset()
        self._cmd(0x01, 0x03, 0x00, 0x2B, 0x2B, 0x03)   # power setting
        self._cmd(0x06, 0x17, 0x17, 0x17)               # booster soft start
        self._cmd(0x00, 0xBF if self.width <= 128 else 0xFF)  # PSR: reg LUT + res
        self._cmd(0x30, 0x3A)                           # PLL
        self._cmd(0x61, self.width, (self.height >> 8) & 0xFF, self.height & 0xFF)
        self._cmd(0x82, 0x08)                           # VCOM DC
        self._cmd(0x50, 0x97)                           # CDI
        # host-supplied waveform: constant-drive phases per level byte. These
        # values + drive_ms are tuned together so the TIMED stop lands right
        # when the panel is fully dark; changing the black phase length shifts
        # that stop point (too long -> waveform loops past dark into gray).
        self._cmd(0x20); self._data(bytes([0x01]) * 22)     # VCOM
        self._cmd(0x21); self._data(bytes([0x0A]) * 20)     # to white
        self._cmd(0x22); self._data(bytes([0x0A]) * 20)
        self._cmd(0x23); self._data(bytes([0x05]) * 20)     # to black
        self._cmd(0x24); self._data(bytes([0x05]) * 20)
        self._cmd(0x04)                                 # power on
        utime.sleep_ms(200)

    def _refresh(self, old, new, dms):
        """One timed refresh driving pixels from `old` state to `new` state."""
        self._init_panel()
        self._cmd(0x10); self._data(old)
        self._cmd(0x11); self._cmd(0x92)                # commit plane
        self._cmd(0x13); self._data(new)
        self._cmd(0x11); self._cmd(0x92)
        self._cmd(0x12)                                 # start refresh
        utime.sleep_ms(dms)                             # waveform loops: timed stop
        self.reset()
        self._cmd(0x02)                                 # power off
        utime.sleep_ms(100)

    def display(self, buf=None):
        """Push a full portrait frame (1bpp, 1=white). Two passes: a longer
        clear-to-white (clear_ms) to fully wipe the previous image, then a
        short white->target (drive_ms) that drives blacks fully dark - both
        tuned on the panel (longer draw over-drives blacks back to gray)."""
        if buf is None:
            buf = self.buf
        n = self.row * self.height
        white = bytes([0xFF]) * n
        black = bytes([0x00]) * n
        self._refresh(black, white, self.clear_ms)      # clear to white
        self._refresh(white, buf, self.drive_ms)        # draw target
