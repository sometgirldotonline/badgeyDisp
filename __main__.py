from PIL import Image, ImageDraw, ImageFont
import numpy as np
from modules import preview
PANEL_W, PANEL_H = 296, 152


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






if __name__ == "__main__":
    import datetime

    font = ImageFont.truetype(
        "wdxllubrifonttc.ttf", 58
    )

    def build_clock_frame() -> bytes:
        img = Image.new("L", (PANEL_W, PANEL_H), 255)  # grayscale canvas, landscape, start white
        draw = ImageDraw.Draw(img)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        draw.text((PANEL_W / 2, PANEL_H / 2), now, font=font, fill=0, anchor="mm")

        bw = img.convert("1", dither=Image.NONE)
        return pack_portrait(bw)

    preview.BadgePreview(scale=3).run(build_clock_frame, interval_ms=1000)
