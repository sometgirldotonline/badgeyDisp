from PIL import Image, ImageDraw
import __main__
import fonts, state, requests, threading,time
fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
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
update_successful = True
def wttr_thread():
    global tmp, sky,last_refreshed,update_successful
    try:
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={state.WTTR_LAT}&longitude={state.WTTR_LONG}&current=temperature_2m,weather_code")
        rj = r.json()
        print(rj)
        tmp = f"{rj["current"]["temperature_2m"]}{rj["current_units"]["temperature_2m"]}"
        sky = dwd_weathercode[rj["current"]["weather_code"]]
        last_refreshed = time.time()
        update_successful = True
        __main__.send_frame()
    except Exception as e:
        print(f"[weather] error in updating weather: {e}, will try again in 7 minutes")
        last_refreshed = time.time()
        update_successful = False


def fb():
    global last_refreshed,fbuf
    fbuf = Image.new("L", (state.PANEL_W, state.PANEL_H), 220)
    if (time.time() - last_refreshed) >= 420 and update_successful:
        update_thread = threading.Thread(target=wttr_thread)
        update_thread.start()
        ltext = "Loading..."
        ImageDraw.Draw(fbuf).rounded_rectangle(xy=(state.PANEL_W-((ImageDraw.Draw(fbuf).textlength(ltext,font=fonts.MainFont))+20),0,state.PANEL_W,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,False,True])
        ImageDraw.Draw(fbuf).text((state.PANEL_W-10, 15), ltext, font=fonts.MainFont, fill=255, anchor="rm")
    else:
        tmp_w = ImageDraw.Draw(fbuf).textlength(tmp,font=fonts.MainFont)
        sky_w = ImageDraw.Draw(fbuf).textlength(sky,font=fonts.MainFont)
        circ = 8
        gap = 10
        ImageDraw.Draw(fbuf).rounded_rectangle(xy=(state.PANEL_W-(sky_w+tmp_w+circ*2+gap+gap),0,state.PANEL_W,32),radius=11,fill=0,outline=None,width=0,corners=[False,False,False,True])
        ImageDraw.Draw(fbuf).text((state.PANEL_W-10, 15), sky, font=fonts.MainFont, fill=255, anchor="rm")
        ImageDraw.Draw(fbuf).circle((state.PANEL_W-(sky_w+gap+circ)+1,15),circ/2,255)
        ImageDraw.Draw(fbuf).text((state.PANEL_W-(sky_w+gap+circ*2), 15), tmp, font=fonts.MainFont, fill=255, anchor="rm")

    return fbuf