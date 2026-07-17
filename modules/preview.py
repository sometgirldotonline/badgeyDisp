from PIL import Image
import numpy as np
import tempfile, os

_preview_path = os.path.join(tempfile.gettempdir(), "badgey_preview.png")

def unpack_portrait(packed: bytes, pw: int = 152, ph: int = 296) -> Image.Image:
    arr = np.frombuffer(packed, dtype=np.uint8).reshape(ph, pw // 8)
    portrait = np.unpackbits(arr, axis=1, bitorder="big")
    landscape = np.flipud(portrait.T)
    return Image.fromarray((landscape * 255).astype(np.uint8), mode="L")

def show(packed: bytes, scale: int = 1):
    img = unpack_portrait(packed)
    if scale != 1:
        w, h = img.size
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    img.save(_preview_path)

def get_path():
    return _preview_path
