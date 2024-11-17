import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import PIL.Image
import PIL.ImageTk
import cv2
#import test_grader

def choose_file():
    global panelA
    global filename
    
    filename = tkinter.filedialog.askopenfilename()

    if filename:
        image = cv2.imread(filename)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = PIL.Image.fromarray(image)
        thumbnail = image.thumbnail([500,705])
        thumbnail = PIL.ImageTk.PhotoImage(image)
        
    if panelA is None:
        panelA = tkinter.Label (canvas,image=thumbnail)
        panelA.image = thumbnail
        panelA.pack(side="left", padx=10, pady=10)
        
    else:
        panelA.configure(canvas,image=thumbnail)
        panelA.image=thumbnail
    
def mark_exam():
    
    ans_key=ans_key_box.get(1.0, "end-1c")
    stu_names=stu_names_box.get(1.0, "end-1c")
    print(ans_key)
    if filename == None:
        tkinter.messagebox.showinfo(title="No file", message= "Please select a file")

        return
    elif not ans_key or not stu_names:
        tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered the Student Names or Answer Key. \nAre you sure you want to continue?")
    
    
root = tkinter.Tk()
root.title("Chilli Marker")
root.configure(bg="#002b36", borderwidth=2)
panelA=None
filename=None
ans_key=None
stu_names=None

root.geometry("1000x750")
root.resizable(False,False)
default_font = tkinter.font.nametofont("TkDefaultFont")
small_font=default_font.copy()
default_font.configure(size=14, weight="bold")
small_font.configure(size=10)
root.option_add("*Font", default_font)

canvas = tkinter.Canvas(root, bg="#004052", height=725, width=523, bd=0, highlightthickness=0, relief='ridge')
canvas.pack(side="left",padx="10", pady="10",fill="y",expand="no")

btn_frame = tkinter.Frame(root, bg="#002b36")
btn_frame.pack(side="right", pady="10", fill="both", expand="yes")


file_btn=tkinter.Button(btn_frame, text="Select Exam", height = 1, width = 20, borderwidth=3, command=choose_file)
file_btn.pack(side="top", padx="10", pady="10", expand="no")
mark_btn=tkinter.Button(btn_frame, text="Mark Exams", height = 3, width = 20,borderwidth=3, command=mark_exam)
mark_btn.pack(side="bottom", padx="10", pady="10", expand="no")

entry_frame = tkinter.Frame(btn_frame,bg="#002b36")
entry_frame.pack(side="top",fill="both",expand="yes")
entry_frame_ans= tkinter.Frame(entry_frame,bg="#004052")
entry_frame_ans.pack(padx=(0,10), pady="10",side="left",fill="both",expand="yes")
entry_frame_stu= tkinter.Frame(entry_frame,bg="#004052")
entry_frame_stu.pack(padx=(0,10), pady="10",side="right",fill="both",expand="yes")

tkinter.Label(entry_frame_ans,text="Answer Key",height = 1,anchor="w",bg="#004052",fg="#fff").pack(padx="10", pady="10",fill="x")
tkinter.Label(entry_frame_ans,text="On separate lines or with commas\nExample: With commas\n    A, A, B, C, ... \n Or: On separate lines\n    A\n    A\n    B\n    ...",anchor="w",bg="#004052", font=small_font,fg="#fff",justify="left").pack(side="bottom", fill="x",padx="10", pady="10")
ans_key_box=tkinter.Text(entry_frame_ans,width=1)
ans_key_box.pack(fill="both", padx="10")

tkinter.Label(entry_frame_stu, text="Student Names", height = 1, anchor="w",bg="#004052",fg="#fff").pack(padx="10", pady="10",fill="x")
tkinter.Label(entry_frame_stu,text="Only on separate lines\nExample: \n    Cara Winters \n    Tanner Moore \n    Emily Hunt\n    Foster Holmes\n    Bailey Alexander\n    ...",anchor="w",bg="#004052", font=small_font,fg="#fff",justify="left").pack(side="bottom", fill="x",padx="10", pady="10")
stu_names_box=tkinter.Text(entry_frame_stu,width=30)
stu_names_box.pack(fill="both",expand="yes", padx="10")




root.mainloop()
