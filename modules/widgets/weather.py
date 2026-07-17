from PIL import Image, ImageDraw
import fonts, state, requests, threading,time
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_W), 220)
dwd_weathercode= {
    0: "Sunny",
    1: "Clear",
    2: "Cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Ice Rain",
    57: "Ice Rain",
    61: "Rain",
    63: "Rain",
    65: "Rain",
    66: "Ice Rain",
    67: "Ice Rain",
    71: "Snow",
    73: "Snow",
    75: "Snow",
    77: "Hail",
    80: "Rain",
    81: "Rain",
    82: "Storm",
    85: "Snow",
    86: "Snow",
    95: "Storm",
    96: "Storm",
    99: "Storm"
}
tmp = "Loading..."
sky = "Loading..."
last_refreshed = 0
def wttr_thread():
    global text
    r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={state.WTTR_LAT}&longitude={state.WTTR_LONG}&current=temperature_2m,weather_code")
    rj = r.json()
    print(rj)
    tmp = f"{rj["current"]["temperature_2m"]}{rj["current_units"]["temperature_2m"]}"
    sky = dwd_weathercode[rj["current"]["weather_code"]]

def fb():
    global text,last_refreshed,fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_W), 220)
    if (time.time() - last_refreshed) >= 420:
        update_thread = threading.Thread(target=wttr_thread)
        update_thread.start()
        last_refreshed = time.time()
        ltext = "Loading..."
        ImageDraw.Draw(fbuf).rounded_rectangle(xy=(state.PANEL_W-((ImageDraw.Draw(fbuf).textlength(ltext,font=fonts.MainFont))+20),0,state.PANEL_W,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,False,True])
        ImageDraw.Draw(fbuf).text((state.PANEL_W-10, 15), ltext, font=fonts.MainFont, fill=255, anchor="rm")
    else:
        tmp_w = ImageDraw.Draw(fbuf).textlength(tmp,font=fonts.MainFont)
        sky_w = ImageDraw.Draw(fbuf).textlength(sky,font=fonts.MainFont)
        circ = 16
        gap = 10
        ImageDraw.Draw(fbuf).rounded_rectangle(xy=(state.PANEL_W-(sky_w+tmp_w+circ+gap+gap),0,state.PANEL_W,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,False,True])
        ImageDraw.Draw(fbuf).text((state.PANEL_W-10, 15), sky, font=fonts.MainFont, fill=255, anchor="rm")
    return fbuf