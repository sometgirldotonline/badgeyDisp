import io, os, dbus
import datetime
from PIL import Image, ImageDraw
import fonts
import state
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
timeout = 0

def init():
    global fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)


def fb():
    global timeout, fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    now = datetime.datetime.now().strftime("%H:%M")
    ImageDraw.Draw(fbuf).text(((state.PANEL_W) / 2, state.PANEL_H / 2), now, font=fonts.ClockFont, fill=0, anchor="mm")
    return fbuf