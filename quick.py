import tkinter.filedialog
import pymupdf

filename = tkinter.filedialog.askopenfilename()
doc = pymupdf.open(filename)

scans = []
for i, page in enumerate(doc):
    scans.append(page.get_pixmap())
    mode = "RGBA" if scanspix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    tkimg = ImageTk.PhotoImage(img)
