import json, sys
try:
    with open('settings.json', 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"[settings] error in loading settings.json: {e}")
    print(f"[settings] check if settings.json exists in workdir")
    print(f"[settings] you can make it an empty json object if you just want defaults, have a poke at the weather coords :3")
    sys.exit()
# width of display
PANEL_W = None
# height display
PANEL_H = None
# latitude
WTTR_LAT = None
# longitude
WTTR_LONG = None
# timeout of notifications
NOTIF_TIMEOUT = None
# not a setting just shared state
FULLSCREEN_VIEW = False
for key, value in data.items():
    globals()[key] = value

if PANEL_W is None:
    PANEL_W = 296
    print("[settings] you didn't specify a panel width (PANEL_W)! defaulting to 296")
if PANEL_H is None:
    PANEL_H = 152
    print("[settings] you didn't specify a panel height (PANEL_H)! defaulting to 152")
if WTTR_LAT is None:
    WTTR_LAT = 39.04626858581778
    print(f"[settings] you didn't specify a latitude for the weather (WTTR_LAT)! defaulting to {WTTR_LAT}")
if WTTR_LONG is None:
    WTTR_LONG = 125.78380837890835
    print(f"[settings] you didn't specify a longitude for the weather (WTTR_LONG)! defaulting to {WTTR_LONG}")
if NOTIF_TIMEOUT is None:
    NOTIF_TIMEOUT = 20
    print("[settings] you didn't specify a notification timeout (NOTIF_TIMEOUT)! defaulting to 20")
