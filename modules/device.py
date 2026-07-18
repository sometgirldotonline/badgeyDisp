# code borrowed from https://github.com/notaroomba/badge-paint/blob/main/tools/send_frame.py
import struct
import sys
import time
frame_in_flight = False
import serial  # pip install pyserial
def test_pattern(PW=296, PH=152):
    row = PW // 8
    frame = bytearray(b"\xff" * (row * PH))

    def black(x, y):
        frame[y * row + (x >> 3)] &= ~(0x80 >> (x & 7))

    for y in range(PH):
        for x in range(PW):
            border = x < 4 or x >= PW - 4 or y < 4 or y >= PH - 4
            vline = PW // 2 - 2 <= x < PW // 2 + 2
            hline = PH // 2 - 2 <= y < PH // 2 + 2
            box = PW // 2 - 30 <= x < PW // 2 + 30 and PH // 2 - 40 <= y < PH // 2 + 40
            if border or vline or hline or box:
                black(x, y)
    return bytes(frame)

def from_image(img_,PW=296, PH=152):
    from PIL import Image
    img = img_.convert("L").resize((PW, PH))
    img = img.point(lambda p: 255 if p > 127 else 0, mode="1")
    return img.tobytes()

def send(frame=test_pattern(152, 296), portname="/dev/ttyACM0", PW=152, PH=296):
    global frame_in_flight
    if frame_in_flight:
        return
    frame_in_flight = True  # portrait dims
    with serial.Serial(portname, 115200, timeout=1) as port:
        packet = b"BPNT1" + struct.pack(">HH", PW, PH) + frame
        print(f"[device] sending {len(packet)} bytes to {portname}")
        port.write(packet)
        port.flush()
        deadline = time.time() + 45
        buf = b""
        while time.time() < deadline:
            buf += port.read(64)
            if b"OK" in buf:
                print("[device] frame printed OK!")
                frame_in_flight = False
                return
            if b"ERR" in buf:
                print("[device] badge got error!\n[device] error:", buf.decode(errors="replace"))
                frame_in_flight = False
                return
        print("[device] timed out waiting for understood response!\n[device] recieved:", buf.decode(errors="replace"))
        frame_in_flight = False
        