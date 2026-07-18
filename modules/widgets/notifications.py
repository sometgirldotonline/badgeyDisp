import io, os, dbus, traceback

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gtk, Gio
import cairosvg
from PIL import Image, ImageDraw
import fonts, threading,datetime
from time import sleep
import state
from pathlib import Path
import __main__
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
past_icons = []
found_regular = None
found_symbolic = None
def resolve_icon(icon_str="preferences-desktop-notification-symbolic"):
    global found_symbolic, found_regular
    if not icon_str:
        icon_str="preferences-desktop-notification-symbolic"
    if os.path.exists(icon_str):
        path = icon_str
        found_symbolic = path
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
        icon_themes = []
        for dir in icon_dirs:
            if not os.path.isdir(dir):
                continue
            for subdir in [f.resolve() for f in Path(dir).iterdir() if f.is_dir()]:
                icon_themes.append(subdir)
        # Sort: user theme first, then dark variants, then everything else
        def theme_sort_key(p):
            name = p.parts[-1]
            is_user = name.startswith(theme_name)
            is_dark = "dark" in name.lower()
            return (not is_user, not is_dark, name)
        icon_themes.sort(key=theme_sort_key)
        found_regular = None
        found_symbolic = None
        for theme_path in icon_themes:
                theme_path = str(theme_path)
                if not os.path.isdir(theme_path):
                    continue

                for root,_,files in os.walk(theme_path):
                    for file in files:
                        if not found_regular and file.endswith(".png") and not file.endswith(".svg") and icon_str in file:
                            found_regular = os.path.join(root,file)

                        if not found_symbolic and icon_str in file and ("symbolic" in file or file.endswith(".svg")):
                            found_symbolic = os.path.join(root,file)
                            return found_symbolic
            # if found_regular or found_symbolic:
                # return found_regular, found_symbolic
    try:  
        print(found_symbolic)
        print(f"[notifications/icons] resolved {icon_str} as symbolic to {found_symbolic}")
        return found_symbolic
    except:
        print(f"[notifications/icons] resolved {icon_str} as regular to {found_regular}")
        return found_regular

def render_notif(icon=Image.new("L", (16,16),255), app="Unknown", title="Unset title", body="No body provided"):
    global fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 0)
    now = datetime.datetime.now().strftime("%H:%M")
    ImageDraw.Draw(fbuf).text((10,10), now, font=fonts.MainFont, fill=255, anchor="lt")
    clocklen = round(ImageDraw.Draw(fbuf).textlength(now, font=fonts.MainFont))
    fbuf.paste(icon.resize((16,16)),(10+clocklen+5,8))
    ImageDraw.Draw(fbuf).text((10+clocklen+10+16,5),app, fill=255,font=fonts.MainFont, align="lm")
    ImageDraw.Draw(fbuf).text((10,30),title, fill=255,font=fonts.NotifTitle, align="lm")
    ImageDraw.Draw(fbuf).text((10,52),body, fill=255,font=fonts.MainFont, align="left")
    # notifIcon = Image.open("notification_icon.png").convert("L").resize((16,16))
def render_statusbar(icons=[]):
    global fbuf
    if len(icons) == 0:
        return
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    icc = len(icons)
    width = (16 * icc) + (10 * (icc + 1))
    ImageDraw.Draw(fbuf).rounded_rectangle(
        xy=(0, 0, width, 32),
        radius=11,
        fill=0,  # Changed from 0 to visible white (or use 255 for grayscale)
        width=0,
        corners=[False, False, True, False]
    )
    idx = 0
    for i in past_icons:
        fbuf.paste(i.resize((16,16)),(
            (16*idx) + (10*(idx+1))
            ,10))
        idx +=1;
def init():
    global fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)

waiting_notif = None

def clear_notif():
    global waiting_notif
    sleep(20)
    state.FULLSCREEN_VIEW = False
    waiting_notif = None
    __main__.send_frame()

def fb():
    global waiting_notif, fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    if waiting_notif == None:
        # print("[notifications] rendering statusbar")
        render_statusbar(past_icons)
    else:
        render_notif(waiting_notif["icon"],waiting_notif["app"],waiting_notif["title"],waiting_notif["body"])
        threading.Thread(target=clear_notif).start()
    return fbuf

def msg_filter(bus, message):
    global waiting_notif, past_icons
    if message.get_interface() != "org.freedesktop.Notifications" or message.get_member() !="Notify":
        return
    try:
        app_name = "DefaultApp"
        icon = resolve_icon("preferences-desktop-notification-symbolic")
        title = "Untitled"
        body = "No body."
        hints = {}
        args = message.get_args_list()
        length = len(args)
        if length > 0: app_name = args[0]
        if length > 2: icon = resolve_icon(args[2].replace("file://",""))
        if icon == None:
            icon = resolve_icon("preferences-desktop-notification-symbolic")
        if length > 3: title = args[3]
        if length > 4: body = args[4]
        if length > 6: hints = args[6]
        if "desktop-entry" in hints:
            print(hints["desktop-entry"])
            if icon == None or "preferences-desktop-notification-symbolic" in icon:
                deIcon = resolve_icon(hints["desktop-entry"])
                if deIcon != None:
                    icon = deIcon
        print(f"""[notifications] Notification from {app_name}\n
Icon -> {str(icon)[:100]}
Title -> {title}
Body -> {body}
Hints -> {str(hints)[:100]}
""")    
        iconimage = Image.new("L", (16,16),255)
        try:
            if icon.lower().endswith('.svg'):
                png_bytes = cairosvg.svg2png(url=icon)
                iconimage = Image.open(io.BytesIO(png_bytes))
            else:
                iconimage = Image.open(icon)
        except Exception as e:
            traceback.print_exc()
            iconimage = Image.new("L", (16,16),0)
        waiting_notif = {"icon":iconimage,"app":app_name,"title":title,"body":body.replace("\n\n","\n")}
        state.FULLSCREEN_VIEW = True
        past_icons.insert(0,iconimage)
        if len(past_icons) > 5:
            past_icons = past_icons[:5]
        __main__.send_frame()
    except Exception as e:
        print(f"[notifications] Error parsing message contents: {e}")
        traceback.print_exc()
DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus()
session_bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
session_bus.add_message_filter(msg_filter)
thread = threading.Thread(target=GLib.MainLoop().run)
thread.start()
print(f"[notifications] started listener thread")