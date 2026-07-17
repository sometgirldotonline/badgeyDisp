# badge-paint firmware - shows the saved frame on boot, then listens on USB
# serial for new frames pushed from the badge-paint web app (WebSerial).
#
# Protocol (host -> badge):  b"BPNT1" + u16be width + u16be height + bitmap
#   bitmap: width*height/8 bytes, portrait orientation, MSB = leftmost pixel,
#   1 = white, 0 = black, row-major.
# Responses (badge -> host, line-oriented): "BPNT-READY", "DRAWING", "OK",
#   "ERR <reason>".
#
# Set PANEL_W to 152 for the 2.66" badges or 128 for the 2.9" badges.

import micropython
import select
import struct
import sys

import framebuf
import utime
from einkdriver import EPD

PANEL_W = 152
PANEL_H = 296
FRAME_FILE = "frame.bin"
MAGIC = b"BPNT1"

epd = EPD(PANEL_W, PANEL_H)


def placeholder():
    fb = epd.fb
    fb.fill(1)
    fb.rect(0, 0, PANEL_W, PANEL_H, 0)
    fb.rect(1, 1, PANEL_W - 2, PANEL_H - 2, 0)
    fb.text("badge", (PANEL_W - 40) // 2, PANEL_H // 2 - 12, 0)
    fb.text("paint", (PANEL_W - 40) // 2, PANEL_H // 2 + 4, 0)


def show_saved():
    # E-ink retains its image unpowered, so if a saved frame exists the panel
    # is already showing it - just load it into the buffer and skip the redraw.
    # On a FRESH badge (no saved frame) we deliberately do NOT draw a
    # placeholder: the app pushes a frame right after install, and a
    # placeholder refresh would just add an extra ~8s flash before it.
    try:
        with open(FRAME_FILE, "rb") as f:
            data = f.read()
        if len(data) == len(epd.buf):
            epd.buf[:] = data
    except OSError:
        pass


poller = select.poll()
poller.register(sys.stdin, select.POLLIN)


def read_exact(stream, n, timeout_ms=3000):
    """Read exactly n bytes, or None if the stream stalls for timeout_ms.
    The timeout is the resync mechanism: a broken/aborted transfer must
    never leave us blocked waiting for payload that will never arrive."""
    buf = bytearray(n)
    got = 0
    while got < n:
        if not poller.poll(timeout_ms):
            return None
        chunk = stream.read(1)
        if not chunk:
            return None
        buf[got] = chunk[0]
        got += 1
    return bytes(buf)


def receive_frame(stream):
    hdr = read_exact(stream, 4)
    if hdr is None:
        return "ERR header timeout"
    w, h = struct.unpack(">HH", hdr)
    if w % 8 or not (0 < w <= 256) or not (0 < h <= 512):
        return "ERR dims %dx%d" % (w, h)
    n = (w // 8) * h
    data = read_exact(stream, n, timeout_ms=5000)
    if data is None:
        return "ERR payload timeout"
    data = bytearray(data)
    if w == PANEL_W and h == PANEL_H:
        epd.buf[:] = data
    else:
        # different panel size selected in the app: centre it
        src = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
        epd.fb.fill(1)
        epd.fb.blit(src, (PANEL_W - w) // 2, (PANEL_H - h) // 2)
    try:
        with open(FRAME_FILE, "wb") as f:
            f.write(epd.buf)
    except OSError:
        pass  # flash full/readonly: still draw it
    print("DRAWING")
    epd.display()
    return "OK"


EXIT_MAGIC = b"BPNT-EXIT"


class _BreakOut(Exception):
    # raising SystemExit from main.py soft-reboots MicroPython (which
    # re-runs main.py) - ENDING main.py is what lands at the REPL
    pass


def serve():
    stream = sys.stdin.buffer
    # Binary frames legitimately contain 0x03 (Ctrl-C) and 0x04 (Ctrl-D).
    # MicroPython intercepts the interrupt char when the byte ARRIVES over
    # USB - long before our scanner reads it - so this must stay disabled
    # the whole time the app runs, or 0x03 raises KeyboardInterrupt and
    # the leftover 0x04 bytes soft-reboot the board at the REPL (the boot
    # loop). Firmware updates: send "BPNT-EXIT" over serial first.
    micropython.kbd_intr(-1)
    print("BPNT-READY %dx%d" % (PANEL_W, PANEL_H))
    m1 = 0   # frame magic progress
    m2 = 0   # exit magic progress
    while True:
        if not poller.poll(1000):
            continue
        b = stream.read(1)
        if not b:
            continue
        c = b[0]
        m1 = m1 + 1 if c == MAGIC[m1] else (1 if c == MAGIC[0] else 0)
        m2 = m2 + 1 if c == EXIT_MAGIC[m2] else (1 if c == EXIT_MAGIC[0] else 0)
        if m2 == len(EXIT_MAGIC):
            # escape hatch for firmware updates: drop to the REPL with
            # normal Ctrl-C handling so mpremote works again
            micropython.kbd_intr(3)
            print("BPNT-BYE")
            raise _BreakOut
        if m1 == len(MAGIC):
            m1 = m2 = 0
            print(receive_frame(stream))


show_saved()
while True:
    try:
        serve()
    except _BreakOut:
        break                     # BPNT-EXIT: fall off main.py -> REPL
    except BaseException as e:
        print("ERR crash: %r" % e)
        utime.sleep_ms(300)
