from PIL import Image, ImageDraw,ImageOps
import __main__
import fonts, state, threading,time
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)

def fb():
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    fgc = 255
    bgc = 0
    if state.FULLSCREEN_VIEW:
        fgc = 0
        bgc = 255
    text = "FEMTANYL - Katamari"
    prepad= 11+16
    width = prepad+ImageDraw.Draw(fbuf).textlength(text,font=fonts.MainFont)+11
    if state.FULLSCREEN_VIEW:
        width = prepad+11
    x1 = state.PANEL_W/2 - width/2
    if state.FULLSCREEN_VIEW:
        x1 = state.PANEL_W - width
    y1 = state.PANEL_H - 32
    x2 = x1 + width
    y2 = state.PANEL_H
    ImageDraw.Draw(fbuf).rounded_rectangle(xy=(x1, y1, x2, y2), radius=11, fill=bgc,corners=[True,True,False,False] if not state.FULLSCREEN_VIEW else [True,False,False,False])

    if not state.FULLSCREEN_VIEW:
        ImageDraw.Draw(fbuf).text(((state.PANEL_W-width)/2+(prepad), state.PANEL_H - 16), text, font=fonts.MainFont, fill=fgc, anchor="lm")
    if state.FULLSCREEN_VIEW:
        fbuf.paste((Image.open("media_icons/play.png").resize((16,16))),(int(x1+11),int(state.PANEL_H-24)))
    else:
        fbuf.paste(ImageOps.invert(Image.open("media_icons/play.png").resize((16,16))),(int(x1+11),int(state.PANEL_H-24)))
    return fbuf