from PIL import Image, ImageDraw, ImageFont, ImageColor,ImageText
import numpy as np
from modules import preview
from modules import device
from modules import notifications
# PANEL_W, PANEL_H = 296, 152
import state
from time import sleep
import os
from fonts import fonts
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


def build_frame_bytes(payload: bytes, pw: int = PANEL_W, ph: int = PANEL_H) -> bytes:
    header = b"BPNT1" + pw.to_bytes(2, "big") + ph.to_bytes(2, "big")
    return header + payload


run = True

if __name__ == "__main__":
    import datetime


    def build_clock_frame() -> bytes:
        notifications.update()
        img = Image.new("L", (PANEL_W, PANEL_H), 255)  # grayscale canvas, landscape, start white
        draw = ImageDraw.Draw(img)
        if notifications.timeout < 1:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            draw.text((PANEL_W / 2, PANEL_H / 2), now, font=fonts.ClockFont, fill=0, anchor="mm")
            draw.rounded_rectangle(xy=(0,0,80,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,True,False])
            draw.rounded_rectangle(xy=(PANEL_W-((draw.textlength("21°c • Cloudy",font=fonts.MainFont))+20),0,PANEL_W,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,False,True])
            draw.text((PANEL_W-10, 15), "21°c • Cloudy", font=fonts.MainFont, fill=255, anchor="rm")
            draw.text((PANEL_W-10, PANEL_H-15), str(notifications.timeout), font=fonts.MainFont, fill=0, anchor="rm")

        else:  
            img = notifications.fb.copy()
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle(xy=(PANEL_W-((draw.textlength("21°c",font=fonts.MainFont))+20),0,PANEL_W,32),radius=11,fill=255,outline=None,width=0,corners=[False,False,False,True])
            draw.text((PANEL_W-10, 15), "21°c", font=fonts.MainFont, fill=1, anchor="rm")
            draw.text((PANEL_W-10, PANEL_H-15), str(notifications.timeout), font=fonts.MainFont, fill=255, anchor="rm")
            now = datetime.datetime.now().strftime("%H:%M:%S")
            draw.text(((PANEL_W-(18+15)) - draw.textlength( "21°c",font=fonts.MainFont), 15), now, font=fonts.MainFont, fill=255, anchor="rm")
        bw = img.convert("1", dither=Image.NONE)
        return pack_portrait(bw)
    notifications.init(PANEL_W,PANEL_H)
    if os.getenv("badgey_mode","badge") == "badge":    
        while run:
            device.send(build_clock_frame(), PW=PANEL_H, PH=PANEL_W)  # portrait dims in header
            sleep(3)
    elif os.getenv("badgey_mode", "badge") == "preview":
        preview.BadgePreview(scale=3).run(build_clock_frame, interval_ms=1000)
    else:
        print(f"[main] mode {os.getenv("badgey_mode", "????")} is unknown, expects one of badge or preview")