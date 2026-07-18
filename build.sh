#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install pyinstaller
pip install -r requirements.txt
set -e
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
pyinstaller \
  --onefile \
  --name myapp \
  --add-data "media_icons:media_icons" \
  --add-data "font.ttf:." \
  --collect-all numpy \
  --collect-all PIL \
  --collect-all cairosvg \
  --collect-all cairocffi \
  --collect-all dbus \
  --collect-all gi \
  --hidden-import=dbus.mainloop.glib \
  --hidden-import=gi.repository.GLib \
  --hidden-import=gi.repository.Gio \
  --hidden-import=serial.tools.list_ports \
  --collect-submodules serial \
  --collect-submodules modules \
  __main__.py

echo "Build complete: dist/badgeydisp"