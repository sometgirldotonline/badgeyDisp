import io, os, dbus
import datetime
from PIL import Image, ImageDraw
import fonts
from state import PANEL_H, PANEL_W
# presume these sizes
PANEL_W, PANEL_H = 296, 152
fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)
timeout = 0

def init():
    global fbuf
    fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)


def fb():
    global timeout, fbuf
    fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)
    now = datetime.datetime.now().strftime("%H:%M")
    ImageDraw.Draw(fbuf).text((PANEL_W / 2, PANEL_H / 2), now, font=fonts.ClockFont, fill=0, anchor="mm")
    return fbuf