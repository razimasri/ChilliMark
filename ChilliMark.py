import multiprocessing
import multiprocessing.pool
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
import tkinter.ttk
import tksvg
import tkinterdnd2
import tkinterdnd2.TkinterDnD
import ctypes


#to do,

#scale also aligning pages
#q_area as relative to alignment rect


def timer(func):
	def wrapper(*args, **kwargs):
		begin = time.time()
		result = func(*args, **kwargs)
		# storing time after function execution
		end = time.time()
		print(func.__name__, end - begin)
		return result
	return wrapper


class Gui:	
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

	def __init__(self):
		self.root = tkinterdnd2.TkinterDnD.Tk()	
		#self.icon = PIL.ImageTk.PhotoImage(file="icons\icon128.png")
		self.icon = tksvg.SvgImage(file="icons\iconwhite.svg", scaletoheight = 128 )
		#self.version = ["v0.9","Capsaicin"]
		self.version = ["v1.0","Adjuma"]
		self.root.tk.call('wm', 'iconphoto', self.root._w, PIL.ImageTk.PhotoImage(file="icons\Icon16.ico"))
		self.root.title("Chilli Marker")
		self.palette = {
			"darktext" : "#280e0d",
			"frame" : "#571622",
			"whitespace" : "#e3e5ef",
			"lighttext" : "#e3e5ef",
			"bg": "#8c1529",
			"button": "#b1a1a4",
			"prog_bar":"#00713e"}
		self.root.configure(bg=self.palette.get("bg"), borderwidth=2)
		self.root.geometry("920x750")
		self.root.resizable(False, False)
		self.default_font = tkinter.font.nametofont("TkDefaultFont")
		self.small_font=self.default_font.copy()
		self.default_font.configure(size=14, weight="bold")
		self.small_font.configure(size=10)
		self.root.option_add("*Font", self.default_font)
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(1, weight=1)

	def q_mouse_posn(self,event):
		self.q_rect.x1, self.q_rect.y1 = event.x, event.y

	def box_mouse_posn(self,event):
		self.box_rect.x1, self.box_rect.y1 = event.x, event.y
		self.box_rect.x1true, self.box_rect.y1true = self.box_canvas.canvasx(event.x), self.box_canvas.canvasy(event.y)

	def q_sel_rect(self,event):
		self.q_rect.x2, self.q_rect.y2 = event.x, event.y
		self.canvas.coords(self.q_rect.rect, self.q_rect.x1, self.q_rect.y1, self.q_rect.x2, self.q_rect.y2)  # Update selection rect.

	def box_sel_rect(self,event):
		self.box_rect.x2, self.box_rect.y2 = event.x, event.y
		self.box_rect.x2true, self.box_rect.y2true = self.box_canvas.canvasx(event.x), self.box_canvas.canvasy(event.y)
		self.box_canvas.coords(self.box_rect.rect, 0,0,0,0)  # Update selection rect.
		self.box_rect.rect = self.box_canvas.create_rectangle(self.box_rect.x1true, self.box_rect.y1true, self.box_rect.x2true, self.box_rect.y2true, dash=(50,), fill='', width=1, outline=self.palette.get("frame"))
		
	def q_area(self,event):
		x1 = max(0,(min(self.q_rect.x1,self.q_rect.x2)))
		x2 = min(500,(max(self.q_rect.x1,self.q_rect.x2)))
		y1 = max(0,(min(self.q_rect.y1,self.q_rect.y2)))
		y2 = min(705,(max(self.q_rect.y1,self.q_rect.y2)))
		self.y1 = round(y1*6828/705)
		self.x1 = round(x1*4800/500)
		self.y2 = round(y2*6828/705)
		self.x2 = round(x2*4800/500) 
		self.image = PIL.ImageTk.PhotoImage(self.pil.crop([self.x1,self.y1,self.x2,self.y2]))
		self.box_canvas.create_image(0, 0, image=self.image, anchor=tkinter.NW)
		self.box_canvas.config(cursor="crosshair",scrollregion=[0,0,self.x2-self.x1,self.y2-self.y1], xscrollcommand = self.hbar.set, yscrollcommand = self.vbar.set)
		self.vbar.grid(row=2,column=1,sticky="ns")
		self.hbar.grid(row=3,column=0,sticky="ew")
		self.int.config(text="Now select one empty box")

	def start_listener(self,event):
		if not self.listener.running:
			self.listener = pynput.mouse.Listener(on_scroll=self.on_scroll)
			self.listener.start()

	def stop_listener(self,event):
		if self.listener.running:
			self.listener.stop()

	def on_scroll(self,x, y, dx, dy):
		while dy>10 or dy<-10:
			dy //= 10
		while dx>10 or dx<-10:
			dx //=10

		self.box_canvas.xview_scroll(dx, "units")
		self.box_canvas.yview_scroll(-dy, "units")

	def home(self):
		self.destroy_children(self.root)
		self.pdf_icon = tksvg.SvgImage(file="icons\pdf.svg", scaletoheight = 256 )
		self.canvas_frame = tkinter.Frame(self.root,bg=self.palette.get("frame"), height=725, width=520, bd=0, highlightthickness=0, relief='ridge')
		self.canvas_frame.grid(padx="10", pady="10", column=0,row=0)
		self.canvas_frame.columnconfigure(0, weight=1)
		self.canvas_frame.rowconfigure(1, weight=1)
		self.canvas_frame.grid_propagate(False)
		self.pdf = tkinter.Label(self.canvas_frame, bg=self.palette.get("frame"), image=self.pdf_icon)
		self.pdf.grid(row=1)

		#Drag and Drop Files
		self.root.drop_target_register(tkinterdnd2.DND_FILES)
		self.root.dnd_bind('<<Drop>>', lambda event: self.open_file(event.data))

		self.right_frame = tkinter.Frame(self.root, bg=self.palette.get("bg"),height=725,width=523)
		self.right_frame.grid(padx=(0,10), pady="10",column=1,row=0, sticky="nsew")
		mark_frame = tkinter.Frame(self.right_frame, bg=self.palette.get("bg"))
		mark_frame.pack(side="bottom", fill="x")
		self.mark_btn=tkinter.Button(mark_frame, text="Mark Exams", height = 4, width = 20,borderwidth=3, command=load_inputs,state=tkinter.DISABLED)
		self.mark_btn.pack(padx=(0,5),pady=(10,0), side='left', fill="both", expand='yes')
		tkinter.Label(mark_frame, bg=self.palette.get("bg"), image=self.icon).pack(side='top')
		tkinter.Label(mark_frame, text=self.version, bg = self.palette.get("bg")).pack(side='bottom')
		entry_frame = tkinter.Frame(self.right_frame,bg=self.palette.get("frame"), height= 500)
		entry_frame.pack(side = "bottom", fill="both", expand="yes")
		entry_frame_ans= tkinter.Frame(entry_frame,bg=self.palette.get("frame"))
		entry_frame_ans.pack(side="right", pady="10",fill="both", expand="yes")
		entry_frame_stu= tkinter.Frame(entry_frame,bg=self.palette.get("frame"))
		entry_frame_stu.pack(side="left", pady=10,padx=(10,0), fill="both", expand="yes")
		tkinter.Label(entry_frame_ans,text="Answer Key",width=9,height = 1,anchor="w",bg=self.palette.get("frame"),fg=self.palette.get("lighttext")).pack(sid="top", pady="10")
		self.ans_key_box=tkinter.Text(entry_frame_ans,width=10,height=2, bg=self.palette.get("whitespace"),undo=True)
		self.ans_key_box.pack(padx = "10",fill="both",expand="yes")
		tkinter.Label(entry_frame_stu, text="Student Names", height = 1, anchor="w",bg=self.palette.get("frame"),fg=self.palette.get("lighttext")).pack(side = "top", padx="10", pady="10")
		tkinter.Label(entry_frame_stu,wraplength=190, bg=self.palette.get("frame"),text="Organize the names in the same order as the scans\nExample: \n    Tanner Moore \n    Emily Hunt\n    Foster Holmes\n    Bailey Alexander\n    ...",anchor="w", font=self.small_font,fg=self.palette.get("lighttext"),justify="left").pack(side="bottom", pady="10", anchor=tkinter.NW)
		self.stu_names_box=tkinter.Text(entry_frame_stu,width=30,height=2,font=self.small_font, bg=self.palette.get("whitespace"),undo=True)
		self.stu_names_box.pack(side = "top",fill="both",expand="yes")
		self.file_btn=tkinter.Button(self.right_frame, text="Select Exam", height = 1, width = 20, borderwidth=3, command=self.choose_file)
		self.file_btn.pack(side="bottom",pady=(0,10),fill="x")

	def parameters(self,template):
		self.page = template
		self.destroy_children(self.canvas)
		r_f_w = self.right_frame.winfo_width()-28
		self.destroy_children(self.right_frame)	
		img = PIL.Image.fromarray(template)
		self.pil = img.copy()
		img.thumbnail([500,705])
		thumb = PIL.ImageTk.PhotoImage(img)
		#panel = tkinter.Label (self.canvas, bg=self.palette.get("frame"))
		#panel.grid(row=0, column=0)
		self.canvas.img = thumb
		self.canvas.create_image(0, 0, image=thumb, anchor=tkinter.NW)
		self.canvas.config(cursor="crosshair")
		self.box_frame = tkinter.Frame(self.right_frame,bg=self.palette.get("frame"))
		self.box_frame.grid(sticky="nsew")
		def back():
			gui.home()
			self.choose_file()
		tkinter.Button(self.box_frame, text="Choose another file", borderwidth=3, command=back).grid()
		self.int = tkinter.Label(self.box_frame,text="Select the question area", bg=self.palette.get("frame"),fg=self.palette.get("lighttext")) 
		self.int.grid()
		#tkinter.Button(self.right_frame, text="Select").grid()
		self.box_canvas = tkinter.Canvas(self.box_frame,bd=0,bg=self.palette.get("frame"), highlightthickness=0, relief='ridge',width=r_f_w,height=470)
		self.box_canvas.grid(row=2,column=0,sticky="nsew") 
		self.hbar=tkinter.Scrollbar(self.box_frame,orient=tkinter.HORIZONTAL,width=12,bd=0,relief=tkinter.FLAT)
		self.vbar=tkinter.Scrollbar(self.box_frame,orient=tkinter.VERTICAL,width=12,bd=0,relief=tkinter.FLAT)
		self.hbar.config(command=self.box_canvas.xview)
		self.vbar.config(command=self.box_canvas.yview)
	
		self.q_rect = self.Rectangle()
		self.q_rect.rect = self.canvas.create_rectangle(0,0,0,0, dash=(50,), fill='', width=1, outline=self.palette.get("frame"))
		self.canvas.bind('<Button-1>', self.q_mouse_posn)
		self.canvas.bind('<B1-Motion>', self.q_sel_rect)
		self.canvas.bind('<ButtonRelease-1>', self.q_area) 

		self.box_rect = self.Rectangle()
		self.box_rect.rect = self.box_canvas.create_rectangle(0,0,0,0)
		#self.box_rect.rect = self.box_canvas.create_rectangle(self.box_rect.x1, self.box_rect.y1, self.box_rect.x2, self.box_rect.y2, dash=(50,), fill='', width=1, outline=self.palette.get("frame"))
		#self.box_canvas.create_rectangle(100,100,200,200, dash=(50,), fill='#000000', width=1, outline=self.palette.get("frame"))
		self.listener = pynput.mouse.Listener(on_scroll=self.on_scroll)
		self.box_canvas.bind('<Button-1>', self.box_mouse_posn)
		self.box_canvas.bind('<B1-Motion>', self.box_sel_rect)
		self.box_canvas.bind('<Enter>', self.start_listener)
		self.box_canvas.bind('<Leave>', self.stop_listener)
		self.box_canvas.bind('<ButtonRelease-1>', lambda _: mark_btn.config(state=tkinter.ACTIVE)) 		
		
		mark_frame = tkinter.Frame(self.right_frame, bg=self.palette.get("bg"))
		mark_frame.grid()
		mark_btn=tkinter.Button(mark_frame, text="Mark Exams", height = 4, width = 20,borderwidth=3, state=tkinter.DISABLED, command=lambda: load_parameters(self,template))
		mark_btn.pack(padx=(0,5),pady=(10,0), side='left', fill="both", expand='yes')
		tkinter.Label(mark_frame, bg=self.palette.get("bg"), image=self.icon).pack(side='top')
		tkinter.Label(mark_frame, text=self.version, bg = self.palette.get("bg")).pack(side='bottom')
		self.root.wait_window()

	def processing(self):

		self.destroy_children(self.root)
		self.progress_frame = tkinter.Frame(self.root)
		tkinter.Label(self.root,text="Processing").grid()
		#self.progress_frame.grid(row=1,sticky="ew")
		self.corrections_frame = tkinter.Frame(self.root, bg=self.palette.get("frame"))
		self.finished=tkinter.BooleanVar(gui.root,True)
		self.corrections_frame.grid()
		self.root.update()
	




	def complete(self):
		global filename
		


		make_output()
		self.destroy_children(self.root)
		path_to_save = filename.replace(".pdf","")
		tkinter.Label(self.root,text="Finished").pack()
		tkinter.Button(self.root,text="Open output", command=lambda:os.startfile(path_to_save)).pack()
		tkinter.Button(self.root,text="Mark Another Exam", command=self.home).pack()
		self.root.wait_window()

	def progress_bar(self,condition=None,frame=None):
		bar = tkinter.ttk.Progressbar(frame, orient = tkinter.HORIZONTAL, length = 280, mode = 'indeterminate')
		
		bar.pack(side='top', pady = (0,10), fill="x")
		while condition():
			bar['value']+=10
			self.wait.wait(0.1)
			bar.update()
		bar.destroy()

	def open_file(self,file: str):
		global filename
		if not file:
			return
		filename = file.strip("{,}")
		self.pdf.destroy()
		#self.canvas_frame.children.clear()
		self.canvas = tkinter.Canvas(self.canvas_frame, bg=self.palette.get("frame"), height=705, width=5, bd=0, highlightthickness=0, relief='ridge')
		self.canvas.grid(padx="10", pady="10", column=0,row=0, sticky="nsew")
		doc = pymupdf.open(filename)
		thumb_size, positions = self.thumb_grid(doc)
		for i, page in enumerate(doc):
			pix = page.get_pixmap(dpi=72, colorspace="RGB")
			img = PIL.Image.frombuffer("RGB", [pix.width, pix.height], pix.samples)  
			img.thumbnail(thumb_size)
			thumb = PIL.ImageTk.PhotoImage(img)
			panel = tkinter.Label (self.canvas)
			panel.grid(row=positions[i][0], column=positions[i][1])
			panel.config(image=thumb)
			panel.image = thumb
			self.root.update()
		self.mark_btn.config(state=tkinter.ACTIVE)

	def thumb_grid(self,doc):
		grid_size = math.isqrt(len(doc))+1*(math.sqrt(len(doc))!=math.isqrt(len(doc)))
		thumb_size = (500//grid_size-4,705//grid_size-4)
		positions = []
		c=0
		r=0
		while r < grid_size:  			#turn shorter logic
			while c < grid_size:
				positions.append([r,c])
				c+=1
			c=0
			r+=1
		return thumb_size ,positions

	def choose_file(self):
		global filename
		filename = tkinter.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
		self.open_file(filename)

	def destroy_children(self,parent):
		for child in parent.winfo_children():
			if child.winfo_children():
				self.destroy_children(child)
			child.destroy()

class Parameters:
	def __init__(self,rect,key_input):
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
		self.set_key(key_input)
	
	def set_box(self,image):
		image = get_thresh(image[int(self.box_y1):int(self.box_y2),int(self.box_x1):int(self.box_x2)],blur=True)
		outer, _ = cv2.findContours(image,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		outer=outer[0]
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

class Student:

	colour = {"red": (200,0,0),"yellow": (250,170,0),"green": (0,170,0)}

	def __init__(self,filename,i,params):
		self.name = f"Student {i+1:0{params.num}}"
		self.num = i+1
		self.scan = None
		self.responses = None
		self.questions = []
		self.score = 0
		self.process_page(filename,i,params)
		self.mark(params)
	
	def process_page(self,filename,i,params):
		doc = pymupdf.open(filename)
		pix = doc[i].get_pixmap(dpi=600, colorspace="RGB")
		image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
		image,rect= rotation(image)
		image= scale(image,rect,params)
		self.scan=image
		self.pil_original = PIL.Image.fromarray(self.scan[:,:,::1])


	def mark(self,params):
		"""Identifies the boxes, and if they have been filled. Then annotates the images"""
		q_area = self.scan[params.y1:params.y2,params.x1:params.x2]
		boxes = find_boxes(q_area,params)
		columns = sort_into_columns(boxes,params)
		sort_into_rows(boxes,params)
		missing(columns,params)
		self.questions = find_questions(columns,params)
		find_responses(self,q_area,params)
		self.responses = [question.response for question in self.questions]
		if params.key:
			self.add_markup(q_area,params)
		q_area = self.annotate(params,q_area)
		self.scan[params.y1:params.y2,params.x1:params.x2] = q_area
		self.scan=cv2.putText(self.scan,self.name,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(255,255,255),25)
		self.scan=cv2.putText(self.scan,self.name,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(0,0,0),10)
		self.scan = cv2.cvtColor(self.scan,cv2.COLOR_BGR2RGB)		
		self.scan[256:512,4288:4544]=cv2.imread("icons\printmark.png")
		self.pil_output = PIL.Image.fromarray(self.scan[:,:,::-1])		
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

class Question:
	
	colour = {"red": (0,0,200),"yellow": (0,170,250),"green": (0,170,0)}
	
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
			print("if",self.response)
			return
		for box in self.boxes:
			print("else",self.response)
			if box.bool:
				cv2.drawContours(image, [box.xy+params.outer], -1, colour.get(box.colour), 5,cv2.LINE_AA)

class Box:
	def __init__(self,xy,q,i):
		self.xy = xy
		# self.question = q #r
		# self.num = i #c
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

def page_to_image(filename,i,params):
	doc = pymupdf.open(filename)
	pix = doc[i].get_pixmap(dpi=600, colorspace="RGB")
	image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
	image,rect= rotation(image)
	image= scale(image,rect,params)
	return image

def load_parameters(gui,template):
	global params

	params.y1 = gui.y1  #assign directly in gui?
	params.x1 = gui.x1
	params.y2 = gui.y2
	params.x2 = gui.x2
	
	params.box_y1 = gui.box_rect.y1true+params.y1
	params.box_x1 = gui.box_rect.x1true+params.x1
	params.box_y2 = gui.box_rect.y2true+params.y1
	params.box_x2 = gui.box_rect.x2true+params.x1
	
	if params.set_box(template)==False:
		tkinter.messagebox.showinfo(message="Choose another box")
		gui.parameters(template)
	
	params.set_markup_size()
	gui.processing()
	core()





def core():
	global names_input, filename, params, students
	doc = pymupdf.open(filename) #probably unecessary. remove after getting the returning of image correct
	params.num = len(doc)//10+1
	
	pages=[[filename,i,params] for i,_ in enumerate(doc)] #creating tuples to pass to the parallel processing function since it cannot take the page object
	

	pool = multiprocessing.Pool(multiprocessing.cpu_count()*2) 
	students = pool.starmap(Student,pages)

	for student in students: #create a sublist or tag instead"

		if all(student.responses):
			continue
		q_area = student.scan[params.y1:params.y2,params.x1:params.x2]
		for question in student.questions:
			if question.response:
				continue
			corrections(question,student.pil_original)
			student.responses[question.number]=question.response
			if not params.key:
				pass
			elif question.response == params.key[question.number]:
				question.response_box.colour="green"
				student.score+=1
			question.annotate(params,q_area)

		if params.key:
			student.scan = cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
			student.scan= cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)		
		
		
		student.scan[params.y1:params.y2,params.x1:params.x2] = q_area
		student.pil_output = PIL.Image.fromarray(student.scan[:,:,::-1])	
				
			# for box in question.boxes:
			# 	if box.bool:
			# 		cv2.drawContours(student.scan, [box.xy+params.outer], -1, colour.get(box.colour), 5,cv2.LINE_AA)


	make_output()
	gui.complete()


	
def load_inputs():
	"""Select the question regions and an example box. 
	Multiple other important parameters are defined based on this"""
	
	global filename, gui, params, template, names_input
	
	names_input=gui.stu_names_box.get(1.0, "end-1c")
	key_input=gui.ans_key_box.get(1.0, "end-1c")
	if filename == None:
		tkinter.messagebox.showinfo(title="No file", message= "Please select a file")
		return
	elif not key_input or not names_input:
		if not tkinter.messagebox.askokcancel(title="Missing Info", message= "You have not entered either the Student Names or Answer Key. \nAre you sure you want to continue?"):
			return
	
	doc = pymupdf.open(filename)
	pix = doc[0].get_pixmap(dpi=600, colorspace="RGB")
	template = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
	template = cv2.resize(template,(4800,6828))
	template,rect = rotation(template)
	params = Parameters(rect,key_input)
	
	gui.parameters(template)

def largest_cnt(image):
	"""Find the largest contour on the page for use with alignment functions. 
	Note that it draws a border on the image to eliminate false contours from scan edges."""

	gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1] 
	thresh = cv2.rectangle(thresh,(0,0),(4800,6828),0,200)
	cnts,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	filtered = filter(lambda cnt: area(cnt)>4000000,cnts)
	sorted_cnts = sorted(filtered, key=area, reverse=True)
	largest = sorted_cnts[0]
	largest = cv2.approxPolyDP(largest, 0.01*cv2.arcLength(largest, True), True)
	return largest

def rotation(page):
	"""Assumes the largest contour is a box. 
	Finds the rotation of largest contour and rotates the page based on that. 
	Also returns key info about the largest for use in future scaling"""
	
	big=largest_cnt(page)
	rect = cv2.minAreaRect(big)
	if rect[2] > 45:
		angle = rect[2]-90
	else: 
		angle = rect[2]
	Matrix = cv2.getRotationMatrix2D((2400,3414),angle,1)
	rotated = cv2.warpAffine(page, Matrix, (4800, 6828))
	big=largest_cnt(rotated)
	rx,ry,rh,rw = cv2.boundingRect(big)	
	rect = [rx,ry,rh,rw]				#Getting the dimension of this key contour is handled here rather than a separate function
	return rotated, rect

def scale(image,rect,params):
	"""Resizes the the page both up or down so that the largest contour matches the size of the key largest contour."""
	
	scale_x = params.rect[2]/rect[2]
	scale_y = params.rect[3]/rect[3]
	rx,ry,_,_ = params.rect	
	sx = round(rect[0]*scale_x)
	sy = round(rect[1]*scale_y)
	image = cv2.resize(image,(round(4800*scale_x),round(6828*scale_y)))
	height, width, _ = image.shape



	if sx<rx:
		diff_x=4800-width+(rx-sx)
		print("Xdirection" ,rx-sx,diff_x)
		image = cv2.copyMakeBorder(image,0,0,rx-sx,diff_x,cv2.BORDER_CONSTANT, value=(255,255,255))	
	else:
		image = image[0:height,sx-rx:sx-rx+4800]
	if sy<ry:
		diff_y=6828-height+(ry-sy)
		print("ydirection",ry-sy,diff_y,height)
		image = cv2.copyMakeBorder(image,ry-sy,max(0,diff_y),0,0,cv2.BORDER_CONSTANT, value=(255,255,255))	
			
	else:
		image = image[sy-ry:sy-ry+6828,0:width]

	return image

def select_area(image, instructions="Select Area",blur=False):
	"Select the area to find contours."
	
	if blur:
		image = cv2.GaussianBlur(image,(19,19),3) 

	height, width, _ = image.shape
	scale = height/705
	width = int(width/scale)
	height = 705

	image = cv2.resize(image, (width,height)) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(255, 255, 255),10,lineType=cv2.LINE_AA) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(1, 1, 1),2,lineType=cv2.LINE_AA) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(21, 21, 140),1,lineType=cv2.LINE_AA) 
	x,y,w,h = cv2.selectROI(instructions, image)
	cv2.namedWindow(instructions)
	cv2.setWindowProperty(instructions, cv2.WND_PROP_TOPMOST, 1)
	cv2.destroyAllWindows()
	if not x:
		return

	x1= int((x-3)*scale) 
	y1= int((y-3)*scale) 
	x2= int((w+6)*scale) + x1
	y2= int((h+6)*scale) + y1

	return y1,x1,y2,x2

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

def sort_into_columns(boxes,params=None):
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
			#print(abs(y-params.row_avg[r+offset]),int(params.y_jump-20))
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
			box = Box(column[r],r,c)
			question.boxes.append(box)
		questions.append(question)
	return questions

def find_responses(student,image,params):

	student.choices = params.choices   #a quick hack to get around globals and how multiprocessing means params no longer take ypdatedinfoinfo
	student.y_jump = params.choices
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
		else:
			question.get_response()

def make_output():
	global names_input, filename, params, students
	#too many parts with too many jobs. should also come later in code sequence

	names(names_input,students)
	basename = os.path.basename(filename)
	basename = basename.replace(".pdf","")
	path_to_save = filename.replace(".pdf","")	
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

def corrections(question,image):
	"""Brings up a GUI to manually choose the student's response"""	
	
	global gui
	#definitly turn into method in class
	gui.finished.set(False)
	centres = [box.xy for box in question.boxes]
	qx,qy = (centres[0][0]+centres[-1][0])//2, (centres[0][1]+centres[-1][1])//2
	x1 = qx-435+gui.x1
	y1 = qy-150+gui.y1
	x2 = qx+435+gui.x1
	y2 = qy+150+gui.y1
	unclear = image.crop([x1,y1,x2,y2])
	imgtk = PIL.ImageTk.PhotoImage(image = unclear)
	def button(response="Unclear",question=question, choose=gui.corrections_frame):
		if type(response)==str:
			question.response = response
		else:
			question.response = chr(response+65)
			question.boxes[response].colour = "red"
			question.boxes[response].bool = True
			question.response_box = question.boxes[response]
		print(question.response)
		gui.destroy_children(gui.corrections_frame)
		gui.finished.set(True)
		return
	span=len(question.boxes)
	tkinter.Label(gui.corrections_frame, image=imgtk).grid(padx="10", pady="10",row=0)#,column=0,columnspan=span)
	frame=tkinter.Frame(gui.corrections_frame,bg="#8c1529")
	frame.grid(padx="5", row=1, sticky="nsew")
	for i in range(span):
		tkinter.Button(frame, text=chr(i+65), command=lambda i=i: button(i)).grid(padx=(5), pady=(0,10),column=i,row=1, sticky="NSEW")
		frame.columnconfigure(index=i,weight=1)
	tkinter.Button(frame, text="Unclear", command=lambda: button("Unclear")).grid(padx=(5), pady=(0,10),row=2,column=0,columnspan=span//2, sticky="NSEW")
	tkinter.Button(frame, text="Blank", command=lambda: button("Blank")).grid(padx=(5), pady=(0,10),row=2,column=2,columnspan=span//2, sticky="NSEW")
	gui.root.wait_variable(gui.finished)

def area(n):
	_,_,w,h = cv2.boundingRect(n)
	return h*w


def main():
	global filename, gui
	filename = None
	
	gui = Gui()
	ctypes.windll.shcore.SetProcessDpiAwareness(1)
	gui.home()
	gui.root.mainloop()

if __name__ == '__main__':
    main()