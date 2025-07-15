import requests
import configparser
import json
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
from atproto import Client, client_utils
from io import BytesIO
from pathlib import Path
from threading import *
import re
import dns.resolver

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

def login():
    global appLang, loggedIn, pfpOriginal, postBtnBG, postBtnFG, pfpTk, postButton, langs

    # Get data from config.ini
    config = configparser.ConfigParser(allow_no_value=True)
    config.read("config.ini")
    handle = clean_input(config["Login"]["bsky_handle"])
    password = clean_input(config["Login"]["app_password"])
    configLang = clean_input(config["Misc"]["language"])
    
    if configLang != "":
        langs = [configLang]
        
        # Change app language if lang is set to a supported language
        if configLang == "ja":
            appLang = "ja"
            change_language()

    try: 
        account = client.login(handle, password)
    except:
        messagebox.showerror("Unable to log in", "SkyDraw couldn't log in to your Bluesky account :( \n\nMake sure the login info in the config file is correct and try again.")
    else:
        loggedIn = TRUE
        avatar = requests.get(account.avatar)
        pfpOriginal = Image.open(BytesIO(avatar.content)).resize((18, 18))
        pfpTk.paste(pfpOriginal)
        postButton["text"] = UIText[appLang]["post"]
        postButton["bg"] = bskyBlue
        postButton["fg"] = "white"

def login_thread():
    t1 = Thread(target=login)
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
    # Reduce all line width by .5 to attempt to correct postscript's fault
    inRange = canvas.find_overlapping(0, 0, 512, 512)
    for i in inRange:
        if i != eraser_border:
            v = float(canvas.itemcget(i,"width"))
            canvas.itemconfig(i, width = max(v - .5,.5))

    # Export the eps file, then open it and save it as png
    canvas.postscript(file="canvas/canvas.eps", pagewidth=511)
    img = Image.open("canvas/canvas.eps")
    img.save(imgPath, "png")

    # Set all line width by back to normal, in the case of being unable to post (so lines don't keep getting thinner with each attempt)
    for i in inRange:
        if i != eraser_border:
            v = float(canvas.itemcget(i,"width"))
            canvas.itemconfig(i, width = min(v + .5, 64))

# Clear canvas
def clear_canvas():
    inRange = canvas.find_overlapping(0, 0, 512, 512)
    for stroke in inRange:
        if stroke != eraser_border:
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
        except requests.ConnectionError:
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

        for text in caption.split(" "):
            if re.fullmatch(hashtag_regex, text) != None:
                postText.tag(text, text[1:])
                postText.text(" ")
                continue

            if re.fullmatch(link_regex, text) != None:
                postText.link(text, text)
                postText.text(" ")
                continue

            if len(text) > 1 and text[0] == '@':
                did = resolve_handle(text[1:])
                if did == None:
                    messagebox.showerror("Invalid Handle","Attempting to tag a user that does not exist: " + text)
                    return
                
                postText.mention(text, did)
                postText.text(" ")
                continue
            
            postText.text(text + " ")

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
clearButton = Button(row3, text="Clear Canvas", command=clear_canvas)
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
        if collinear(*prevLineCoords,x,y): #if the previous line is colinear with the new point, u can just extend the previous line
            canvas.coords(prevLine,*(prevLineCoords[:2]),x,y)
        else: #else make a new line
            prevLine = canvas.create_line(*(prevLineCoords[2:4]), x, y, width=brushSize, fill=bskyBlue, capstyle="round", joinstyle="round")

    LMBWasReleased = FALSE

def draw(event):
    global mouseBuffer, mouseBufferMaxSize

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

eraser_border = canvas.create_rectangle(0,0,0,0,outline="#7F7F7F", state='hidden')

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

def erase(event):
    x = event.x
    y = event.y
    
    canvas.itemconfig(eraser_border, state='normal')

    eraseRect = [x-eraseRange, y-eraseRange, x+eraseRange, y+eraseRange]
    canvas.coords(eraser_border,*eraseRect)
    
    inRange = canvas.find_overlapping(*eraseRect)
    for stroke in inRange:
        if stroke != eraser_border:
            ax,ay,bx,by = canvas.coords(stroke)
            line_width = float(canvas.itemcget(stroke,"width"))/2
            state = 0

            #increase eraser relative to line width
            eraseRect_w = [x-eraseRange-line_width, y-eraseRange-line_width, x+eraseRange+line_width, y+eraseRange+line_width]

            #check which points are inside the rectangle
            if (pointInBox(ax,ay,*eraseRect_w)): state += 1
            if (pointInBox(bx,by,*eraseRect_w)): state += 2

            match state:
                case 0:
                    #this means the line intersects the box at two points
                    #so it has to be split into two lines 

                    nx, ny = boxIntersection(ax,ay,bx,by,*eraseRect_w)
                    if (nx != -1 ):
                        canvas.coords(stroke,nx,ny,bx,by)

                    nx, ny = boxIntersection(bx,by,ax,ay,*eraseRect_w)
                    if (nx != -1 ):
                        canvas.create_line(nx,ny,ax,ay, width=line_width*2, fill=bskyBlue, capstyle="round", joinstyle="round")

                case 1:#if its just one, move the colliding point to the intersection point
                    nx, ny = boxIntersection(ax,ay,bx,by,*eraseRect_w)
                    if (nx != -1):
                        canvas.coords(stroke,nx,ny,bx,by)
                case 2:
                    nx, ny = boxIntersection(bx,by,ax,ay,*eraseRect_w)
                    if (nx != -1):
                        canvas.coords(stroke,ax,ay,nx,ny)
                case 3:#the entire line is within the eraser, so delete it
                    canvas.delete(stroke)

def RMB_released(event):
    canvas.itemconfig(eraser_border, state='hidden')

# Draw bindings
canvas.bind("<B1-Motion>", draw)
window.bind("<ButtonRelease-1>", LMB_released)
canvas.bind("<B3-Motion>", erase)
window.bind("<ButtonRelease-3>", RMB_released)

# Run program
window.after_idle(login_thread)
window.mainloop()