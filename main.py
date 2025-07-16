import requests
import configparser
import json
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image, ImageGrab
from atproto import Client, client_utils
from io import BytesIO
from pathlib import Path
from threading import *
import re
import dns.resolver
import time

# Variables
bskyBlue = "#1083fe"

brushSize = 4
eraseRange = 8
mouseBuffer = []
mouseBufferMaxSize = 5 # smoothness
prevLine = -1
LMBWasReleased = TRUE

# Import user facing strings from UI_Text.json (for multi language support)
appLang = "en"
with open('UI_Text.json', 'r', encoding="utf-8") as file:
    UIText = json.load(file)

# Bluesky setup
client = Client()
loggedIn = FALSE
postBtnBG = "#f1f3f5"
postBtnFG = "black"
pfpOriginal = Image.open("assets/notLoggedIn.png").resize((18, 18))
langs = ['en', 'ja']
config = configparser.ConfigParser(allow_no_value=True)


def onload():
    global langs, appLang, brushSize, eraseRange, mouseBufferMaxSize
    
    config.read("config.ini")
    configLang = clean_input(config["Misc"]["language"])

    if configLang != "":
        langs = [configLang]
        
        # Change app language if lang is set to a supported language
        if configLang == "ja":
            appLang = "ja"
            change_language()

    try:
        brushSize = int(clean_input(config["Canvas"]["brush_size"])) 
        brushSizeSlider.set(brushSize)
    except ValueError: 
        pass

    try:
        eraseRange = int(clean_input(config["Canvas"]["eraser_range"]))
        eraseRangeSlider.set(eraseRange)
    except ValueError: 
        pass

    try:
        mouseBufferMaxSize = int(clean_input(config["Canvas"]["stabilizer"]))
        stabilizerSlider.set(mouseBufferMaxSize)
    except ValueError: 
        pass

    login_thread(TRUE)
    


def login(skip_warning = False):
    global loggedIn, pfpOriginal, postBtnBG, postBtnFG, pfpTk, postButton

    # Get data from config.ini
    config.read("config.ini")
    handle = clean_input(config["Login"]["bsky_handle"])
    password = clean_input(config["Login"]["app_password"])
    
    try: 
        account = client.login(handle, password)
    except:
        if (not skip_warning):
            messagebox.showerror("Unable to log in", "SkyDraw couldn't log in to your Bluesky account :( \n\nMake sure the login info in the config file is correct and try again.")
    else:
        loggedIn = TRUE
        avatar = requests.get(account.avatar)
        pfpOriginal = Image.open(BytesIO(avatar.content)).resize((18, 18))
        pfpTk.paste(pfpOriginal)
        postButton["text"] = UIText[appLang]["post"]
        postButton["bg"] = bskyBlue
        postButton["fg"] = "white"

def login_thread(skip_warning = False):
    t1 = Thread(target=login, args=[skip_warning])
    t1.start()

# PIL canvas setup
canvasPath = Path("canvas/")
canvasPath.mkdir(exist_ok=True)
imgPath = "canvas/canvas.png"

# Update brush and eraser size
def update_size(event):
    global brushSize, eraseRange, mouseBufferMaxSize
    brushSize = int(brushSizeSlider.get())
    eraseRange = int(eraseRangeSlider.get())
    mouseBufferMaxSize = int(stabilizerSlider.get())

# Save canvas as PNG
def save_as_png():
    window.attributes("-topmost", True) #incase you have an always-on-top application running
    x = window.winfo_rootx() + canvas.winfo_x()
    y = window.winfo_rooty() + canvas.winfo_y()
    xx = x + canvas.winfo_width()
    yy = y + canvas.winfo_height()
    ImageGrab.grab(bbox=(x, y, xx, yy), all_screens=TRUE).save(imgPath)
    window.attributes("-topmost", False)

# Clear canvas
def clear_canvas():
    inRange = canvas.find_overlapping(0, 0, 512, 512)
    for stroke in inRange:
        if stroke not in tool_shapes:
            canvas.delete(stroke)

def resolve_handle(handle: str) -> str | None:
    #try DNS
    result = None

    try:
        answers = dns.resolver.resolve(f"_atproto.{handle}", "TXT")

        for answer in answers:
            txt = answer.to_text()
            if txt.startswith('"did='):
                result = txt[len('"did='):-1]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        pass

    #try wellknown http
    if result == None:
        try:
            response = requests.get(f"https://{handle}/.well-known/atproto-did", timeout=5.0)
            response.raise_for_status()
            result = response.text.strip()
        except (requests.ConnectionError, requests.HTTPError):
            pass

    return result

def clean_input(s):
    return s.strip().replace(u'\u202a',"").replace(u'\u202c',"")

hashtag_regex = re.compile(r'[#＃][^\s!@#$%^&*()=+./,\[{\]};:\'"?><]+') #should work universaly now
link_regex = re.compile(r'((http|https)://)(www.)?[a-zA-Z0-9@:%._\+~#?&//=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%._\+~#?&//=]*)')
#full urls only.

# Post to Bluesky
def post_to_bsky():
    save_as_png()

    if loggedIn:
        caption = clean_input(captionInput.get())
        alt_text = clean_input(altTextInput.get())

        #validate inputs
        if (len(caption) > 300):
            messagebox.showerror("Invalid caption length","Caption must be < 300 chars long. Currently it is: " + str(len(caption)))
            return
        
        if (len(alt_text) > 1000):
            messagebox.showerror("Invalid alt-text length","Alt-Text must be < 1000 chars long. Currently it is: " + str(len(alt_text)))
            return

        #build text
        postText = client_utils.TextBuilder()

        
        #https://stackoverflow.com/questions/6319551/whats-the-best-separator-delimiter-characters-for-a-plaintext-db-file 
        #the ␟ is an ascii unit seperator, it should never show up
        for text in caption.replace(" ","␟ ␟").replace("　","␟　␟").split("␟"):
            if re.fullmatch(hashtag_regex, text) != None:
                postText.tag(text, text[1:])
                continue

            if re.fullmatch(link_regex, text) != None:
                postText.link(text, text)
                continue

            if len(text) > 1 and text[0] == '@':
                did = resolve_handle(text[1:])
                if did == None:
                    messagebox.showerror("Invalid Handle","Attempting to tag a user that does not exist: " + text)
                    return
                
                postText.mention(text, did)
                continue
            
            postText.text(text)

        postText.text(" ")
        postText.tag("#SkyDraw", "SkyDraw")

        with open(imgPath, 'rb') as f:
            img_data = f.read()

        try:
            client.send_image(text=postText, image=img_data, image_alt=alt_text, langs=langs)
        except:
            messagebox.showerror("Unable to post", "Couldn't post for some reason???")
        else:
            captionInput.delete(0, END)
            altTextInput.delete(0, END)
            clear_canvas()
    
    else:
        #try to log-in again
        login_thread()

# Window setup
window = Tk()
window.title("SkyDraw")
window.minsize(512, 601)
window.iconbitmap("assets/icon.ico")

pfpTk = ImageTk.PhotoImage(pfpOriginal)

topSpace = Frame(width=512, height=512)
canvas = Canvas(topSpace, width=512, height=512, bg="white", highlightthickness=0)

row1 = Frame(window, width=512)
row2 = Frame(window, width=512)
row3 = Frame(window, width=512)

brushLabel = Label(row1, text=UIText["en"]["brush"])
brushSizeSlider = Scale(row1, from_=1, to=64, orient=HORIZONTAL, command=update_size)
eraserLabel = Label(row1, text=UIText["en"]["eraser"])
eraseRangeSlider = Scale(row1, from_=1, to=64, orient=HORIZONTAL, command=update_size)
stabilizerLabel = Label(row1, text="   Stabilizer: ")
stabilizerSlider = Scale(row1, from_=1, to=15, orient=HORIZONTAL, command=update_size, length=50)

captionLabel = Label(row2, text="Caption: ")
captionInput = Entry(row2)

altTextLabel = Label(row3, text="Alt-Text: ")
altTextInput = Entry(row3)
clearButton = Button(row3, text="Clear Canvas")
postButton = Button(row3, text="Log in ", image=pfpTk, compound="right", fg=postBtnFG, bg=postBtnBG, command=post_to_bsky)

# Place and pack elements
topSpace.pack(side=TOP, fill="both", expand=TRUE)
canvas.place(relx=0.5, rely=0.5, anchor="c")

row3.pack(side=BOTTOM, fill="x")
row2.pack(side=BOTTOM, fill="x")
row1.pack(side=BOTTOM, fill="x")

brushLabel.pack(side=LEFT)
brushSizeSlider.pack(side=LEFT, fill="x", expand=TRUE)
eraserLabel.pack(side=LEFT)
eraseRangeSlider.pack(side=LEFT, fill="x", expand=TRUE)
stabilizerLabel.pack(side=LEFT)
stabilizerSlider.pack(side=LEFT, fill="x", expand=TRUE)

captionLabel.pack(side=LEFT)
captionInput.pack(side=LEFT, fill="x", expand=TRUE)

altTextLabel.pack(side=LEFT)
altTextInput.pack(side=LEFT, fill="x", expand=TRUE)
postButton.pack(side=RIGHT)
clearButton.pack(side=RIGHT)

# Change language of labels and other UI elements
def change_language():
    brushLabel["text"] = UIText[appLang]["brush"]
    eraserLabel["text"] = UIText[appLang]["eraser"]
    stabilizerLabel["text"] = UIText[appLang]["stabilizer"]
    captionLabel["text"] = UIText[appLang]["caption"]
    altTextLabel["text"] = UIText[appLang]["alt-text"]
    clearButton["text"] = UIText[appLang]["clear canvas"]
    postButton["text"] = UIText[appLang]["login"]

# Set sliders to default values
brushSizeSlider.set(brushSize)
eraseRangeSlider.set(eraseRange)
stabilizerSlider.set(mouseBufferMaxSize)

eraser_border = canvas.create_rectangle(0,0,0,0,outline="#7F7F7F", state='hidden')
brush_border = canvas.create_oval(0,0,0,0,outline="#7F7F7F", state='hidden')
tool_shapes = [eraser_border, brush_border]

# Change post button color when hovering over it
def post_hover(event):
    if loggedIn:
        postButton["bg"] = "#0168d5"
def post_not_hover(event):
    if loggedIn:
        postButton["bg"] = bskyBlue
postButton.bind("<Enter>", post_hover)
postButton.bind("<Leave>", post_not_hover)

# Drawing on canvas
def sign(num):
    return -1 if num < 0 else 1

#if 3 points are on the same line.
def collinear(x1,y1,x2,y2,x3,y3):
    same_direction = sign(x1 - x2) == sign(x2 - x3) and sign(y1 - y2) == sign(y2 - y3)
    return (y3 - y2)*(x2 - x1) == (y2 - y1)*(x3 - x2) and same_direction

def draw_line():
    global LMBWasReleased, mouseBuffer, prevLine
    
    #get x, y averages
    x = 0
    y = 0

    for p in mouseBuffer:
        x += p[0]
        y += p[1]

    x /= len(mouseBuffer)
    y /= len(mouseBuffer)

    if LMBWasReleased: #there is no previous line, so just draw one
        prevLine = canvas.create_line(x, y, x, y, width=brushSize, fill=bskyBlue, capstyle="round", joinstyle="round")
    else:
        prevLineCoords = canvas.coords(prevLine)
        if collinear(*prevLineCoords[-4:],x,y): #if the previous line is colinear with the new point, u can just extend the previous line
            canvas.coords(prevLine,*(prevLineCoords[:-2]),x,y)
        else: #else make a new line
            canvas.coords(prevLine,*prevLineCoords,x,y)

    LMBWasReleased = FALSE
    
def draw(event):
    global mouseBuffer, mouseBufferMaxSize
    canvas.itemconfig(eraser_border, state='hidden')
    mouseBuffer.append([event.x, event.y])
    mouseBuffer = mouseBuffer[-mouseBufferMaxSize:]
    
    draw_line()

def LMB_released(event):
    global LMBWasReleased,mouseBuffer,mouseBufferMaxSize

    #draw in remaining lines
    if len(mouseBuffer) > 0:
        for i in range(len(mouseBuffer)-1):
            mouseBuffer.append([event.x, event.y])
            mouseBuffer = mouseBuffer[-mouseBufferMaxSize:]
            draw_line()

    mouseBuffer.clear()
    LMBWasReleased = TRUE

def pointInBox(ax,ay,x0,y0,x1,y1):
    return (x0 <= ax <= x1) and (y0 <= ay <= y1)

def boxIntersection(x_in,y_in,x_out,y_out,x0,y0,x1,y1):
    #no idea if this is good or not
    #assuming one point is inside the rectangle and the other is outside
    #return the point of intersection

    if (x_in != x_out):
        slope = (y_out - y_in) / (x_out - x_in)
        intercept = y_in - x_in * slope

        if x_out >= x1:
            d = x1 * slope + intercept
            if y0 <= d <= y1:
                return x1, d
        if x_out <= x0:
            d = x0 * slope + intercept
            if y0 <= d <= y1:
                return x0, d
        
        if (slope != 0):
            if y_out >= y1:
                d = (y1 - intercept) / slope
                if x0 <= d <= x1:
                    return d, y1
                
            if y_out <= y0:
                d = (y0 - intercept) / slope
                if x0 <= d <= x1:
                    return d, y0

    #line is veritcal
    if y_out >= y1:
        return x_out,y1
    
    if y_out <= y0:
        return x_out,y0
    
    return -1, -1 #error, should never happen

def aabb(ax_min, ay_min, ax_max, ay_max, bx_min, by_min, bx_max, by_max):  
    return (ax_min <= bx_max and ax_max >= bx_min) and (ay_min <= by_max and ay_max >= by_min) 

def erase(event):
    x = event.x
    y = event.y
    
    canvas.itemconfig(eraser_border, state='normal')

    eraseRect = [x-eraseRange, y-eraseRange, x+eraseRange, y+eraseRange]
    canvas.coords(eraser_border,*eraseRect)
    
    inRange = canvas.find_overlapping(*eraseRect)
    for stroke in inRange:
        if stroke not in tool_shapes:
            stroke_coords = canvas.coords(stroke)
            line_width = float(canvas.itemcget(stroke,"width"))
            
            canvas.delete(stroke)

            #increase eraser relative to line width
            eraseRect_w = [x-eraseRange-line_width/2, y-eraseRange-line_width/2, x+eraseRange+line_width/2, y+eraseRange+line_width/2]
        
            last_seg = 0
            
            #iterate through a line segment
            for i in range(len(stroke_coords)//2-1):
                ax,ay,bx,by = stroke_coords[i*2 : i*2 + 4]

                #check if line segment intersects with the eraser
                if not aabb(*eraseRect_w, min(ax,bx),min(ay,by),max(ax,bx),max(ay,by)):
                    continue

                state = 0

                #check which points are inside the rectangle
                if (pointInBox(ax,ay,*eraseRect_w)): state += 1
                if (pointInBox(bx,by,*eraseRect_w)): state += 2

                match state:
                    case 0:
                        #this means the line intersects the box at two points
                        #so it has to be split into two lines 

                        nx, ny = boxIntersection(bx,by,ax,ay,*eraseRect_w)
                        nx2, ny2 = boxIntersection(ax,ay,bx,by,*eraseRect_w)

                        if (nx != -1 and nx2 != -1):
                            create_line_group(stroke_coords[last_seg*2:i*2+2] + [nx, ny], line_width)

                            stroke_coords[i*2] = nx2
                            stroke_coords[i*2+1] = ny2
                            
                            last_seg = i

                    case 1:#if its just one, move the colliding point to the intersection point

                        nx, ny = boxIntersection(ax,ay,bx,by,*eraseRect_w)
                        if (nx != -1):
                            stroke_coords[i*2] = nx
                            stroke_coords[i*2+1] = ny
                            last_seg = i
                    case 2:
                        nx, ny = boxIntersection(bx,by,ax,ay,*eraseRect_w)
                        if (nx != -1):
                            create_line_group(stroke_coords[last_seg*2:i*2+2] + [nx, ny], line_width)
                            last_seg = i + 2

                    case 3:#the entire line is within the eraser, so delete it

                        last_seg = i + 2


            create_line_group(stroke_coords[last_seg*2:], line_width)

def create_line_group(segments, line_width):
    n = len(canvas.find_overlapping(0,0,512,512))
    
    ls = len(segments)
    if ls < 2 or ls % 2 == 1: return
    if ls == 2:
        canvas.create_line(*segments, *segments, width=line_width, fill=bskyBlue, capstyle="round", joinstyle="round")
        return
    canvas.create_line(*segments, width=line_width, fill=bskyBlue, capstyle="round", joinstyle="round")


def RMB_released(event):
    canvas.itemconfig(eraser_border, state='hidden')

# Draw bindings
canvas.bind("<B1-Motion>", draw)
window.bind("<ButtonRelease-1>", LMB_released)
canvas.bind("<B3-Motion>", erase)
window.bind("<ButtonRelease-3>", RMB_released)
canvas.config(cursor="tcross")

def brushPreview(event):
    r = brushSize / 2
    canvas.tag_raise(brush_border)
    canvas.itemconfig(brush_border, state='normal')
    canvas.coords(brush_border,256-r, 256-r, 256+r,256+r)

def eraserPreview(event):
    r = eraseRange
    canvas.tag_raise(eraser_border)
    canvas.itemconfig(eraser_border, state='normal')
    canvas.coords(eraser_border,256-r, 256-r, 256+r,256+r)

brushSizeSlider.bind("<B1-Motion>", brushPreview)
brushSizeSlider.bind("<ButtonRelease-1>", lambda event: canvas.itemconfig(brush_border, state='hidden'))

eraseRangeSlider.bind("<B1-Motion>", eraserPreview)
eraseRangeSlider.bind("<ButtonRelease-1>", lambda event: canvas.itemconfig(eraser_border, state='hidden'))

clearButtonText = "Clear Canvas"
clearButtonReleased = False
clearButtonTime = 0

def clear_timer():
    global clearButtonText, clearButtonTime, clear_timer_worker, clearButtonReleased
    if not clearButtonReleased:
        if clearButtonTime < 10:
            clearButtonTime += 1
            clearButton["text"] = clearButtonTime//2 * "█" + (clearButtonTime%2)*"▌" + (5-clearButtonTime//2-(clearButtonTime%2)) * "    " 
            time.sleep(.1)
            clear_timer()
        elif clearButtonTime == 10:
            clearButton["text"] = clearButtonText
            clearButtonTime += 1
            clear_canvas()
    
clear_timer_worker = None

def clear_button_hold(event):
    global clearButtonText, clearButtonReleased, clear_timer_worker
    clearButtonText = clearButton["text"]
    clearButtonReleased = False

    if not clear_timer_worker: 
        clear_timer_worker = Thread(target=clear_timer)
        clear_timer_worker.start()
    
  
def clear_button_release(event):
    global clearButtonText, clearButtonReleased, clear_timer_worker, clearButtonTime
    clearButtonReleased = True

    if clear_timer_worker:
        clear_timer_worker.join()
        clear_timer_worker = None
        clearButtonTime = 0

    clearButton["text"] = clearButtonText

clearButton.bind("<Button-1>", clear_button_hold)
clearButton.bind("<ButtonRelease-1>", clear_button_release)

# Run program
window.after_idle(onload)
window.mainloop()