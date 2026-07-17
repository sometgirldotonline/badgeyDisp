import io, os, dbus

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gtk, GdkPixbuf, Gio
from PIL import Image, ImageDraw
import fonts
from state import PANEL_H, PANEL_W
# presume these sizes
PANEL_W, PANEL_H = 296, 152
fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)
timeout = 0
def resolve_icon(icon_str):
    if not icon_str:
        return None
    if os.path.isabs(icon_str) and os.path.exists(icon_str):
        path = icon_str
    else: 
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            theme_name = settings.get_string("icon-theme")
        except Exception as e:
            print(f"(!) [notifications/icons] error picking icon theme: {e}")
            theme_name = "hicolor"
        print(f"[notifications/icons] using icon theme: {theme_name}")
        icon_dirs = [
            os.path.expanduser("~/.local/share/icons"),
            os.path.expanduser("~/.icons"),
            "/usr/share/icons"
        ]

        regular_icons = [f"{icon_str}.png",f"{icon_str}.svg"]
        symbolic_icons = [f"{icon_str}-symbolic.symbolic.png", f"{icon_str}-symbolic.svg", f"{icon_str}-symbolic.png"]
        found_regular = None
        found_symbolic = None
        for theme in [theme_name+"-Dark",theme_name+"-dark",theme_name, "hicolor"]:
            for base_dir in icon_dirs:
                theme_path = os.path.join(base_dir, theme)
                if not os.path.isdir(theme_path):
                    continue

                for root,_,files in os.walk(theme_path):
                    for file in files:
                        if not found_regular and file in regular_icons:
                            found_regular = os.path.join(root,file)
                        
                        if not found_symbolic and file in symbolic_icons:
                            found_symbolic = os.path.join(root,file)
                        
            # if found_regular or found_symbolic:
                # return found_regular, found_symbolic
            
    if found_symbolic:
        print(f"[notifications/icons] resolved {icon_str} as symbolic to {found_symbolic}")
        return found_symbolic
    else:
        print(f"[notifications/icons] resolved {icon_str} as regular to {found_regular}")
        return found_regular


def render_notif(icon=Image.new("L", (16,16),255), app="Unknown", title="Unset title", body="No body provided"):
    global fbuf
    fbuf = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(fbuf).text((54,28),"No Notifications", fill=255,font=fonts.MainFont, align="lm")
    ImageDraw.Draw(fbuf).text((32,55),"No Notifications", fill=255,font=fonts.NotifTitle, align="lm")
    ImageDraw.Draw(fbuf).text((32,85),"No Notifications", fill=255,font=fonts.MainFont, align="lm")
    # notifIcon = Image.open("notification_icon.png").convert("L").resize((16,16))
    fbuf.paste(icon,(32,32))
def render_statusbar(icons=[]):
    global fbuf
    fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)
    icc = 5
    width = (16 * icc) + (10 * (icc + 1))
    ImageDraw.Draw(fbuf).rounded_rectangle(
        xy=(0, 0, width, 32),
        radius=11,
        fill=0,  # Changed from 0 to visible white (or use 255 for grayscale)
        width=0,
        corners=[False, False, True, False]
    )
    notifIcon = Image.new("L", (16,16),255)
    for i in range(0,5):
        fbuf.paste(notifIcon,(
            (16*i) + (10*(i+1))
            ,10))

def init():
    global fbuf
    fbuf = Image.new("L", (PANEL_W, PANEL_H), 220)


def fb():
    global timeout
    timeout -= 1
    if timeout == -2:
        timeout = 5
    if timeout < 1:
        render_statusbar([])
    else:
        render_notif()
    return fbuf