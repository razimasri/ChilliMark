import tkinter.filedialog
import pymupdf
import PIL.Image
import PIL.ImageTk
import numpy
import math



filename = tkinter.filedialog.askopenfilename()
doc = pymupdf.open(filename)


grid_size = math.isqrt(len(doc))+1
thumb_size = (500//grid_size-grid_size*2,705//grid_size-grid_size*2)
positions = []

c=0
r=0
while r < grid_size:
    while c < grid_size:
        positions.append([r,c])
        c+=1
    c=0
    r+=1


scans = []
root = tkinter.Tk()
canvas = tkinter.Canvas(root).pack()
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=600, colorspace="GRAY")
    img = PIL.Image.frombytes("BGR", [pix.width, pix.height], pix.samples)
    tkimg = PIL.ImageTk.PhotoImage(img)
    scans.append(img)
    
    thumb = img.thumbnail(thumb_size)
    thumb = PIL.ImageTk.PhotoImage(img)
    panelA = tkinter.Label (canvas)
    panelA.grid(row=positions[i][0], column=positions[i][1])
    panelA.config(image=thumb)
    panelA.image = thumb





root.mainloop()
