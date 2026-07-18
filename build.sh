#!/bin/bash
sudo apt install python3-dev libdbus-1-dev libdbus-glib-1-dev libgirepository1.0-dev libcairo2-dev pkg-config libgirepository-2.0-dev -y
sudo apt install python3.13-venv -y

python3 -m venv venv
source venv/bin/activate
pip install pyinstaller --break-system-packages
pip install -r requirements.txt --break-system-packages

set -e
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
pyinstaller \
  --onefile \
  --name badgeydisp \
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
  --collect-all requests \
  __main__.py

echo "Build complete: dist/badgeydisp"
