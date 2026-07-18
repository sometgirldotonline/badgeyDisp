from PIL import Image, ImageDraw,ImageOps
import __main__,math
import fonts, state, threading,time,subprocess
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
media_string = "Nothing playing"
mstate = False
def fitter(string, mlen=32, sep=" - "):
    if len(string) < 2:
        song = string[0],
        artist = "Not Provided"
    else:
        song, artist = string[0], string[1]
    budget = mlen - len(sep)

    if len(song) + len(sep) + len(artist) <= mlen:
        return f"{song}{sep}{artist}"

    song_mfloor = max(1, min(math.floor(len(song) * 0.4), math.floor(mlen * 0.45)))
    art_mfloor = max(1, min(math.floor(len(artist) * 0.4), math.floor(mlen * 0.45)))

    total_len = len(song) + len(artist)
    song_share = budget * len(song) / total_len
    artist_share = budget * len(artist) / total_len

    song_alloc = max(song_share, song_mfloor)
    artist_alloc = max(artist_share, art_mfloor)

    if len(song) < song_alloc:
        surplus = song_alloc - len(song)
        song_alloc = len(song)
        artist_alloc += surplus
    if len(artist) < artist_alloc:
        surplus = artist_alloc - len(artist)
        artist_alloc = len(artist)
        song_alloc += surplus

    song_alloc, artist_alloc = math.floor(song_alloc), math.floor(artist_alloc)

    overflow = (song_alloc + artist_alloc) - budget
    if overflow > 0:
        song_slack = song_alloc - song_mfloor
        artist_slack = artist_alloc - art_mfloor
        total_slack = max(song_slack + artist_slack, 1)
        song_cut = math.floor(overflow * song_slack / total_slack)
        artist_cut = overflow - song_cut
        song_alloc = max(song_mfloor, song_alloc - song_cut)
        artist_alloc = max(art_mfloor, artist_alloc - artist_cut)

    def truncate(text, alloc):
        if len(text) <= alloc:
            return text
        if alloc <= 1:
            return text[:alloc]
        return text[:alloc - 1].rstrip() + "…"

    return f"{truncate(song, song_alloc)}{sep}{truncate(artist, artist_alloc)}"

def tracker_thread2():
    global media_string,mstate
    proc = subprocess.Popen(
        ["playerctl", "metadata", "-F", '-f', '{{xesam:title}}⸻{{xesam:artist}}'],
        stdout=subprocess.PIPE,
        text=True
    )
    for line in proc.stdout:
        line = line.strip().split("⸻")
        stateproc = subprocess.run(['playerctl', 'status'], capture_output=True, text=True)
        print(stateproc.stdout)
        if "Playing" in stateproc.stdout.strip():
            media_string = line
            mstate = True
            __main__.send_frame()
        else:
            mstate = False
            __main__.send_frame()
def tracker_thread1():
    global media_string,mstate
    proc = subprocess.Popen(
        ["playerctl", "status", "-F"],
        stdout=subprocess.PIPE,
        text=True
    )
    for line in proc.stdout:
        if "Playing" in line.strip():
            metaproc = subprocess.run(['playerctl', 'metadata', '-f', '{{xesam:title}}⸻{{xesam:artist}}'], capture_output=True, text=True)
            media_string = metaproc.stdout.strip().split("⸻")
            mstate = True
            __main__.send_frame()
        else:
            mstate = False
            __main__.send_frame()

def init():
    threading.Thread(target=tracker_thread1).start()
    threading.Thread(target=tracker_thread2).start()
def fb():
    
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    fgc = 255
    bgc = 0
    if not mstate:
        return fbuf
    if state.FULLSCREEN_VIEW:
        fgc = 0
        bgc = 255
    prepad= 11+16
    print(media_string)
    if ", " in media_string[1]:
        media_string[1] = media_string[1].split(", ")[0]
    if " & " in media_string[1]:
        media_string[1] = media_string[1].split(" & ")[0]
    if "feat" in media_string[1]:
        media_string[1] = media_string[1].split("feat")[0].strip(" ,。")
    fitted = fitter(media_string,mlen=32,sep=" - ")

    if fitted is None:
        fitted = ""
    width = prepad+ImageDraw.Draw(fbuf).textlength(fitted,font=fonts.MainFont)+11
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
        ImageDraw.Draw(fbuf).text(((state.PANEL_W-width)/2+(prepad), state.PANEL_H - 16), fitted, font=fonts.MainFont, fill=fgc, anchor="lm")
    if state.FULLSCREEN_VIEW:
        fbuf.paste((Image.open("media_icons/play.png").resize((16,16))),(int(x1+11),int(state.PANEL_H-24)))
    else:
        fbuf.paste(ImageOps.invert(Image.open("media_icons/play.png").resize((16,16))),(int(x1+11),int(state.PANEL_H-24)))
    return fbuf