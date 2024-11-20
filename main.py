import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk
import tkPDFViewer


import PIL.Image
import PIL.ImageTk

import math

import tkPDFViewer.tkPDFViewer
import test_grader
import pymupdf
import numpy
import io


def thumb_grid(doc):
    grid_size = 1
    if len(doc)>1:
        grid_size = math.isqrt(len(doc))+1
    thumb_size = (500//grid_size-2,705//grid_size-2)
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


def choose_file():
    global filename, scans
    filename = tkinter.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

    if not filename:
        return
    canvas_frame.children.clear()
    canvas = tkinter.Canvas(canvas_frame, bg=palette.get("frame"), height=725, width=523, bd=0, highlightthickness=0, relief='ridge')
    canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")

    doc = pymupdf.open(filename)

    #v1= tkPDFViewer.tkPDFViewer.ShowPdf()
    #v2 = v1.pdf_view(root, pdf_location=filename, width=525, height=725,load="")
    #v2.grid(row=0,column = 0)
    
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
    
    
def mark_exam():
    global filename, scans
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
        name = "".join(filter(lambda x: not x.isdigit(), name))
        if not name:
            stu_names.pop(i)
        else:
            stu_names[i]=name.rstrip(", ")

    if filename == None:
        tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
        return
    elif not ans_key or not stu_names:
        if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered the Student Names or Answer Key. \nAre you sure you want to continue?"):
            return
    
    scans = test_grader.main(scans,ans_key_nums,ans_key_letter)
    marked_pdf = pymupdf.open()
    for scan in scans:
        
        pil_scan = PIL.Image.fromarray(scan[0][:,:,::-1])
        bio = io.BytesIO()
        pil_scan.save(bio,"jpeg")
        bytes_scan = pymupdf.open('jpg',bio.getvalue())
        pdfbytes = bytes_scan.convert_to_pdf()
        rect = bytes_scan[0].rect
        bytes_scan.close()
        pdf_scan = pymupdf.open("pdf", pdfbytes)
        page = marked_pdf._newPage(width=rect.width, height=rect.height)
        page.show_pdf_page(rect,pdf_scan,0)

    path_to_save = tkinter.filedialog.asksaveasfilename(defaultextension='.pdf', initialfile = 'Marked exam')
    if path_to_save:
        marked_pdf.save(path_to_save)
        

        




version = ["1.0","Adjuma"]






root = tkinter.Tk()
#root.tk.call('wm', 'iconphoto', root._w, PIL.ImageTk.PhotoImage(file="chillimark.ico"))
root.title("Chilli Marker")
palette = {
    "darktext" : "#280e0d",
    "frame" : "#571622",
    "whitespace" : "#e3e5ef",
    "lighttext" : "#e3e5ef",
    "bg": "#8c1529",
    "button": "#b1a1a4"}
root.configure(bg=palette.get("bg"), borderwidth=2)
filename=None
ans_key=None
stu_names=None
scans=[]
output =[]

root.geometry("1035x750")
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


file_btn=tkinter.Button(btn_frame, text="Select Exam", height = 1, width = 20, borderwidth=3, command=choose_file)
file_btn.pack(side="top",pady=(0,10))
entry_frame = tkinter.Frame(btn_frame,bg=palette.get("frame"), height= 500)
entry_frame.pack(fill="both", expand="yes")
mark_btn=tkinter.Button(btn_frame, text="Mark Exams", height = 3, width = 20,borderwidth=3, command=mark_exam)
mark_btn.pack(side="bottom",pady=(10,0))

entry_frame_ans= tkinter.Frame(entry_frame,bg=palette.get("frame"))
entry_frame_ans.pack(side="left", padx=(0,10), pady="10",fill="both", expand="yes")
entry_frame_stu= tkinter.Frame(entry_frame,bg=palette.get("frame"))
entry_frame_stu.pack(side="right", padx=(0,0), pady="10",fill="both", expand="yes")

tkinter.Label(entry_frame_ans,text="Answer Key",height = 1,anchor="w",bg=palette.get("frame"),fg=palette.get("lighttext")).pack(sid="top",padx="10", pady="10")
tkinter.Label(entry_frame_ans,bg=palette.get("frame"),text="On separate lines or with commas\nExample: With commas\n    A, A, B, C, ... \n Or: On separate lines\n    A\n    A\n    B\n    ...",anchor="w", font=small_font,fg=palette.get("lighttext"),justify="left").pack(side="bottom", padx="10", pady="10")
ans_key_box=tkinter.Text(entry_frame_ans,width=30,height=2, font=small_font, bg=palette.get("whitespace"))
ans_key_box.pack(padx = "10",fill="both",expand="yes")

tkinter.Label(entry_frame_stu, text="Student Names", height = 1, anchor="w",bg=palette.get("frame"),fg=palette.get("lighttext")).pack(side = "top", padx="10", pady="10")
tkinter.Label(entry_frame_stu,wraplength=190, bg=palette.get("frame"),text="Organize the names in the same order as the scans\nExample: \n    Tanner Moore \n    Emily Hunt\n    Foster Holmes\n    Bailey Alexander\n    ...",anchor="w", font=small_font,fg=palette.get("lighttext"),justify="left").pack(side="bottom", padx="10", pady="10")
stu_names_box=tkinter.Text(entry_frame_stu,width=30,height=2,font=small_font, bg=palette.get("whitespace"))
stu_names_box.pack(padx="10",fill="both",expand="yes")

root.mainloop()
