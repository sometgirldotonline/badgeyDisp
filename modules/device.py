# code borrowed from https://github.com/notaroomba/badge-paint/blob/main/tools/send_frame.py
import struct
import sys
import time

import serial  # pip install pyserial
def test_pattern(PW, PH):
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

