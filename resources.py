import sys
from pathlib import Path

def resource(rel):
    if getattr(sys, "frozen", False):
        print(str(Path(sys._MEIPASS)/rel))
        return str(Path(sys._MEIPASS)/rel)
    print(str(Path(__file__).resolve().parent / rel))
    return str(Path(__file__).resolve().parent / rel)