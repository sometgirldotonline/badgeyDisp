from PIL import Image
import state
fb = Image.new("L", (state.PANEL_W, state.PANEL_H), 255)
frames = []

def init():
    global fb, frames
    fb = Image.new("L", (state.PANEL_W, state.PANEL_H), 255)
    frames = []

def add_frame(frameref):
    global fb, frames
    frames.append(frameref)

def del_frame(frameref):
    global fb, frames
    try:
        frames.remove(frameref)
    except Exception as e:
        print(f"[compositor] maybe put the frame there first??? {e}")

def move_frame_to_layer(frameref, idx):
    global fb, frames
    try:
        frames.remove(frameref)
        frames.insert(idx, frameref)
    except Exception as e:
        print(f"[compositor] maybe put the frame there first??? {e}")

def move_frame_by(frameref, adj):
    global fb, frames
    try:
        current_pos = frames.index(frameref)
        frames.remove(frameref)
        frames.insert(current_pos+adj, frameref)
    except Exception as e:
        print(f"[compositor] maybe put the frame there first??? {e}")

def render():
    global fb, frames
    for frame in frames:
        fb.paste(frame,(0,0),mask=frame.point(lambda p: 0 if p == 220 else 255))