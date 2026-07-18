import sys
from pathlib import Path

def resource(rel):
    if getattr(sys, "frozen", False):
        print(str(Path(sys._MEIPATH)/rel))
        return str(Path(sys._MEIPATH)/rel)
    print(str(Path(__file__).resolve().parent / rel))
    return str(Path(__file__).resolve().parent / rel)