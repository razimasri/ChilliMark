#Dedicated to my wife who put up with me being obsessed with the computer for a month

import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk
import os
import PIL.Image
import PIL.ImageTk
import math
import pymupdf
import numpy
import test_grader
import csv
import threading
import time
import cv2
from ctypes import windll

def progress_bar(condition):
    bar = tkinter.ttk.Progressbar(btn_frame, orient = tkinter.HORIZONTAL, length = 280, mode = 'indeterminate')
    bar.pack(side='top', pady = (0,10), fill="x")
    wait = threading.Event()
    while condition.is_alive():
        bar['value']+=10
        wait.wait(0.1)
        bar.update()
    bar.destroy()

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

def open_file(filename):
    global scans

    if not filename:
        return
    
    canvas_frame.children.clear()
    canvas = tkinter.Canvas(canvas_frame, bg=palette.get("frame"), height=725, width=523, bd=0, highlightthickness=0, relief='ridge')
    canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")

    doc = pymupdf.open(filename)
    thumb_size, positions = thumb_grid(doc)

    scans = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=600, colorspace="RGB") #reduce colour space
        image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  
        
        scans.append(image)
        
        thumb = img.thumbnail(thumb_size)
        thumb = PIL.ImageTk.PhotoImage(img)
        panel = tkinter.Label (canvas)
        panel.grid(row=positions[i][0], column=positions[i][1])
        panel.config(image=thumb)
        panel.image = thumb
    return

def choose_file():
    global filename, scans

    filename = tkinter.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

    open_thread = threading.Thread(target=open_file, args=[filename])
    open_thread.daemon=True
    progress_thread = threading.Thread(target=progress_bar, args=[open_thread])
    progress_thread.start()
    open_thread.start()

def mark_exam():
    global filename, scans, stu_names

    ans_key_input=ans_key_box.get(1.0, "end-1c")
    stu_names_input=stu_names_box.get(1.0, "end-1c")
    ans_key_nums={}
    ans_key_letter={}
    
    ans_key_input = "".join(x for x in ans_key_input if x.isalpha())
    ans_key_input = ans_key_input.upper()
    for i, ans in enumerate(ans_key_input): #should make the ans_key in number rather than letters to prevent repeated conversion    
        ans_key_nums[i]=ord(ans)-65
        ans_key_letter[i]=ans
    
    stu_names_input = stu_names_input.title()
    stu_names = stu_names_input.split("\n")
    
    for i, name in enumerate(stu_names.copy()):
        if not name:
            stu_names.pop(i)
        else:
            stu_names[i]=name.rstrip(", ")
    #print(stu_names)
    
    if filename == None:
        tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
        return
    elif not ans_key_nums or not stu_names:
        if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered the Student Names or Answer Key. \nAre you sure you want to continue?"):
            return

    basename= os.path.basename(filename)
    basename= basename.replace(".pdf","")
    path_to_save = filename.replace(".pdf","")

    inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2 = test_grader.set_parameters(scans)
    
    process_thread = threading.Thread(target=process, args=(scans,ans_key_nums,ans_key_letter,inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2,path_to_save,ans_key_input))
    progress_thread = threading.Thread(target=progress_bar, args=[process_thread])
    progress_thread.start()
    process_thread.start()
    
def process(scans,ans_key_nums,ans_key_letter,inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2,path_to_save,ans_key_input):
    start = time.time()
    marked_work = test_grader.process(scans,ans_key_nums,ans_key_letter,inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2)
    
    global marked_pdf
    if not(os.path.exists(path_to_save) and os.path.isdir(path_to_save)):
        os.mkdir(path_to_save)
                
    make_output(marked_work,path_to_save,ans_key_input,stu_names)
    end = time.time()

    print("time", end-start)

def make_output(marked_work,path_to_save,ans_key_input,stu_names):


    file = open(f"{path_to_save}/answers.csv", 'w' ,newline='')
    writer = csv.writer(file, dialect='excel', )
    writer.writerow(["Student Name"]+[f"Out of {len(ans_key_input)}"]+list(ans_key_input))
    marked_pdf = pymupdf.open()
    stats_raw = marked_work[0][2]
    if not(os.path.exists(f"{path_to_save}/single pages") and os.path.isdir(f"{path_to_save}/single pages")):
        os.mkdir(f"{path_to_save}/single pages")
    
    for i, mark in enumerate(marked_work):
        if stu_names:
            writer.writerow([stu_names[i]]+[mark[1]]+mark[2])
            string = stu_names[i].replace(",", "")
            mark[0]=cv2.putText(mark[0],string,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(255,255,255),25)
            mark[0]=cv2.putText(mark[0],string,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(0,0,0),10)
            jpeg_path =f"{path_to_save}/single pages/{string}.jpg"
        else:
            writer.writerow([f"Student {i+1}"]+[mark[1]]+mark[2])
            jpeg_path= f"{path_to_save}/single pages/Student {i+1}.jpg"

        pil_scan = PIL.Image.fromarray(mark[0][:,:,::-1])
        #bio = io.BytesIO()
        #pil_scan.save(bio,"jpeg")
        #bytes_scan = pymupdf.open('jpg',bio.getvalue()) (save incase web version cannot write)
        pil_scan.save(jpeg_path)
        bytes_scan = pymupdf.open(jpeg_path)                #bytes_scan = pymupdf.open('png',mark[0])
        pdfbytes = bytes_scan.convert_to_pdf()
        rect = bytes_scan[0].rect                           #bytes_scan.close()
        
        pdf_scan = pymupdf.open("pdf", pdfbytes)
        
    
#eventually add logic to add student name. Don't want ot code in dealing with the commas
        page = marked_pdf._newPage(width=rect.width, height=rect.height)
        page.show_pdf_page(rect,pdf_scan,0) 

        if i>0:
            stats_raw = zip(stats_raw,mark[2])

    marked_pdf.save(f"{path_to_save}/answers.pdf")
    #deal with stats of answers
    stats = [] 
    options = sorted(set(ans_key_input)) #currently randomly makes 6 choices. Can automate with sets 
    csv_stats = [["Correct"]]
    rates = {"Correct": 0}
    for option in options:
        rates.update({option : 0})
        csv_stats.append([option])       
    for i, row in enumerate(stats_raw):
        rate = rates.copy()
        if i == len(ans_key_input):
            break
        for ans in row:
            if rate.get(ans)!= None:
                rate[ans]=rate.get(ans) + 1
            if ans == ans_key_input[i] and ans_key_input:
                rate["Correct"] = rate.get("Correct") +1
        stats.append(rate.values())

    for row in stats:
        for k, r in enumerate(row):
            csv_stats[k].append(r)

    writer.writerow([""])
    for x in csv_stats:
        writer.writerow([""]+x)

    os.startfile(path_to_save)

root = tkinter.Tk()
windll.shcore.SetProcessDpiAwareness(1)
icon = PIL.ImageTk.PhotoImage(file="icons\Icon128.png")
version = ["v0.6","Capsaicin"]
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
filename=None

stu_names=None
scans=[]
output =[]

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
