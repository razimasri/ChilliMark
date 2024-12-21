import multiprocessing
import multiprocessing.pool
import multiprocessing.process
import threading
import numpy
import cv2
import time
import math
import pynput
import pymupdf
import csv
import os
import PIL
import PIL.Image
import PIL.ImageTk
import operator
import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tksvg
import tkinterdnd2
import tkinterdnd2.TkinterDnD
import ctypes
import random

#images are set to 4800 vs 6784.
#This is close to the A4 Ratio and the 600dpi scan
#based on 4800 is 2^6,3^1,5^2 and 6784 2^7,53

class Question:
	
	colour = {"red": (0,0,200),"yellow": (0,170,250),"green": (0,170,0)}
	
	class Box:
		def __init__(self,xy,i):
			self.xy = xy
			self.letter = chr(i+65)
			self.colour = None
			self.bool = False
	
		def fill(self,params,thresh):
			contour = params.inner + self.xy
			x,y,w,h= cv2.boundingRect(contour)
			temp = thresh[y:y+h,x:x+w]
			mask = numpy.zeros(temp.shape, dtype="uint8") 
			mask = cv2.bitwise_and(temp, temp, mask)
			if cv2.countNonZero(mask) > params.fill_limit:
				self.bool = True
				self.colour = "yellow"

	def __init__(self,r):
		self.response = "Blank"
		self.boxes = []
		self.response_box = None
		self.number = r
	
	def get_response(self):
		for box in self.boxes:
			if box.bool:
				self.response=box.letter
				self.response_box=box
				box.colour = "red"
	
	def annotate(self,params,image,colour=colour): 
		#the logic of the two annotate functions is slightly different. 
		# This time we do no want to skip unclear. 
		# We are also avoiding a later RGB colour flip
		if self.response =="Blank":
			return
		for box in self.boxes:
			if box.bool:
				cv2.drawContours(image, [box.xy+params.outer], -1, colour.get(box.colour), 5,cv2.LINE_AA)

class Gui:	

	palette = { 
		"darktext" : "#280e0d",
		"frame" : "#571622",
		"whitespace" : "#e3e5ef",
		"lighttext" : "#e3e5ef",
		"bg": "#8c1529",
		"button": "#b1a1a4"}
	
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
		
		self.version = ["v1.0","Adjuma"] #["v0.9","Capsaicin"]

		self.icon = tksvg.SvgImage(file="icons\iconwhite.svg", scaletoheight = 128 )
		self.sel_img = tksvg.SvgImage(file="icons\selection.svg")
		self.pdf_icon = tksvg.SvgImage(file="icons\pdf.svg", scaletoheight = 256 )
		self.frames = [PIL.Image.open(f"icons\\animations\\pageprocess\\{file}") for file in os.listdir("icons\\animations\\pageprocess")]
		self.root.tk.call('wm', 'iconphoto', self.root._w, PIL.ImageTk.PhotoImage(file="icons\Icon16.ico"))

		self.root.title("Chilli Marker")
		self.root.configure(borderwidth=2,background=Gui.palette.get("bg"))
		self.root.geometry("1020x893")
		self.root.resizable(False, False)

		self.default_font = tkinter.font.nametofont("TkDefaultFont")
		self.small_font=self.default_font.copy()
		self.default_font.configure(size=14, weight="bold")
		self.small_font.configure(size=10)
		self.root.option_add("*Font", self.default_font)
		self.root.columnconfigure(index=1, weight=1)
		self.root.rowconfigure(index=1, weight=2)

		self.next = tkinter.BooleanVar(value=False)
		


	def home(self):
		self.destroy_children(self.root)


		#Drag and Drop Files
		self.root.drop_target_register(tkinterdnd2.DND_FILES)
		self.root.dnd_bind('<<Drop>>', lambda event: self.open_file(event.data))

		self.canvas_frame = tkinter.Frame(self.root,bg=Gui.palette.get("frame"), height=868, width=622, bd=0, highlightthickness=0, relief='ridge', cursor="hand2")
		self.canvas_frame.grid(padx=10, pady=10, column=0,row=0,rowspan=3,sticky="nsew")
		self.canvas_frame.columnconfigure(index=0, weight=1,minsize=622)
		self.canvas_frame.rowconfigure(index=0, weight=1,minsize=868)
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
		self.mark_btn=tkinter.Button(self.mark_frame, text="Continue ►", height = 4, width = 20,borderwidth=3, command=lambda:load_inputs(self),state=tkinter.DISABLED,cursor="X_cursor")#

		self.mark_btn.pack(padx=(0,5),side='left', fill="both", expand='yes')
		tkinter.Label(self.mark_frame,bg = Gui.palette.get("bg"), image=self.icon).pack(side='top')
		tkinter.Label(self.mark_frame, text=self.version, bg = Gui.palette.get("bg")).pack(side='bottom')

	def parameters(self,params):
		
		self.next.set(False)
		self.page = params.template
		self.destroy_children(self.canvas)
		self.destroy_children(self.right_frame)	
		
		img = PIL.Image.fromarray(params.template)
		self.pil = img.copy()
		img.thumbnail([600,848])
		thumb = PIL.ImageTk.PhotoImage(img)
		
		self.canvas.img = thumb
		self.canvas.create_image(0, 0, image=thumb, anchor=tkinter.NW)
		self.canvas.config(cursor="crosshair")

		self.box_frame = tkinter.LabelFrame(self.right_frame,text="Select the question area", relief="flat", labelanchor="n",fg=Gui.palette.get("lighttext"),bg=Gui.palette.get("frame"),bd=0,highlightthickness=0) #Hack to get nic border spacing
		self.box_frame.grid(row=0,pady=10,padx=10,sticky="nsew")
		self.box_frame.rowconfigure(index=0,weight=1)
		self.box_frame.columnconfigure(index=0,weight=1)

		def back():
			self.home()
			self.choose_file()

		self.file_btn.config(text="Choose another file", command=back)

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
		self.listener = pynput.mouse.Listener(on_scroll=self.on_scroll)
		self.box_canvas.bind('<Button-1>', self._box_mouse_posn)
		self.box_canvas.bind('<B1-Motion>', self._box_sel_rect)
		self.box_canvas.bind('<Enter>', self.start_listener)
		self.box_canvas.bind('<Leave>', self.stop_listener)
		self.box_canvas.bind('<ButtonRelease-1>', lambda _: self.mark_btn.config(state=tkinter.ACTIVE,cursor="hand2")) 		

		self.mark_btn.configure(text="Mark Exams", state=tkinter.DISABLED, command=lambda: params.load_selection_boxes(self),cursor="X_cursor")
		
		self.anim_sel_box = self.sel_anim_cnvs.create_rectangle(0,0,0,0,dash=(50,), fill='', width=1, outline="#ffffff")
		self.sel_anim_cnvs.after(100,self.selection_animation)

	def marking(self):
		self.destroy_children(self.root)
		self.corrections_frame = tkinter.Frame(self.root,bd=0,bg=Gui.palette.get("frame"))
		self.corrections_frame.grid(row=0,column=1, pady=10,padx=10,sticky="nsew")
		self.corrections_frame.columnconfigure(index=0,weight=1)
		self.corrections_frame.rowconfigure(index=0,weight=1,minsize=328)
		self.anim_frame = tkinter.Frame(self.corrections_frame,bd=0,bg=Gui.palette.get("frame"))
		self.anim_frame.grid(row=0,rowspan=3)

		self.progress_frame = tkinter.Frame(self.root)
		self.progress_frame.grid(row=1,column=1)
		self.proc_canvas = tkinter.Canvas(self.progress_frame,relief='ridge')
		self.proc_canvas.pack()
		self.panels = []
		self.prog_size =(max(68,min(100,round(900/len(self.thumbs))))-4,round(1.41*max(68,(min(100,900/len(self.thumbs))))))
		for img, _ in self.thumbs:

			img.thumbnail(self.prog_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			panel = tkinter.Label(self.proc_canvas,bd=2)
			panel.pack(side="left")
			panel.config(image=thumb)
			panel.image = thumb
			self.panels.append(panel)
			self.canvas.update()
		self.make_anim_boxes(self.anim_frame)

	def enter_corrections(self,image: PIL):
		self.next.set(False)
		# for item in self.buttons:
		# 	button,response = item
		# 	button.config(command=lambda response=response: self.button_cmd(response))
		correction_image = PIL.ImageTk.PhotoImage(image = image)
		self.correction_image_label.config(image=correction_image)
		self.correction_image_label.grid()
		self.corrections_frame.wait_variable(self.next)

	def completed_page_panels(self,student):
		if all(student.responses):
			img = student.pil_output.resize(self.prog_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			self.panels[student.index].config(image=thumb)
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
		self.next.set(False)


		self.correction_image_label = tkinter.Label(self.corrections_frame,bd=0,bg=Gui.palette.get("frame"))
		self.correction_image_label.grid(pady="10",padx="10",row=0,column=0,sticky="ew")
		self.correction_buttons_frame=tkinter.Frame(self.corrections_frame,bg=Gui.palette.get("frame"))
		self.correction_buttons_frame.grid(padx="5", row=1, sticky="nsew")
		#self.buttons= []
		for i in range(choices):
			button=tkinter.Button(self.correction_buttons_frame, text=chr(i+65),cursor="hand2",command= lambda r=chr(i+65): self.button_cmd(r))
			button.grid(padx=(5), pady=(0,10),column=i,row=1, sticky="NSEW")
			self.correction_buttons_frame.columnconfigure(index=i,weight=1)
			#self.buttons.append([button, chr(i+65)])

		unclear_button=tkinter.Button(self.correction_buttons_frame, text="Unclear",cursor="hand2",command= lambda : self.button_cmd("Unclear"))
		unclear_button.grid(padx=(5), pady=(0,10),row=2,column=0,columnspan=choices//2, sticky="NSEW")
		blank_button = tkinter.Button(self.correction_buttons_frame, text="Blank",cursor="hand2", command= lambda: self.button_cmd("Blank"))
		blank_button.grid(padx=(5), pady=(0,10),row=2,column=2,columnspan=choices//2, sticky="NSEW")
		#self.buttons.append([unclear_button, "unclear"])
		#self.buttons.append([blank_button, "Blank"])
		
		#for some unknow reason command= lambda : self.button_cmd("Unclear")) was executing immediately. So packed into a list and reassign on correction image loading 

	def complete(self,students):
		self.destroy_children(self.root)
		self.canvas_frame = tkinter.Frame(self.root,bg=Gui.palette.get("frame"),bd=0, highlightthickness=0, relief='ridge')
		self.canvas_frame.pack(padx="10", pady="10", side="right", fill="both")
		self.canvas_frame.propagate(False)
		path_to_save = self.filename.replace(".pdf","")
		basename = os.path.basename(self.filename)
		basename = basename.replace(".pdf","")
		tkinter.Label(self.root, bg=Gui.palette.get("bg"), fg=Gui.palette.get("lighttext"), wraplength=300, text=f"Finished \n The results have been saved in \n {path_to_save}").pack(pady=20,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open results folder", command=lambda:os.startfile(path_to_save),cursor="hand2").pack(pady=5, padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open marked pdf", command=lambda:os.startfile(f"{path_to_save}\\ChilliMark-{basename}.pdf",cursor="hand2")).pack(pady=5,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Open stats", command=lambda:os.startfile(f"{path_to_save}\\{basename}.csv"),cursor="hand2").pack(pady=5,padx =(10,0), fill="both")
		tkinter.Button(self.root,text="Mark Another Exam", command=self.home,cursor="hand2").pack(pady=5,padx =(10,0), fill="both")
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

	def	make_anim_boxes(self,frame):
		self.anim_bool = tkinter.BooleanVar(value=True)
		boxes = []
		wide = self.corrections_frame.winfo_width()//90 -1
		for i in range(wide*wide//2):
			box = self.Anim_Box(frame,i,wide)
			box.round()
			boxes.append(box)	
		random.shuffle(boxes)
		self.animate_box(boxes)

	def animate_box(self,boxes):
		
		box = boxes[-1]
		box.time=time.time()
		box.start=math.degrees(time.time())%360
		box.canvas.itemconfig(box.cover,start = box.start)
		box.swipe(boxes)
		boxes.pop(-1)
		self.corrections_frame.after(200,lambda:self.animate_box(boxes))
	
	def animate_page(self,queue):
		if not self.anim_bool.get():
			return
		try: #since this is in a different thread it fails on last one
			tup=queue.get(block=False)
			index, frame = tup
			temp,_ = self.thumbs[index].copy()
			x, y = self.prog_size
			temp.paste(self.frames[frame],[x//2-16,y//2-15],self.frames[frame])
			thumb = PIL.ImageTk.PhotoImage(temp)
			self.panels[index].config(image=thumb)
			self.panels[index].image = thumb
		except:
			pass
		self.progress_frame.after(100,lambda: self.animate_page(queue))

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
		
		#Cleans up value of corners
		x1 = max(0,(min(self.q_rect.x1,self.q_rect.x2)))
		x2 = min(600,(max(self.q_rect.x1,self.q_rect.x2)))
		y1 = max(0,(min(self.q_rect.y1,self.q_rect.y2)))
		y2 = min(848,(max(self.q_rect.y1,self.q_rect.y2)))

		self.y1 = round(y1//8)
		self.x1 = round(x1//8)
		self.y2 = round(y2//8)
		self.x2 = round(x2//8) 

		self.image = PIL.ImageTk.PhotoImage(self.pil.crop([self.x1,self.y1,self.x2,self.y2]))
		self.sel_anim_cnvs.destroy()
		self.box_canvas.create_image(0, 0, image=self.image, anchor=tkinter.NW)
		self.box_canvas.config(cursor="crosshair",scrollregion=[0,0,self.x2-self.x1,self.y2-self.y1], xscrollcommand = self.hbar.set, yscrollcommand = self.vbar.set)
		self.box_canvas.grid(pady=(10,0),row=0,sticky="nsew")
		self.vbar.grid(row=0,column=1,sticky="ns",pady=(10,0))
		self.hbar.grid(row=1,column=0,sticky="ew")
		self.box_frame.config(text="Now select one empty box")

	def start_listener(self,event):
		if not self.listener.running:
			self.listener = pynput.mouse.Listener(on_scroll=self.on_scroll)
			self.listener.start()

	def stop_listener(self,event):
		if self.listener.running:
			self.listener.stop()

	def on_scroll(self,x, y, dx, dy):
		while abs(dy)>5:
			dy //= 5
		while abs(dx>5):
			dx //=5
		self.box_canvas.xview_scroll(dx, "units")
		self.box_canvas.yview_scroll(-dy, "units")

	def selection_animation(self):
		x = 50*math.sin(time.time())
		self.sel_anim_cnvs.coords(self.anim_sel_box, 75,155,225+x,310+x)
		self.sel_anim_cnvs.after(33,self.selection_animation)

	def img_preview(self,event=None,index=None,imgs=None):
		hidden = self.canvas.grid_slaves()
		list(map(operator.methodcaller("grid_remove"), hidden))
		temp = imgs[index].copy()
		temp.thumbnail([600,848])
		preview = PIL.ImageTk.PhotoImage(temp)
		panel=tkinter.Label(self.canvas,image = preview,bd=0)
		panel.image = preview
		panel.grid()
		def reload(event):
			panel.destroy()
			list(map(operator.methodcaller("grid"), hidden)) 
		panel.bind("<Button-1>",reload)

	def thumb_grid(self,event=None,thumbs=None,imgs=None):
		self.destroy_children(self.canvas)
		for i, item in enumerate(thumbs):
			_,thumb = item
			panel = tkinter.Label(self.canvas,image=thumb,cursor="hand2")
			panel.grid(row=i//self.grid_size, column=i%self.grid_size)
			panel.image = thumb
			panel.bind("<Button-1>",lambda e=None,index=i:self.img_preview(e,index=index,imgs=imgs))
			self.canvas.update()

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

	def destroy_children(self,parent):
		for child in parent.winfo_children():
			if child.winfo_children():
				self.destroy_children(child)
			child.destroy()

	def button_cmd(self,response):
		self.response.set(response)
		self.correction_image_label.grid_remove()
		self.next.set(True)

class Parameters:
	def __init__(self,rect,key,names,template):
		self.rect = rect
		self.y1	= 0
		self.x1	= 0
		self.y2 = 0
		self.x2 = 0
		self.box_y1	= 0
		self.box_x1	= 0
		self.box_y2 = 0
		self.box_x2 = 0
		self.outer = []
		self.inner = []
		self.h = 0
		self.w = 0
		self.text_shift = []
		self.font_size = 0 #maybe shift this to markup class
		self.fill_limit = 0
		self.set_key(key)
		self.template = template
		self.names = names

	def set_box(self,image):
		image = get_thresh(image[int(self.box_y1):int(self.box_y2),int(self.box_x1):int(self.box_x2)],blur=True)
		outer, _ = cv2.findContours(image,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		outer=outer[0]
		#if area(outer)
		percentage = abs(area(outer)-((self.box_y2-self.box_y1)*(self.box_x2-self.box_x1)))/area(outer)
		
		if percentage>100:
			raise Exception("Your selection does return a complete box")
		if percentage>0.35:
			print(percentage)
		
		
		outer = cv2.approxPolyDP(outer, 0.05*cv2.arcLength(outer, True), True)		
		x, y, w, h = cv2.boundingRect(outer)#not the most elegant
		image = cv2.bitwise_not(image)
		image = cv2.rectangle(image,(x,y),(x+w,y+h),0,w//6)
		image = image[y:y+h,x:x+w]
		inner, _ = cv2.findContours(image,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)	
		if len(inner)==0:
			return inner == False
		inner = inner[0]
		self.h = h
		self.w = w
		self.outer = outer-contour_center(outer)
		self.inner = inner-contour_center(inner)
		self.fill_limit = 5.5*math.sqrt(cv2.contourArea(self.inner))

	def set_markup_size(self):
		text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, 4, 4)[0]
		text_shift = [0,0]
		if text_size [1]>self.h*1.2:	
			self.font_size=3
			text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, self.font_size, 4)[0]
			text_shift[1] = -self.h
		else:
			self.font_size=4
			text_shift[1] = text_size[1]//2
		text_shift[0]=-text_size[0]//2
		self.text_shift = text_shift
	
	def set_key(self,key_input):
		"""Formats the user inputs for use. Adds answer key to Parameters and names to students"""
		self.key={}
		if key_input:
			key_input = "".join(x for x in key_input if x.isalpha())
			key_input = key_input.upper()
		for i, ans in enumerate(key_input):    
			self.key[i]=ans
		if key_input:
			self.score_size = cv2.getTextSize(f"Score =  {len(self.key)} / {len(self.key)}",cv2.FONT_HERSHEY_SIMPLEX, 5,7)[0]

	def load_selection_boxes(self, gui: Gui):
		"""Loads the selection box co-ordinates from gui"""
		
		self.y1 = int(gui.y1)
		self.x1 = int(gui.x1)
		self.y2 = int(gui.y2)
		self.x2 = int(gui.x2)

		self.box_y1 = int(gui.box_rect.y1true+self.y1)
		self.box_x1 = int(gui.box_rect.x1true+self.x1)
		self.box_y2 = int(gui.box_rect.y2true+self.y1)
		self.box_x2 = int(gui.box_rect.x2true+self.x1)

		try: 
			self.set_box(self.template)
			self.set_markup_size()
		except:
			tkinter.messagebox.showinfo(message="Please try selecting the box again")
			return
		return core(gui,self)

class Student:

	colour = {"red": (200,0,0),"yellow": (250,170,0),"green": (0,170,0)}

	def __init__(self,filename,i,params,queue):
		self.name: str = f"Student {i+1:0{params.num}}"
		self.index: int = i 
		self.scan = None
		self.responses = None
		self.questions: list = []
		self.incomplete: list = []
		self.score: int = 0
		self.queue = queue
		self.frame = 0
		self.process_page(filename,i,params)
		self.mark(params)

	def animation_step(self):
		self.queue.put( [self.index,self.frame])
		self.frame+= 1
	
	def process_page(self,filename: str,i: int,params: Parameters):
		#doesn't seem to affect performance. can change it so that it animate in chunks of 4
		#or just have non-progress tied looping animations 
		self.animation_step() 
		doc = pymupdf.open(filename)
		self.animation_step()
		pix = doc[i].get_pixmap(dpi=600, colorspace="RGB")
		self.animation_step()
		image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
		self.animation_step()
		image,rect= rotation(image)
		self.animation_step()
		image= scale(image,rect,params)
		self.animation_step()
		self.scan=image
		self.animation_step()
		self.pil_original = PIL.Image.fromarray(self.scan)
		self.animation_step()

	def mark(self,params):
		"""Identifies the boxes, and if they have been filled. Then annotates the images"""
		self.animation_step()
		q_area = self.scan[params.y1:params.y2,params.x1:params.x2]
		self.animation_step()
		boxes = find_boxes(q_area,params)
		columns = sort_into_columns(boxes,params)
		sort_into_rows(boxes,params)
		self.animation_step()
		missing(columns,params)
		self.questions = find_questions(columns,params)
		find_responses(self,q_area,params)
		self.animation_step()
		self.responses = [question.response for question in self.questions]
		if params.key:
			self.add_markup(q_area,params)
		q_area = self.annotate(params,q_area)
		self.animation_step()
		self.scan[params.y1:params.y2,params.x1:params.x2] = q_area
		self.scan=cv2.putText(self.scan,self.name,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(255,255,255),25)
		self.animation_step()
		self.scan=cv2.putText(self.scan,self.name,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(0,0,0),10)
		self.scan = cv2.cvtColor(self.scan,cv2.COLOR_BGR2RGB)	
		self.animation_step()
		self.scan[256:512,4288:4544]=cv2.imread("icons\printmark.png")
		self.pil_output = PIL.Image.fromarray(self.scan[:,:,::-1])		
		self.animation_step()
		#dont know what the [:,:,::-1] is for
		return self

	def annotate(self,params,image,colour=colour):
		for question in self.questions:
			if question.response=="Blank" or not question.response:
				continue
			for box in question.boxes:
				if box.bool:
					cv2.drawContours(image, [box.xy+params.outer], -1, colour.get(box.colour), 5,cv2.LINE_AA)
		return image
	
	def add_markup(self,image,params,colour=colour.get("green")):
		for question in self.questions:
			if question.number>len(params.key)-1:
				break
			if question.response == params.key[question.number]:
				question.response_box.colour="green"
				self.score+=1
			x,y=question.boxes[ord(params.key[question.number])-65].xy
			text_y = y+params.text_shift[1]
			text_x = x+params.text_shift[0]
			cv2.putText(image,params.key[question.number], (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, params.font_size,(255,255,255),20,lineType=cv2.LINE_AA) 
			cv2.putText(image,params.key[question.number], (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, params.font_size,colour,7,lineType=cv2.LINE_AA) 
		if question.response:
			self.scan = cv2.putText(self.scan,f"Score = {self.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
			self.scan= cv2.putText(self.scan,f"Score = {self.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)		
		return image

def corrections(students: list, gui: Gui, params: Parameters):
	"""Looks through list of students responses with unclear answers,
	Brings up a gui with the question and asks the marker to assign the respose."""
	
	for student in students:
		gui.completed_page_panels(student)	
	gui.create_corrections_gui(len(students[0].questions[0].boxes))#get a nicer war to manage choices

	incomplete = [student for student in students if not all(student.responses)]

	for student in incomplete:
		for question in student.incomplete:
			centres = [box.xy for box in question.boxes]
			qx,qy = (centres[0][0]+centres[-1][0])//2, (centres[0][1]+centres[-1][1])//2
			x1 = qx-435+params.x1
			y1 = qy-155+params.y1
			x2 = qx+435+params.x1
			y2 = qy+158+params.y1
			unclear = student.pil_original.crop([x1,y1,x2,y2])
			gui.enter_corrections(unclear)
			#while not gui.next_correction.get():
				#continue
			question.response = gui.response.get()
			#print("coregui",gui.response.get())
			#print("student",question.response)
			if len(question.response)==1:
				question.boxes[ord(question.response)-65].colour = "red"
				question.boxes[ord(question.response)-65].bool = True
				question.response_box = question.boxes[ord(question.response)-65]
			student.responses[question.number]=question.response
			if params.key:
				if question.response == params.key[question.number]:
					question.response_box.colour="green"
					student.score+=1
			#Zgui.next.set(True)
		threading.Thread(target=correction_update, args=[student,gui,params]).start()

def correction_update(student: Student,gui: Gui,params:Parameters):
	q_area = student.scan[params.y1:params.y2,params.x1:params.x2]
	for question in student.incomplete:
		question.annotate(params,q_area)
	if params.key:
		student.scan = cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
		student.scan= cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)
	student.scan[params.y1:params.y2,params.x1:params.x2] = q_area
	student.pil_output = PIL.Image.fromarray(student.scan[:,:,::-1])
	try: #gui will have moved onto complete for final image if this was last
		gui.completed_page_panels(student)
	except:
		pass

def core(gui: Gui,params: Parameters):
	doc = pymupdf.open(gui.filename) #probably unecessary. remove after getting the returning of image correct
	params.num = len(doc)//10+1
	manager = multiprocessing.Manager()
	queue = manager.Queue()

	#creating tuples to pass to the parallel processing function since it cannot take the page object
	pages=[[gui.filename,i,params,queue] for i,_ in enumerate(doc)] 
	pool = multiprocessing.Pool(len(doc)) 
	students_async = pool.starmap_async(Student,pages)
	gui.marking()	


	def getting():
		students = students_async.get()
		corrections(students,gui,params)
		make_output(students,gui,params)
		gui.complete(students)

	get_thread = threading.Thread(target=getting)
	anim_thread = threading.Thread(target=lambda: gui.animate_page(queue), daemon=True)
	anim_thread.start()
	get_thread.start()

		


def load_inputs(gui):
	"""Select the question regions and an example box. 
	Multiple other important parameters are defined based on this"""
	
	key_input=gui.ans_key_box.get(1.0, "end-1c")
	names_input=gui.stu_names_box.get(1.0, "end-1c")
	if gui.filename == None:
		tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
		return
	elif not key_input or not names_input:
		if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered either the Student Names or Answer Key. \nAre you sure you want to continue?"):
			return

	doc = pymupdf.open(gui.filename)
	pix = doc[0].get_pixmap(dpi=600, colorspace="RGB")
	template = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
	template = cv2.resize(template,(4800,6784))
	template,rect = rotation(template)
	params = Parameters(rect,key_input,names_input,template)
	params.filename = gui.filename
	gui.parameters(params)


def largest_cnt(image:cv2.typing.MatLike) -> cv2.typing.MatLike:
	"""Find the largest contour on the page for use with alignment functions. 
	Note that it draws a border on the image to eliminate false contours from scan edges."""

	gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1] 
	thresh = cv2.rectangle(thresh,(0,0),(4800,6784),0,200)
	cnts,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	filtered = filter(lambda cnt: area(cnt)>4000000,cnts)
	sorted_cnts = sorted(filtered, key=area, reverse=True)
	largest = sorted_cnts[0]
	largest = cv2.approxPolyDP(largest, 0.01*cv2.arcLength(largest, True), True)
	return largest

def rotation(page: cv2.typing.MatLike) -> cv2.typing.MatLike:
	"""Assumes the largest contour is a rectangle. 
	Finds the rotation of largest rectangle and rotates the page based on that. 
	Also returns the largest rectangle for use in future scaling"""
	
	big=largest_cnt(page)
	rect = cv2.minAreaRect(big)
	if rect[2] > 45:
		angle = rect[2]-90
	else: 
		angle = rect[2]
	Matrix = cv2.getRotationMatrix2D((2400,3414),angle,1)
	rotated = cv2.warpAffine(page, Matrix, (4800, 6784))
	big=largest_cnt(rotated)
	rx,ry,rh,rw = cv2.boundingRect(big)	
	rect = [rx,ry,rh,rw]				#Getting the dimension of this key contour is handled here rather than a separate function
	return rotated, rect

def scale(image:cv2.typing.MatLike,rect: list,params: Parameters) -> cv2.typing.MatLike:
	"""Resizes the the page both up or down so that the largest contour matches 
	the size of the template largest contour."""
	
	#needs to actually determine each side seperately

	scale_x = params.rect[2]/rect[2]
	scale_y = params.rect[3]/rect[3]
	rx,ry,_,_ = params.rect	
	sx = round(rect[0]*scale_x)
	sy = round(rect[1]*scale_y)
	image = cv2.resize(image,(round(4800*scale_x),round(6784*scale_y)))
	height, width, _ = image.shape

	if sx<rx:
		diff_x=4800-width+(rx-sx)
		print("Xdirection" ,rx-sx,diff_x)
		image = cv2.copyMakeBorder(image,0,0,rx-sx,diff_x,cv2.BORDER_CONSTANT, value=(255,255,255))	
	else:
		image = image[0:height,sx-rx:sx-rx+4800]
	if sy<ry:
		diff_y=6784-height+(ry-sy)
		print("ydirection",ry-sy,diff_y,height)
		image = cv2.copyMakeBorder(image,ry-sy,max(0,diff_y),0,0,cv2.BORDER_CONSTANT, value=(255,255,255))	
	else:
		image = image[sy-ry:sy-ry+6784,0:width]

	return image

def get_thresh(image,blur=True):
	if blur:
		image = cv2.medianBlur(image,5)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	return cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 27,4)

def	contour_center(contour):
	M = cv2.moments(contour)
	cx = int(M['m10']/M['m00'])
	cy = int(M['m01']/M['m00'])
	return [cx,cy]

def find_boxes(q_area,params):
	"""Goes through contour and returns List of only those of similar size to user defined box."""

	boxes = []
	thresh = get_thresh(q_area)
	cnts,hier = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)

	sorted_cnts = []
	for i, c in enumerate(cnts): 
		if hier[0][i][3]==-1:
			sorted_cnts.append(c)
	#sorted_cnts = [c for i, c in enumerate(cnts) if hier[0][i][3]==-1] #slower for some reason
	sorted_cnts = sorted(sorted_cnts, key=area, reverse=True)

	limit = 0.9*params.h*params.w
	min_w= int(params.w*0.9)
	min_h = int(params.h*0.9)
	max_w = int(params.w*2)
	max_h = int(params.h*2)
	version = None
	if params.w>params.h*2:
		version = "narrow"
	for c in sorted_cnts:
		_, _, w, h = cv2.boundingRect(c)
		if w*h<limit:	
			break
		if min_w<= w <= max_w and min_h <= h <= max_h: 
			boxes.append(contour_center(c))
			continue
		if version == "narrow":
			continue
		if h<params.h*4.5:
			erode_messy(c,q_area,params,boxes)
	return boxes

def erode_messy(c,q_area,params,boxes):
	"""Cleans up messy selections that bridge boxes. First and erosion pass then splits them based on height and width."""

	erode_mask = numpy.zeros(q_area.shape, dtype="uint8") 
	erode_mask = cv2.drawContours(erode_mask,[c],-1,(255,255,255),-1) 						#cv2.imshow("",cv2.resize(erode_mask,(700,700))) #cv2.waitKey(0)
	kernel = numpy.ones((31, 31), numpy.uint8)
	erode_mask = cv2.erode(erode_mask,kernel=kernel,iterations=1)
	erode_mask = cv2.cvtColor(erode_mask,cv2.COLOR_RGB2GRAY) 								#cv2.imshow("",cv2.resize(erode_mask,(700,700)))#cv2.waitKey(0)#cv2.imshow("",cv2.resize(erode_mask,(700,700))) #cv2.waitKey(0)
	erode_cnts,_= cv2.findContours(erode_mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	for e_cnt in erode_cnts: 
		x, y, w, h = cv2.boundingRect(e_cnt)
		if params.w*0.5 <= w <= params.w*1.5 and params.h*0.5 <= h <= params.h*1.5:
			boxes.append(contour_center(e_cnt))
			continue
		slice_messy(q_area,e_cnt,params,x,y,w,h,boxes)

def slice_messy(q_area,e_cnt,params,x,y,w,h,boxes):
	slice_mask = numpy.zeros(q_area.shape, dtype="uint8") 
	slice_mask = cv2.drawContours(slice_mask,[e_cnt],-1,(255,255,255),-1)
	x_scale = w//params.w+1
	y_scale = h//params.h
	j=1
	while j<x_scale:
		cv2.line(slice_mask,(x+j*w//x_scale,y-10),(x+j*w//x_scale,y+h+10),(0,0,0),15)
		j+=1
	k=1
	while k<y_scale:
		cv2.line(slice_mask,(x-10,y+k*h//y_scale),(x+w+10,y+k*h//y_scale),(0,0,0),15)
		k+=1
	slice_mask = cv2.cvtColor(slice_mask,cv2.COLOR_RGB2GRAY)
	slice_cnts,_= cv2.findContours(slice_mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)		#cv2.imshow("",cv2.resize(slice_mask,(700,700)))	#cv2.waitKey(0)
	for s_cnt in slice_cnts: 
		_, _, sw, sh = cv2.boundingRect(s_cnt)
		if params.w*0.5 <= sw <= params.w*1.5 and params.h*0.5 <= sh <= params.h*1.5:
			boxes.append(contour_center(s_cnt))

def sort_into_columns(boxes,params: Parameters):
	"""Sorts them from left to right. 
	Then if the gap between the left side of a box is more than half the width of a box of the previous it makes a new column
	Columns are then sorted from top to bottom"""

	columns = [[]]
	boxes = sorted(boxes, key=operator.itemgetter(0))
	
	prev_x=0
	col_index = 0
	for i, box in enumerate(boxes):	 
		x,_ = box
		if abs(x-prev_x) > params.w//2 and i>0:
			col_index +=1
			columns.append([])
		columns[col_index].append(box)
		prev_x = x
	copy_columns = columns.copy()
	for i, column in enumerate(copy_columns):
		if len(column) ==1:
			columns.pop(i)
	col_avg=[]
	for c, column in enumerate(columns):
		columns[c] = sorted(column, key=operator.itemgetter(1))
		x_pos=[]
		for r in columns[c]:
			x_pos.append(r[0])
		avg = sum(x_pos)/len(x_pos)
		col_avg.append(int(avg))
	params.col_avg = col_avg

	params.x_jump = int((col_avg[-1]-col_avg[0])/len(col_avg))

	prev = col_avg[0]
	for i, x_pos in enumerate(col_avg):
		if x_pos-prev>params.x_jump*1.2:
			params.choices=i
			break
		prev=x_pos
		params.choices=i+1
	return columns

def sort_into_rows(boxes,params):
	"""Sorts them from left to right. 
	Then if the gap between the left side of a box is more than half the width of a box of the previous it makes a new column
	Columns are then sorted from top to bottom."""

	rows = [[]]
	boxes = sorted(boxes, key=operator.itemgetter(1))

	prev_y=0
	row_index = 0
	for i, box in enumerate(boxes):	 
		_,y= box
		if abs(y-prev_y) > params.h and i>0:
			row_index +=1
			rows.append([])
		rows[row_index].append(box)
		prev_y = y	
	copy_rows = rows.copy()
	for i, row in enumerate(copy_rows):
		if len(row) ==1:
			print("lone",i)
			rows.pop(i)
	
	row_avg=[]
	for r, row in enumerate(rows):
		rows[r] = sorted(row, key=operator.itemgetter(0))
		y_pos=[]
		for c in rows[r]:
			_,y = c
			y_pos.append(y)
		avg = sum(y_pos)/len(y_pos)
		row_avg.append(int(avg))
	params.row_avg = row_avg
	params.y_jump = int((row_avg[-1]-row_avg[0])/len(row_avg))

def missing(columns,params): 
	"""Find missing question based on gaps that do not match average Y position of rows"""
	
	columns_copy=columns.copy()
	for c, column in enumerate(columns_copy):
		offset=0
		for r, row in enumerate(column):
			x,y = row

			if 20<abs(y-params.row_avg[r+offset])<int(params.y_jump-20):
				columns[c].pop(r+offset)
				offset-=1
				continue
			elif abs(y-params.row_avg[r+offset])>params.h:
				column.insert(r,[x,params.row_avg[r+offset]])
		if len(params.row_avg)>len(column):
			column.append([params.col_avg[c],params.row_avg[-1]])
		columns[c] = column
	return (columns)

def find_questions(columns,params):
	"""Goes through the columns to build questions."""

	stack = [[]]*params.choices
	for c, column in enumerate(columns):
		index = c%params.choices
		stack[index]= stack[index]+column
	questions=[]
	for r,row in enumerate(stack[0]):
		question = Question(r)
		for c,column in enumerate(stack):
			box = Question.Box(column[r],c)
			question.boxes.append(box)
		questions.append(question)
	return questions

def find_responses(student: Student,image,params: Parameters):

	student.choices = params.choices   
	student.y_jump = params.y_jump
	student.w = params.w

	thresh = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	thresh = cv2.GaussianBlur(thresh,(5,5),4)
	thresh = cv2.threshold(thresh,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1] 
	
	for question in student.questions:
		filled = 0	
		for box in question.boxes:
			box.fill(params,thresh)
			if box.bool:
				filled+=1
		if filled > 1:			
			question.response = False		
			student.incomplete.append(question)	
		else:
			question.get_response()


def make_output(students: list,gui: Gui,params: Parameters):
	#too many parts with too many jobs. should also come later in code sequence
	
	names(params.names,students)
	basename = os.path.basename(gui.filename)
	basename = basename.replace(".pdf","")
	path_to_save = gui.filename.replace(".pdf","")	
	if not(os.path.exists(path_to_save) and os.path.isdir(path_to_save)):
		os.mkdir(path_to_save)
	make_pdf(basename,path_to_save,students)
	make_csv(path_to_save,basename,students,params)

def make_pdf(basename,path_to_save,students):
	marked_pdf = pymupdf.open()
	if not(os.path.exists(f"{path_to_save}/single pages") and os.path.isdir(f"{path_to_save}/single pages")):
		os.mkdir(f"{path_to_save}/single pages")		
	for student in students:	
		student.string = student.name.replace(",", "")
		jpeg_path =f"{path_to_save}/single pages/{student.string}.jpg" #need to figure out how to make the zipfile able to add subdir
		student.pil_output.save(jpeg_path)
		bytes_scan = pymupdf.open(jpeg_path)                					#bytes_scan = pymupdf.open('png',student.scan)
		pdfbytes = bytes_scan.convert_to_pdf()
		rect = bytes_scan[0].rect                           					#bytes_scan.close()
		pdf_scan = pymupdf.open("pdf", pdfbytes)
		page = marked_pdf._newPage(width=rect.width, height=rect.height)
		page.show_pdf_page(rect,pdf_scan,0) 
	marked_pdf.save(f"{path_to_save}/ChilliMark-{basename}.pdf")

def make_csv(path_to_save,basename,students,params):
	file = open(f"{path_to_save}/{basename}.csv", 'w' ,newline='')
	writer = csv.writer(file, dialect='excel', )
	writer.writerow(["Student Name"]+[f"Out of {len(params.key)}"]+list(params.key.keys()))
	writer.writerow(["Answer Key"]+[""]+list(params.key.values()))
	for student in students:
		writer.writerow([student.name]+[student.score]+student.responses)	
	all_responses = [student.responses for student in students]
	all_responses= zip(*all_responses)

	csv_stats = [["Correct"]]
	rates = {"Correct": 0}
	for i in range(students[0].choices):
		rates.update({f"{chr(i+65)}" : 0})
		csv_stats.append([chr(i+65)])    

	stats = [] 
	for i, row in enumerate(all_responses):
		rate = rates.copy()
		for ans in row:
			if rate.get(ans)!= None:
				rate[ans]=rate.get(ans) + 1
			if ans == params.key.get(i) and params.key:
				rate["Correct"] = rate.get("Correct") +1
		stats.append(rate.values())

	
	for row in stats:
		for k, r in enumerate(row):
			csv_stats[k].append(r)

	writer.writerow([""])
	for x in csv_stats:
		writer.writerow([""]+x)

def names(names_input,students):
	if names_input:
		names_input = names_input.title()
		names_input = names_input.split("\n")
		for i, name in enumerate(names_input):
			students[i].name = name.rstrip(", ") if name else students[i].name

def area(n):
	_,_,w,h = cv2.boundingRect(n)
	return h*w

def main():

	gui = Gui()
	ctypes.windll.shcore.SetProcessDpiAwareness(1)
	gui.home()
	#core(gui,params)
	#gui.processing()
	#gui.complete()
	#gui.box_canvas.after(10,gui.selection_animation())	
	gui.root.mainloop()

if __name__ == '__main__':
    main()