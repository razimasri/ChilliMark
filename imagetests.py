import cv2
import pymupdf
import numpy
import time
import tkinter
import PIL.Image
import PIL.ImageTk
import PIL
import math

def thumb_grid(doc):
    grid_size = 1
    
    grid_size = math.isqrt(len(doc))+1*(math.sqrt(len(doc))!=math.isqrt(len(doc)))
    thumb_size = (500//grid_size-grid_size//2,705//grid_size-grid_size)
    positions = []
    c=0
    r=0
    while r < grid_size:
        while c < grid_size:
            positions.append([r,c])
            c+=1
        c=0
        r+=1
    return thumb_size ,positions

root = tkinter.Tk()
start = time.time()
doc = pymupdf.open("sample\igsample.pdf")
thumb_size, positions = thumb_grid(doc)

for i, page in enumerate(doc):
	pix = page.get_pixmap(dpi=50, colorspace="RGB")
	img = PIL.Image.frombuffer("RGB", [pix.width, pix.height], pix.samples)  
	
	img.thumbnail(thumb_size,resample=PIL.Image.Resampling.NEAREST,reducing_gap=1)
	thumb = PIL.ImageTk.PhotoImage(img)
	panel = tkinter.Label (root)
	panel.grid(row=positions[i][0], column=positions[i][1])
	panel.config(image=thumb)
	panel.image = thumb
end = time.time()
print(end-start)


root.mainloop()
