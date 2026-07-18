from PIL import Image
# , ImageDraw, ImageFont, ImageColor,ImageText
import numpy as np
from modules import preview
from modules import device
from modules.widgets import media 
from modules.widgets import notifications
from modules.widgets import clock
from modules.widgets import weather
# PANEL_W, PANEL_H = 296, 152
import state
from time import sleep, time
import os, traceback
# import fonts
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

def build_frame() -> bytes:
    compositor.init()
    compositor.add_frame(clock.fb())
    compositor.add_frame(notifications.fb())
    compositor.add_frame(weather.fb())
    compositor.add_frame(media.fb())
    compositor.render()
    bw = compositor.fb.convert("1", dither=Image.NONE)
    return pack_portrait(bw)
media.init()
notifications.init()
clock.init()

def send_frame():
        try:
            if os.getenv("badgey_mode","badge") == "badge":    
                device.send(build_frame(), PW=state.PANEL_H, PH=state.PANEL_W)  # portrait dims in header
            elif os.getenv("badgey_mode", "badge") == "preview":
                preview.show(build_frame())
        except Exception as e:
            print(f"[main] exception caught when sending frame: {e}")
            traceback.print_exc()
if os.getenv("badgey_mode", "badge") == "preview":
    print(f"[preview] writing to {preview.get_path()}")
    print(f"[preview] try: feh --reload 1 {preview.get_path()}")
if os.getenv("badgey_mode", "badge") not in ["badge","preview"]:
    print(f"[main] mode {os.getenv("badgey_mode", "????")} is unknown, expects one of badge or preview")
    exit()
while run:
    send_frame()
    now = time()
    next_minute = (int(now) // 60 + 1) * 60
    sleep(next_minute - now)

