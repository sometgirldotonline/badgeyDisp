from PIL import Image, ImageDraw, ImageFont, ImageColor,ImageText
import numpy as np
from modules import preview
from modules import device
from modules import device
from modules.widgets import notifications
from modules.widgets import clock
from modules.widgets import weather
# PANEL_W, PANEL_H = 296, 152
import state
from time import sleep
import os
import fonts
from modules import compositor
def pack_portrait(bw_landscape: Image.Image) -> bytes:
    arr = np.array(bw_landscape)
    land = arr > 0                       # True = white; robust to whatever dtype PIL gives back
    H, W = land.shape                    # H=LAND_H, W=LAND_W
    py, px = np.indices((W, H))          # portrait shape is (PH=W, PW=H)
    lx = py
    ly = H - 1 - px
    portrait = land[ly, lx]              # shape (PH, PW), True = white
    packed = np.packbits(portrait, axis=1, bitorder="big")
    return packed.tobytes()


def build_frame_bytes(payload: bytes, pw: int = state.PANEL_W, ph: int =  state.PANEL_H) -> bytes:
    header = b"BPNT1" + pw.to_bytes(2, "big") + ph.to_bytes(2, "big")
    return header + payload


run = True


def build_clock_frame() -> bytes:
    compositor.init()
    compositor.add_frame(clock.fb())
    compositor.add_frame(notifications.fb())
    compositor.add_frame(weather.fb())
    compositor.render()
    bw = compositor.fb.convert("1", dither=Image.NONE)
    return pack_portrait(bw)
notifications.init()
clock.init()

if os.getenv("badgey_mode","badge") == "badge":    
    while run:
        device.send(build_clock_frame(), PW=state.PANEL_H, PH=state.PANEL_W)  # portrait dims in header
        sleep(3)
elif os.getenv("badgey_mode", "badge") == "preview":
    preview.BadgePreview(scale=1).run(build_clock_frame, interval_ms=1000)
else:
    print(f"[main] mode {os.getenv("badgey_mode", "????")} is unknown, expects one of badge or preview")