import io, os, dbus

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gtk, GdkPixbuf, Gio
from PIL import Image, ImageDraw
from fonts import fonts
PANEL_W, PANEL_H = 296, 152
f = Image.new("L", (PANEL_W, PANEL_H), 0)
frames = []

def init(pnw,pnh):
    global fb
    PANEL_W, PANEL_H = pnw, pnh
    fb = Image.new("L", (PANEL_W, PANEL_H), 0)
    notifIcon = Image.new("L", (16,16),255)

def add_frame(frameref):
    frames.append(frameref)

def del_frame(frameref):
    frames.remove(frameref)

def move_frame_to_layer(frameref, idx):
    frames.remove(frameref)
    frames.insert(idx, frameref)

def move_frame_by(frameref, adj):
    current_pos = frames.index(frameref)
    frames.remove(frameref)
    frames.insert(current_pos+adj, frameref)

def render():
    for frame in frames:
        f.paste(frame,(0,0))
    return f