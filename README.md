# SkyDraw
Anti-perfectionist Bluesky doodling application

<img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreic2wdtqbr3riaaz2eja3eelzkapezd7wokmjbeg3yucboz2kx7rxq@jpeg" alt="sampleImage1" width="256"/> <img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreia67hg7rpfdvrjknsvinph2ytirmd7mlkakrbenen2vsamyftavbe@jpeg" alt="sampleImage2" width="256"/> <img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreiez5ta2xdwsvc4xwpjsubxiq2vmsveydzlwqiaydlargwo67znxri@jpeg" alt="sampleImage3" width="256"/>

[Get the latest release here!](https://github.com/iamsako/SkyDraw/releases/latest) 
(Only a Windows build is available for now, but hopefully the source code works on other platforms)

## How to setup
**DUMB PREREQUISITE:** 
This application requires [Ghostscript](https://ghostscript.com/) installed to be able to convert the drawing from a .eps file (the format that Tkinter, the Python GUI framework this uses, saves the canvas as) to a normal image format that can be posted. Just regular Ghostscript is required, not GhostPCL or XPS or whatever else listed on the downloads page. Get the AGPL release for your platform. After downloading and installing it, make sure it appears in Path in your system environment variables (as "...\gs\gs(version)\bin"). If you have no idea what that last sentence was on about, the installer should've done that automatically anyway so you should be fine.

I wish this wasn't necessary and if I find a way to avoid this prerequisite, I will.

After all that:
- Unzip the zip (if downloaded from a release)
- Open config.ini
- Enter your Bluesky handle (without the @) after "bsky_handle ="
- Enter an [app password](https://bsky.app/settings/app-passwords) after "app_password =" (you can use your actual password but an app password is safer!)
- By default, posts from this application are tagged as both English and Japanese. If you want to change it to any single language, add an [ISO language code](https://www.w3schools.com/tags/ref_language_codes.asp) after "language =". Otherwise you can leave it blank or edit the source code if you want posts tagged as multiple other languages.

Here's an example of what the configured ini file should look like:
```
[Login]
bsky_handle = yourcoolname.bsky.social
app_password = abcd-1234-efgh-5678

[Misc]
language = en
```

Once the ini file is configured, save it and run the exe (or main.py). If the app was able to login to your account, the "Post to Bluesky" button will be blue and it will have your profile picture on it (very teeny tiny). Nice!

## How to use
- Left click to draw
- Right click to erase
- Change the brush and eraser size with the sliders
- You can type a caption and enter alt text in the text boxes at the bottom
- Click the "Clear Canvas" button to, uhh...
- Click the "Post to Bluesky" button to... clear the canvas?
- TIP: If you want to draw at the very edges of the canvas without accidentally clicking on something else (like the close button...), you can make the window bigger (the canvas will stay the same size)

## Quirks and limitations of this application
- No undo/redo
- Only one colour
- Posting will also immediately clear the canvas if the post was successful (this is intentional, done is done).
- Drawn lines in the final posted image may be slightly thicker than they were while drawing. This is a quirk with how drawing and image conversion is handled in this app. It's complicated, not sure how to fix this without using a completely different framework and rewriting everything (turns out tkinter isn't really suitable for this kind of application it seems).
- The program will probably lag if too many lines are drawn. Erasing lines will help if this happens.
- <s>Hashtags (and tagging other users, I assume) don't work in the caption field, they won't be blue and clickable in the post.</s> Thanks to [numa](https://github.com/numa-smells) for fixing this!
- Posts won't have any content warnings applied, so sensitive drawings may get them slapped on later on by Bluesky moderation. I may add a checkbox for it eventually, if I can figure out how to get that working.

<img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreifgda3tdua2juhe4revltkitwhnkdm5tdwpb5646kjs2fjdtpktsa@jpeg" alt="sampleImage3" width="256"/>

Nearly everything about this application new and unfamiliar to me. I'm not used to Python or Tkinter and haven't really dealt with social media APIs before. I don't know the best way to handle things like safely storing and reading login details and passwords. This is my first public project on GitHub, I don't know if I'm doing things correctly! 

This application is incredibly jank and I know it. It takes a long time to start up, lags if you draw too much, requires downloading something else to convert the drawing to an image file, and the final image is slighly different to how it appeared on the canvas. But despite all that... it's functional and is exactly the application I wanted to make for myself. It's good enough for me to use regularly throughout the past year (with 60+ posts from it as of writing), so I thought it might be good enough for other people to use if they want. I wish the setup was simpler, but here it is. Maybe someday I'll completely remake this in a different language/framework to be more performant and easier to setup.
