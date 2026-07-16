from PIL import Image, ImageDraw, ImageFont
import numpy as np
def unpack_portrait(packed: bytes, pw: int = 152, ph: int = 296) -> Image.Image:
    """Unpack portrait packed bytes back to a landscape image for preview."""
    arr = np.frombuffer(packed, dtype=np.uint8).reshape(ph, pw // 8)
    portrait = np.unpackbits(arr, axis=1, bitorder="big")  # shape (ph, pw) = (296, 152)
    # Reverse pack_portrait: portrait[y, x] = landscape[151-x, y]
    # So landscape[x, y] = portrait[y, 151-x] = portrait.T[x, y] flipped on axis 0
    landscape = np.flipud(portrait.T)  # shape (152, 296) -> (296, 152) landscape
    return Image.fromarray((landscape * 255).astype(np.uint8), mode="L")

class BadgePreview:
    """Preview window for dev."""

    def __init__(self, pw: int = 152, ph: int = 296, scale: int = 3):
        import tkinter as tk

        self.pw, self.ph, self.scale = pw, ph, scale
        self.root = tk.Tk()
        self.root.title("badge preview")
        self.label = tk.Label(self.root, bg="#888")
        self.label.pack()
        self._photo = None  # tkinter drops the image if nothing keeps a reference

    def show(self, packed: bytes):
        from PIL import ImageTk

        img = unpack_portrait(packed, self.pw, self.ph)
        w, h = img.size  # landscape dimensions after unpack
        img = img.resize((w * self.scale, h * self.scale), Image.NEAREST)
        self._photo = ImageTk.PhotoImage(img)
        self.label.configure(image=self._photo)
        self.root.update()  # pump the event loop without blocking - call this per-frame

    def run(self, tick_fn, interval_ms: int = 1000):
        """Call tick_fn() -> packed bytes on a timer and preview each result -
        handy for watching a clock face update live while you tweak layout."""
        def _step():
            self.show(tick_fn())
            self.root.after(interval_ms, _step)
        _step()
        self.root.mainloop()
