import time
import math
import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tksvg
import tkinterdnd2
import random
import tkinterdnd2.TkinterDnD
import PIL
import PIL.Image
import PIL.ImageTk
import os
import pymupdf
import operator
import ctypes
import sys
import webbrowser

class Gui:	

	palette = { 
		"darktext" : "#280e0d",
		"frame" : "#571622",
		"whitespace" : "#e3e5ef",
		"lighttext" : "#e3e5ef",
		"bg": "#8c1529",
		"button": "#b1a1a4",
		"lightgreen" : "#00713e",
		"darkgreen" : "#02251a"}
	
	class Rectangle:
		def __init__(self):
			self.rect = None
			self.x1 = 1
			self.y1 = 1
			self.x2 = 1
			self.y2 = 1
			self.x1true = 1
			self.y1true = 1
			self.x2true = 1
			self.y2true = 1
	
	class Anim_Box:
		
		def __init__(self,frame,i,wide):
			self.canvas=tkinter.Canvas(frame,bd=0,highlightthickness=0, bg=Gui.palette.get("frame"),width=110, height=110)
			self.canvas.grid(row=i//wide, column=i%wide,sticky="nsew")
			self.index = i

		def round(self):
			size=90
			radius = 20
			corners= [(10,10),(10+size,10),(10+size,10+size),(10,10+size)]
			_pattern = [1,1,-1,1,-1,-1,1,-1]
			offset = [radius*i for i in _pattern]
			offset = list(zip(offset[::2], offset[1::2]))
			points=[]
			for i,point in enumerate(corners):
				x,y = point
				ox,oy = offset[i]
				new_x = x+ox
				new_y = y+oy
				if i%2:
					points.append([new_x,y,x,y,x,new_y])
					continue
				points.append([x,new_y,x,y,new_x,y])

			self.poly = self.canvas.create_polygon(points,smooth=1, splinesteps=30,fill="",outline=Gui.palette.get("bg"), width=5)
			self.cover = self.canvas.create_arc(-10,-10,120,120,outline="", fill=Gui.palette.get("frame"),start=0,extent=0, stipple="gray25")
		
		def swipe(self,boxes):
			x=math.degrees(4*(time.time()-self.time))%360
			if (time.time()-self.time)>3.14:
				self.canvas.itemconfig(self.cover,start= 0, extent=0)
				boxes.insert(random.randint(0,len(boxes)-1),self)
				self.colour = f"#{random.randrange(256**3):06x}"
				return
			if (time.time()-self.time)<1.57:
				self.canvas.itemconfig(self.cover, start = self.start, extent=x)
			else:
				self.canvas.itemconfig(self.cover, start = self.start, extent=x-360)
			self.canvas.after(100, lambda: self.swipe(boxes))

	def __init__(self):
		self.root = tkinterdnd2.TkinterDnD.Tk()	
		ctypes.windll.shcore.SetProcessDpiAwareness(1)
		self.version = ["v1.2","Adjuma"] #["v0.9","Capsaicin"]

		self.icon = tksvg.SvgImage(file=get_path(r"icons\iconwhite.svg"), scaletoheight = 128 )
		self.sel_img = tksvg.SvgImage(file=get_path(r"icons\selection.svg"))
		self.pdf_icon = tksvg.SvgImage(file=get_path(r"icons\pdf.svg"), scaletoheight = 256 )
		self.frames = [PIL.Image.open(get_path(f"icons\\animations\\pageprocess\\{file}")) for file in os.listdir(get_path(r"icons\animations\pageprocess"))]
		self.root.tk.call('wm', 'iconphoto', self.root._w, PIL.ImageTk.PhotoImage(file=get_path(r"icons\Icon16.ico")))

		self.root.title("Chilli Marker")
		self.root.configure(borderwidth=2,background=Gui.palette.get("bg"))
		self.root.geometry("1020x900") 
		self.root.resizable(False, False)

		self.default_font = tkinter.font.nametofont("TkDefaultFont")
		self.small_font=self.default_font.copy()
		self.mid_font=self.default_font.copy()
		self.mid_font.configure(size=14)
		self.default_font.configure(size=14, weight="bold")
		self.small_font.configure(size=10)
		self.root.option_add("*Font", self.default_font)
		self.root.columnconfigure(index=1, weight=1)
		self.root.rowconfigure(index=1, weight=2)

		self.response = tkinter.StringVar()

		self.next = tkinter.BooleanVar(value=False)
		self.anim_bool = tkinter.BooleanVar(value=True)
		
	def home(self):
		self.destroy_children(self.root)
		self.next.set(False)
		#Drag and Drop Files
		self.root.drop_target_register(tkinterdnd2.DND_FILES)
		self.root.dnd_bind('<<Drop>>', lambda event: self.open_file(event.data))

		self.canvas_frame = tkinter.Frame(self.root,bg=Gui.palette.get("frame"), height=875, width=622, bd=0, highlightthickness=0, relief='ridge', cursor="hand2")
		self.canvas_frame.grid(padx=10, pady=10, column=0,row=0,rowspan=3,sticky="nsew")
		self.canvas_frame.columnconfigure(index=0, weight=1,minsize=622)
		self.canvas_frame.rowconfigure(index=0, weight=1,minsize=875)
		self.canvas_frame.propagate(False)
		self.pdf = tkinter.Label(self.canvas_frame, bd=0, bg=Gui.palette.get("frame"), image=self.pdf_icon, cursor="hand2")
		self.pdf.grid()
		self.pdf.bind('<Button-1>',self.choose_file)
		self.canvas_frame.bind('<Button-1>',self.choose_file)
		
		self.file_btn=tkinter.Button(self.root, text="Select Exam", height = 1, width = 20, borderwidth=3, command=self.choose_file,cursor="hand2")
		self.file_btn.grid(row=0,column=1,pady=10,padx=(0,10),sticky="new")
		
		self.right_frame = tkinter.Frame(self.root,bg=Gui.palette.get("frame"),height=200)
		self.right_frame.grid(row=1, column=1,sticky="news",padx=(0,10))
		self.right_frame.columnconfigure(index=0, weight=2)
		self.right_frame.columnconfigure(index=1, weight=1)
		self.right_frame.rowconfigure(index=0, weight=1)
		self.right_frame.propagate(False)
		
		stu_frame=tkinter.LabelFrame(self.right_frame,bg=Gui.palette.get("frame"),text="Student Names",fg=Gui.palette.get("lighttext"),labelanchor="n", relief="flat")
		stu_frame.grid(padx=(10,5),pady=(10,10),row=0,column=0,sticky="nsew")
		#stu_frame.grid_propagate(False)
		stu_frame.rowconfigure(index=0,weight=1)
		stu_frame.rowconfigure(index=1,weight=1)
		
		self.stu_names_box=tkinter.Text(stu_frame,width=30, height = 10, font=self.small_font, bg=Gui.palette.get("whitespace"),undo=True, relief="flat")
		self.stu_names_box.pack(pady=10,fill="both",expand="yes")

		ans_frame= tkinter.LabelFrame(self.right_frame,bg=Gui.palette.get("frame"),text="Answer Key",fg=Gui.palette.get("lighttext"),labelanchor="n", relief="flat")
		ans_frame.grid(padx=(5,10),pady=10,row=0,column=1,sticky="nsew")
		ans_frame.rowconfigure(index=0,weight=1)

		self.ans_key_box=tkinter.Text(ans_frame,width=10, height=10, bg=Gui.palette.get("whitespace"),undo=True, relief="flat")
		self.ans_key_box.pack(pady=(10,0),fill="both",expand="yes")

		name_inst = tkinter.Label(stu_frame, wraplength=stu_frame.winfo_screenwidth()//7, bg=Gui.palette.get("frame"),text="Organize the names in the same order as the scans\nExample: \n    Tanner Moore \n    Emily Hunt\n    Foster Holmes\n    Bailey Alexander\n    ...",anchor="w", font=self.small_font,fg=Gui.palette.get("lighttext"),justify="left")
		name_inst.pack(fill="both")
		name_inst.bind("<Configure>",lambda e:name_inst.configure(wraplength=name_inst.winfo_width()))
		
		self.mark_frame = tkinter.Frame(self.root,bg=Gui.palette.get("bg"))
		self.mark_frame.grid(row=2, column=1,pady=(10,10),padx=(0,10),sticky="ew")
		self.mark_btn=tkinter.Button(self.mark_frame, text="Continue ►", height = 4, width = 20,borderwidth=3, command=self.inputs,state=tkinter.DISABLED,cursor="X_cursor")#

		self.mark_btn.pack(padx=(0,5),side='left', fill="both", expand='yes')
		tkinter.Label(self.mark_frame,bg = Gui.palette.get("bg"), image=self.icon).pack(side='top')
		tkinter.Label(self.mark_frame, text=self.version, bg = Gui.palette.get("bg")).pack(side='bottom')

		self.root.wait_variable(self.next)

	def inputs(self):
		self.key_input=self.ans_key_box.get(1.0, "end-1c")
		self.names_input=self.stu_names_box.get(1.0, "end-1c")
		if self.filename == None:
			tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
			return
		elif not self.key_input or not self.names_input:
			if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered either the Student Names or Answer Key. \nAre you sure you want to continue?"):
				return
		self.next.set(True)

	def parameters(self,params):
		
		self.next.set(False)
		self.page = params.template
		self.destroy_children(self.canvas)
		self.destroy_children(self.right_frame)	
		
		img = PIL.Image.fromarray(params.template)
		self.pil = img.copy()
		img.thumbnail([600,855])
		thumb = PIL.ImageTk.PhotoImage(img)
		
		self.canvas.img = thumb
		self.canvas.create_image(0, 0, image=thumb, anchor=tkinter.NW)
		self.canvas.config(cursor="crosshair")

		self.box_frame = tkinter.LabelFrame(self.right_frame,text="Select the question area", relief="flat", labelanchor="n",fg=Gui.palette.get("lighttext"),bg=Gui.palette.get("frame"),bd=0,highlightthickness=0) #Hack to get nic border spacing
		self.box_frame.grid(row=0,pady=10,padx=10,sticky="nsew")
		self.box_frame.rowconfigure(index=0,weight=1)
		self.box_frame.columnconfigure(index=0,weight=1)

		self.file_btn.config(text="Choose another file", command=lambda: params.reset(self))

		self.box_canvas = tkinter.Canvas(self.box_frame, bd=0 ,bg=Gui.palette.get("frame"), highlightthickness=0, relief='ridge')#,width=339,height=445)
		
		self.sel_anim_cnvs = tkinter.Canvas(self.box_frame, bg=Gui.palette.get("frame"), highlightthickness=0, bd=0,relief='ridge')#,width=321,height = 431,)
		self.sel_anim_cnvs.grid(row=0,sticky="nsew") 
		self.sel_anim_cnvs.create_image(175,215,image = self.sel_img, anchor=tkinter.CENTER)

		self.hbar=tkinter.Scrollbar(self.box_frame,orient=tkinter.HORIZONTAL,width=12,bd=0,relief=tkinter.FLAT)
		self.vbar=tkinter.Scrollbar(self.box_frame,orient=tkinter.VERTICAL,width=12,bd=0,relief=tkinter.FLAT)
		self.hbar.config(command=self.box_canvas.xview)
		self.vbar.config(command=self.box_canvas.yview)
	
		self.q_rect = self.Rectangle()
		self.q_rect.rect = self.canvas.create_rectangle(0,0,0,0, dash=(50,), fill='', width=1, outline=Gui.palette.get("frame"))
		self.canvas.bind('<Button-1>', self._q_mouse_posn)
		self.canvas.bind('<B1-Motion>', self._q_sel_rect)
		self.canvas.bind('<ButtonRelease-1>', self.q_area) 

		self.box_rect = self.Rectangle()
		self.box_rect.rect = self.box_canvas.create_rectangle(0,0,0,0,outline=Gui.palette.get("frame"),fill=Gui.palette.get("frame"))
		#self.listener = pynput.mouse.Listener(on_scroll=self.on_scroll)
		self.box_canvas.bind('<Button-1>', self._box_mouse_posn)
		self.box_canvas.bind('<B1-Motion>', self._box_sel_rect)
		self.box_canvas.bind('<MouseWheel>', self.vscroll)
		self.box_canvas.bind('<Shift-MouseWheel>', self.hscroll)

		self.box_canvas.bind('<ButtonRelease-1>', lambda _: self.mark_btn.config(state=tkinter.ACTIVE,cursor="hand2")) 		

		self.mark_btn.configure(text="Mark Exams", state=tkinter.DISABLED, command=lambda: params.load_selection_boxes(self),cursor="X_cursor")
		
		self.anim_sel_box = self.sel_anim_cnvs.create_rectangle(0,0,0,0,dash=(50,), fill='', width=1, outline="#ffffff")
		self.sel_anim_cnvs.after(100,self.selection_animation)

		self.root.wait_variable(self.next)

	def vscroll(self,event):
		self.box_canvas.yview_scroll(-1 * (event.delta // 120), "units")
	
	def hscroll(self,event):
		self.box_canvas.xview_scroll(-1 * (event.delta // 120), "units")

	def marking(self,queue):
		
		self.destroy_children(self.root)
		self.corrections_frame = tkinter.Frame(self.root,bd=0,bg=Gui.palette.get("frame"))
		self.corrections_frame.grid(row=0,column=1, pady=10,padx=10,sticky="nsew")
		self.corrections_frame.columnconfigure(index=0,weight=1)
		self.corrections_frame.rowconfigure(index=0,weight=1,minsize=328)
		self.anim_frame = tkinter.Frame(self.corrections_frame,bd=0,bg=Gui.palette.get("frame"))
		self.anim_frame.grid(row=0,rowspan=3)

		self.progress_frame = tkinter.Frame(self.root)
		self.progress_frame.grid(row=1,column=1)
		self.proc_canvas = tkinter.Canvas(self.progress_frame,relief='ridge',bg=Gui.palette.get("bg"), highlightthickness=0)
		self.proc_canvas.pack()
		self.panels = []
		self.prog_size =(max(68,min(100,round(900/len(self.thumbs))))-4,round(1.41*max(68,(min(100,900/len(self.thumbs))))))
		for img, _ in self.thumbs:
			img.thumbnail(self.prog_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			panel = tkinter.Label(self.proc_canvas,bd=5)
			panel.pack(padx=5,side="left")
			panel.config(image=thumb)
			panel.image = thumb
			self.panels.append(panel)
			self.canvas.update()
		self.make_anim_boxes(self.anim_frame)
		self.animate_page(queue)


	def enter_corrections(self,image: PIL):
		self.next.set(False)
		correction_image = PIL.ImageTk.PhotoImage(image = image)
		self.correction_image_label.config(image=correction_image)
		self.correction_image_label.grid()
		self.corrections_frame.wait_variable(self.next)

	def completed_page_panels(self,student):
		if all(student.responses):
			img = student.pil_output.resize(self.prog_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			self.panels[student.index].config(image=thumb, bd=5, bg=Gui.palette.get("lightgreen"))
			self.panels[student.index].image = thumb
			self.panels[student.index].update()
		else:
			x, y = self.prog_size
			temp,_ = self.thumbs[student.index].copy()
			temp.paste(self.frames[-1],[x//2-16,y//2-15],self.frames[-1])
			thumb = PIL.ImageTk.PhotoImage(temp)
			self.panels[student.index].config(image=thumb)
			self.panels[student.index].image = thumb
			self.panels[student.index].update()

	def create_corrections_gui(self,choices: int):
		"""Brings up a GUI to manually choose the student's response"""	
		self.anim_bool.set(False)

		self.correction_image_label = tkinter.Label(self.corrections_frame,bd=0,bg=Gui.palette.get("frame"))
		self.correction_image_label.grid(pady="10",padx="10",row=0,column=0,sticky="ew")
		self.correction_buttons_frame=tkinter.Frame(self.corrections_frame,bg=Gui.palette.get("frame"))
		self.correction_buttons_frame.grid(padx="5", row=1, sticky="nsew")

		for i in range(choices):
			button=tkinter.Button(self.correction_buttons_frame, text=chr(i+65),cursor="hand2",command= lambda r=chr(i+65): self.button_cmd(r))
			button.grid(padx=(5), pady=(0,10),column=i,row=1, sticky="NSEW")
			self.correction_buttons_frame.columnconfigure(index=i,weight=1)


		unclear_button=tkinter.Button(self.correction_buttons_frame, text="Unclear",cursor="hand2",command= lambda : self.button_cmd("Unclear"))
		unclear_button.grid(padx=(5), pady=(0,10),row=2,column=0,columnspan=choices//2, sticky="NSEW")
		blank_button = tkinter.Button(self.correction_buttons_frame, text="Blank",cursor="hand2", command= lambda: self.button_cmd("Blank"))
		blank_button.grid(padx=(5), pady=(0,10),row=2,column=2,columnspan=choices//2, sticky="NSEW")
		self.next.set(True)

	def complete(self,students):
		self.destroy_children(self.root)
		self.canvas_frame = tkinter.Frame(self.root,bg=Gui.palette.get("frame"),bd=0, highlightthickness=0, relief='ridge')
		self.canvas_frame.pack(padx="10", pady="10", side="right", fill="both")
		self.canvas_frame.propagate(False)
		tkinter.Label(self.root, bg=Gui.palette.get("bg"), fg=Gui.palette.get("lighttext"), wraplength=300, text=f"Finished \n The results have been saved in \n {self.path}").pack(pady=20,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open results folder", command=lambda:os.startfile(self.path),cursor="hand2").pack(pady=5, padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open marked pdf", command=lambda:os.startfile(f"{self.path}\\ChilliMark-{self.basename}.pdf"),cursor="hand2").pack(pady=5,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open stats", command=lambda:os.startfile(f"{self.path}\\{self.basename}.csv") ,cursor="hand2").pack(pady=5,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Mark Another Exam", command=self.root.destroy,cursor="hand2").pack(pady=5,padx =(10,0), fill="both")
		tkinter.Label(self.root, bg=Gui.palette.get("bg"), fg=Gui.palette.get("lighttext"), wraplength=350,font=self.mid_font,text="ChilliMark is developed by a solo dev. \n It is free to use by individual teachers. \n A watermark free version is available for $2 on Buy me a Coffee. \n If your school uses this as a matter of policy, please ask them to purchase the commercial copy.").pack(pady=5,padx =(10,0), fill="both")
		tkinter.Button(self.root, text="Buy me a Coffee ☕", command = lambda:webbrowser.open("buymeacoffee.com/jumplogic/e/349532"), cursor = "hand2",).pack(side="bottom",pady=5,padx =(10,0), fill="both")
		#tkinter.Label("Buy Chilli Commecial")
		
		tkinter.Label(self.root, bg=Gui.palette.get("bg"), image=self.icon).pack(side='bottom')
		tkinter.Label(self.root, text=self.version, bg = Gui.palette.get("bg")).pack(side='bottom')
		
		
		self.canvas = tkinter.Canvas(self.canvas_frame, bg=Gui.palette.get("frame"), bd=0, highlightthickness=0, relief='ridge')#height=705, width=520, 
		self.canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")
		self.canvas.propagate(False)
		imgs = [student.pil_output for student in students]

		thumbs= []
		for img in imgs:
			pil = img.copy()
			pil.thumbnail(self.thumb_size)
			thumb = PIL.ImageTk.PhotoImage(pil)
			thumbs.append([pil,thumb])
		self.thumb_grid(None,thumbs,imgs)
		self.root.wait_window()


	#Selection boxes mouse event functions from selection boxes page

	def _q_mouse_posn(self,event):
		self.q_rect.x1, self.q_rect.y1 = event.x, event.y

	def _box_mouse_posn(self,event):
		self.box_rect.x1, self.box_rect.y1 = event.x, event.y
		self.box_rect.x1true, self.box_rect.y1true = self.box_canvas.canvasx(event.x), self.box_canvas.canvasy(event.y)

	def _q_sel_rect(self,event):
		self.q_rect.x2, self.q_rect.y2 = event.x, event.y
		self.canvas.coords(self.q_rect.rect, self.q_rect.x1, self.q_rect.y1, self.q_rect.x2, self.q_rect.y2)  # Update selection rect.

	def _box_sel_rect(self,event):
		self.box_rect.x2, self.box_rect.y2 = event.x, event.y
		self.box_rect.x2true, self.box_rect.y2true = self.box_canvas.canvasx(event.x), self.box_canvas.canvasy(event.y)
		self.box_canvas.coords(self.box_rect.rect, 0,0,0,0)  # Update selection rect.
		self.box_rect.rect = self.box_canvas.create_rectangle(self.box_rect.x1true, self.box_rect.y1true, self.box_rect.x2true, self.box_rect.y2true, dash=(50,), fill='', width=1, outline=Gui.palette.get("frame"))

	def q_area(self,event):
		"""Gets the question_area. An prepares the GUI for the boc selection. These coordinates are pass to the marking kernal
		Note turned into a list since ultimately the Images are arrays and croppings is sone by slicing the array.
		So crop "function" alway define by 4 variables"""
		#Cleans up value of corners
		x1 = max(0,(min(self.q_rect.x1,self.q_rect.x2)))
		x2 = min(600,(max(self.q_rect.x1,self.q_rect.x2)))
		y1 = max(0,(min(self.q_rect.y1,self.q_rect.y2)))
		y2 = min(855,(max(self.q_rect.y1,self.q_rect.y2)))

		self.y1 = round(y1*8)
		self.x1 = round(x1*8)
		self.y2 = round(y2*8)
		self.x2 = round(x2*8) 

		self.image = PIL.ImageTk.PhotoImage(self.pil.crop([self.x1,self.y1,self.x2,self.y2]))
		self.sel_anim_cnvs.destroy()
		self.box_canvas.create_image(0, 0, image=self.image, anchor=tkinter.NW)
		self.box_canvas.config(cursor="crosshair",scrollregion=[0,0,self.x2-self.x1,self.y2-self.y1], xscrollcommand = self.hbar.set, yscrollcommand = self.vbar.set)
		self.box_canvas.grid(pady=(10,0),row=0,sticky="nsew")
		self.vbar.grid(row=0,column=1,sticky="ns",pady=(10,0))
		self.hbar.grid(row=1,column=0,sticky="ew")
		self.box_frame.config(text="Now select one empty box")



	#File handling section

	def open_file(self,file: str):
		if not file:
			return
		self.thumbs=[]
		self.filename = file.strip("{,}")
		self.pdf.destroy()
		#self.canvas_frame.children.clear()
		self.canvas = tkinter.Canvas(self.canvas_frame, bg=Gui.palette.get("frame"), height=848, width=600, bd=0, highlightthickness=0, relief='ridge')
		self.canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")
		doc = pymupdf.open(self.filename)
		self.grid_size = math.isqrt(len(doc))+1*(math.sqrt(len(doc))!=math.isqrt(len(doc)))
		self.thumb_size = (600//self.grid_size-self.grid_size,848//self.grid_size-self.grid_size)
		imgs = []
		for page in doc:
			pix = page.get_pixmap(dpi=72, colorspace="RGB")
			img = PIL.Image.frombuffer("RGB", [pix.width, pix.height], pix.samples) 
			imgs.append(img.copy().resize((600,848)))
			img.thumbnail(self.thumb_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			self.thumbs.append([img,thumb])
		self.thumb_grid(None,self.thumbs,imgs)
		self.mark_btn.config(state=tkinter.ACTIVE,cursor="hand2")

	def choose_file(self,event=None):
		filename = tkinter.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
		if filename == "":
			return
		self.filename = filename
		self.open_file(self.filename)

	#This section deals with the preview thumbsnails. 
	#Future Addtions:
	# Offer a text box for each student name
	# Overlay the names of the students into the UI as it is enter in the text box
	# Allow to loop through student preview
	# Allow to reorder students

	def img_preview(self,event=None,index=None,imgs=None):
		"""Focus on one page"""

		hidden = self.canvas.grid_slaves()
		list(map(operator.methodcaller("grid_remove"), hidden))
		preview=tkinter.Label(self.canvas,bd=0)
		
		def set_img(index,imgs=imgs):
			temp = imgs[index].copy()
			temp.thumbnail([600,855])
			preview_img = PIL.ImageTk.PhotoImage(temp)
			preview.config(image = preview_img)
			preview.image = preview_img
			preview.grid()
			preview.focus()
	
			preview.bind("<Button-1>",reload)
			preview.bind("<Right>",lambda e:cycle_next_image(1,index))
			preview.bind("<Left>",lambda e:cycle_next_image(-1,index))
			preview.bind("<MouseWheel>",lambda e:cycle_next_image(e.delta,index))
			preview.bind("<Shift-MouseWheel>",lambda e:cycle_next_image(e.delta,index))

		def reload(event):
			preview.destroy()
			list(map(operator.methodcaller("grid"), hidden))

		def cycle_next_image(delta,index,imgs=imgs,):
			delta=delta//(abs(delta))
			if index+delta <0:
				index = len(imgs)-1
			elif index+delta==len(imgs):
				index=0
			else:
				index = index+delta
			set_img(index)

		set_img(index)
		
	def thumb_grid(self,event=None,thumbs=None,imgs=None):
		self.destroy_children(self.canvas)
		for i, item in enumerate(thumbs):
			_,thumb = item
			panel = tkinter.Label(self.canvas,image=thumb,cursor="hand2")
			panel.grid(row=i//self.grid_size, column=i%self.grid_size)
			panel.image = thumb
			panel.bind("<Button-1>",lambda e=None,index=i:self.img_preview(e,index=index,imgs=imgs))
			self.canvas.update()

	#GUI animations. 
	# Future Additions. Single Box selections and transitions 
	def selection_animation(self):
		"""Causes the dashed selection box to grow and shrink"""

		x = 50*math.sin(time.time())
		self.sel_anim_cnvs.coords(self.anim_sel_box, 75,155,225+x,310+x)
		self.sel_anim_cnvs.after(33,self.selection_animation)
	
	
	def	make_anim_boxes(self,frame):
		"""Initiates rounded box objects. The boxes are put into a random list then calls the animation functions.
		The first set up some parameters then initiates animation before staging the next animation function.
		At the end of the second the box places itself back into a random position in the list ensuring random order"""

		boxes = []
		wide = self.corrections_frame.winfo_width()//90 -1
		for i in range(wide*wide//2):
			box = self.Anim_Box(frame,i,wide)
			box.round()
			boxes.append(box)	
		random.shuffle(boxes)
		self.animate_box(boxes)

	def animate_box(self,boxes):
		"""Calculates a starting position for the animation loop. Then calls the actual animation loop for that box.
		THen prepares animation for next box."""

		box = boxes[-1]
		box.time=time.time()
		box.start=math.degrees(time.time())%360
		box.canvas.itemconfig(box.cover,start = box.start)
		box.swipe(boxes)
		boxes.pop(-1)
		try:
			self.corrections_frame.after(200,lambda:self.animate_box(boxes))
		except:
			return

	def animate_page(self,queue):
		"""Recursivly calls the multiprocessor queue to check progress of each page and updates the frame. 
		There are 16 steps to the animation."""
	
		if not self.anim_bool.get():
			return
		try: #since this is in a different thread it fails on last one
			tup=queue.get(block=False)
			index, frame = tup
			temp,_ = self.thumbs[index].copy()
			x, y = self.prog_size
			temp.paste(self.frames[frame],[x//2-16,y//2-15],self.frames[frame])
			temp = PIL.ImageTk.PhotoImage(temp)
			self.panels[index].config(image=temp)
			self.panels[index].image = temp
		except:
			pass
		self.progress_frame.after(100,lambda: self.animate_page(queue))

	#Minor functions in the GUI
	def destroy_children(self,parent):
		for child in parent.winfo_children():
			if child.winfo_children():
				self.destroy_children(child)
			child.destroy()

	def button_cmd(self,response):
		self.response.set(response)
		self.next.set(True)

	def	bad_box(self):
		tkinter.messagebox.showinfo(message="Please try selecting the box again")

def get_path(filename):
	if hasattr(sys, "_MEIPASS"):
		return os.path.join(sys._MEIPASS, filename)
	else:
		return filename

if __name__ == "__main__":
	pass