#Dedicated to my wife who put up with me being obsessed with the computer for a month

import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk
import PIL.Image
import PIL.ImageTk
import PIL
import math
import pymupdf
import chillimark
import threading
import os
from ctypes import windll

def progress_bar(condition=None):
    bar = tkinter.ttk.Progressbar(btn_frame, orient = tkinter.HORIZONTAL, length = 280, mode = 'indeterminate')
    wait = threading.Event()
    bar.pack(side='top', pady = (0,10), fill="x")
    while condition.is_alive():
        bar['value']+=10
        wait.wait(0.1)
        bar.update()
    bar.destroy()

def thumb_grid(doc):
    grid_size = 1
    
    grid_size = math.isqrt(len(doc))+1*(math.sqrt(len(doc))!=math.isqrt(len(doc)))
    thumb_size = (500//grid_size-1,705/grid_size)
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

def open_file(filename):
    
    if not filename:
        return
    
    canvas_frame.children.clear()
    canvas = tkinter.Canvas(canvas_frame, bg=palette.get("frame"), height=705, width=5, bd=0, highlightthickness=0, relief='ridge')
    canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")

    doc = pymupdf.open(filename)
    thumb_size, positions = thumb_grid(doc)
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=50, colorspace="RGB")
        img = PIL.Image.frombuffer("RGB", [pix.width, pix.height], pix.samples)  
        
        img.thumbnail(thumb_size)
        thumb = PIL.ImageTk.PhotoImage(img)
        panel = tkinter.Label (canvas)
        panel.grid(row=positions[i][0], column=positions[i][1])
        panel.config(image=thumb)
        panel.image = thumb
    
    global first_page
    first_page = chillimark.first_page(filename)#sneaky workaround to avoid loading time of first page.
    return

def choose_file():
    global filename
    filename = tkinter.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

    open_thread = threading.Thread(target=open_file, args=[filename])
    #open_thread.daemon=True
    progress_thread = threading.Thread(target=progress_bar, args=[open_thread])
    progress_thread.start()
    open_thread.start()

def mark_exam():
    key_input=ans_key_box.get(1.0, "end-1c")
    names_input=stu_names_box.get(1.0, "end-1c")
    print(threading.activeCount())
    if filename == None:
        tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
        return
    elif not key_input or not names_input:
        if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered either the Student Names or Answer Key. \nAre you sure you want to continue?"):
            return
    
    chillimark.main(filename,key_input,names_input,first_page)
    path_to_save = filename.replace(".pdf","")
    os.startfile(path_to_save)


global filename
filename = None

root = tkinter.Tk()
windll.shcore.SetProcessDpiAwareness(1)
icon = PIL.ImageTk.PhotoImage(file="icons\Icon128.png")
version = ["v0.8","Capsaicin"]
#version = ["v1.0","Adjuma"]

root.tk.call('wm', 'iconphoto', root._w, PIL.ImageTk.PhotoImage(file="icons\Icon16.ico"))
root.title("Chilli Marker")
palette = {
    "darktext" : "#280e0d",
    "frame" : "#571622",
    "whitespace" : "#e3e5ef",
    "lighttext" : "#e3e5ef",
    "bg": "#8c1529",
    "button": "#b1a1a4",
    "prog_bar":"#00713e"}

root.configure(bg=palette.get("bg"), borderwidth=2)

root.geometry("920x750")
root.resizable(False, False)
default_font = tkinter.font.nametofont("TkDefaultFont")
small_font=default_font.copy()
default_font.configure(size=14, weight="bold")
small_font.configure(size=10)
root.option_add("*Font", default_font)
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

canvas_frame = tkinter.Frame(root,bg=palette.get("frame"), height=725, width=523, bd=0, highlightthickness=0, relief='ridge')
canvas_frame.grid(padx="10", pady="10", column=0,row=0)
canvas_frame.columnconfigure(0, weight=1)
canvas_frame.rowconfigure(1, weight=1)
canvas_frame.grid_propagate(False)

btn_frame = tkinter.Frame(root, bg=palette.get("bg"),height=725,width=523)
btn_frame.grid(padx=(0,10), pady="10",column=1,row=0, sticky="nsew")

mark_frame = tkinter.Frame(btn_frame, bg=palette.get("bg"))
mark_frame.pack(side="bottom", fill="x")
mark_btn=tkinter.Button(mark_frame, text="Mark Exams", height = 4, width = 20,borderwidth=3, command=mark_exam)
mark_btn.pack(padx=(0,5),pady=(10,0), side='left', fill="both", expand='yes')
tkinter.Label(mark_frame, bg=palette.get("bg"), image=icon).pack(side='top')
tkinter.Label(mark_frame, text=version, bg = palette.get("bg")).pack(side='bottom')

entry_frame = tkinter.Frame(btn_frame,bg=palette.get("frame"), height= 500)
entry_frame.pack(side = "bottom", fill="both", expand="yes")

entry_frame_ans= tkinter.Frame(entry_frame,bg=palette.get("frame"))
entry_frame_ans.pack(side="right", pady="10",fill="both", expand="yes")
entry_frame_stu= tkinter.Frame(entry_frame,bg=palette.get("frame"))
entry_frame_stu.pack(side="left", pady=10,padx=(10,0), fill="both", expand="yes")

tkinter.Label(entry_frame_ans,text="Answer Key",width=9,height = 1,anchor="w",bg=palette.get("frame"),fg=palette.get("lighttext")).pack(sid="top", pady="10")
ans_key_box=tkinter.Text(entry_frame_ans,width=10,height=2, bg=palette.get("whitespace"))
ans_key_box.pack(padx = "10",fill="both",expand="yes")

tkinter.Label(entry_frame_stu, text="Student Names", height = 1, anchor="w",bg=palette.get("frame"),fg=palette.get("lighttext")).pack(side = "top", padx="10", pady="10")
tkinter.Label(entry_frame_stu,wraplength=190, bg=palette.get("frame"),text="Organize the names in the same order as the scans\nExample: \n    Tanner Moore \n    Emily Hunt\n    Foster Holmes\n    Bailey Alexander\n    ...",anchor="w", font=small_font,fg=palette.get("lighttext"),justify="left").pack(side="bottom", pady="10", anchor=tkinter.NW)
stu_names_box=tkinter.Text(entry_frame_stu,width=30,height=2,font=small_font, bg=palette.get("whitespace"))
stu_names_box.pack(side = "top",fill="both",expand="yes")

file_btn=tkinter.Button(btn_frame, text="Select Exam", height = 1, width = 20, borderwidth=3, command=choose_file)
file_btn.pack(side="bottom",pady=(0,10),fill="x")

root.mainloop()


