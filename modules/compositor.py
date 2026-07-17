import io, os, dbus

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gtk, GdkPixbuf, Gio
from PIL import Image, ImageDraw
import state
fb = Image.new("L", (state.PANEL_W, state.PANEL_H), 255)
frames = []

def init():
    global fb, frames
    fb = Image.new("L", (state.PANEL_W, state.PANEL_H), 255)
    frames = []

def add_frame(frameref):
    global fb, frames
    frames.append(frameref)

def del_frame(frameref):
    global fb, frames
    frames.remove(frameref)

def move_frame_to_layer(frameref, idx):
    global fb, frames
    frames.remove(frameref)
    frames.insert(idx, frameref)

def move_frame_by(frameref, adj):
    global fb, frames
    current_pos = frames.index(frameref)
    frames.remove(frameref)
    frames.insert(current_pos+adj, frameref)

def render():
    global fb, frames
    for frame in frames:
        fb.paste(frame,(0,0),mask=frame.point(lambda p: 0 if p == 220 else 255))