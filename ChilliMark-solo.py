import multiprocessing
import multiprocessing.pool
import multiprocessing.process
import threading
import numpy
import cv2
import pymupdf
import csv
import os
import operator
import PIL
import PIL.Image
import Gui

#Dedicated to my Wife



class Question:
	
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
		self.number = r
		self.response = "Blank"
		self.response_box = None
		self.boxes = []
		
	
	def get_response(self):
		for box in self.boxes:
			if box.bool:
				self.response=box.letter
				self.response_box=box
				box.colour = "red"
	
	def annotate(self,params,image): 
		#the logic of the two annotate functions is slightly different. 
		# This time we do no want to skip unclear. 
		# We are also avoiding a later RGB colour flip
		colours = {"red": (200,0,0),"yellow": (250,170,0),"green": (0,170,0)}
		if self.response =="Blank":
			return
		for box in self.boxes:
			if box.bool:
				cv2.drawContours(image, [box.xy+params.outer], -1, colours.get(box.colour), 5,cv2.LINE_AA)

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

		percentage = abs(area(outer)-((self.box_y2-self.box_y1)*(self.box_x2-self.box_x1)))/area(outer)
		
		if percentage>0.7:
			raise Exception("Your selection does not return a complete box")
		#if percentage>0.35:
		#	print(percentage)
		
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
		self.fill_limit = 5.5*(cv2.contourArea(self.inner))**0.5

	def set_markup_size(self):
		"""Defines the sizes for the text annotation to match the Box Size"""
		
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
			gui.bad_box()
		else:
			return gui.next.set(True)

class Student:

	colours = {"red": (200,0,0),"yellow": (250,170,0),"green": (0,170,0)}

	def __init__(self,filename,i,params):
		self.name: str = f"Student {i+1:0{params.num}}"
		self.index: int = i 

		self.params = params
		self.filename = filename
		#self.queue = queue
		#self.frame = 0
		self.scan = None
		self.responses = None
		self.questions: list = []
		self.incomplete: list = []
		self.score: int = 0
	
	def get(self):
		"""Multiprocess only handles certain types of object. Even with Dill. 
		This function ensure the functions are called in a multiprocessing safe way.
		It changes nested classs objects into picklable list objects for use by the core logic.
		Classes still used on this side to make managements easier"""


		self.pdfs_to_images(self.filename,self.index,self.params)
		self.mark(self.params)

		p_questions = []
		for q in self.questions:
			p_boxes = []
			for i, b in enumerate(q.boxes):
				p_box = [b.xy,i, b.colour,b.bool]
				p_boxes.append(p_box)
			p_question = [q.number,q.response,p_boxes]
			p_questions.append(p_question)

		pickles = [self.scan,self.responses,self.score,p_questions]#,self.questions,self.incomplete]
		return pickles
	
	def animation_step(self):
		#self.queue.put( [self.index,self.frame])
		self.frame+= 1
	
	def pdfs_to_images(self,filename: str,i: int,params: Parameters):
		"""Opens up the doc file and create both the Pillow image and CV2 Matrix. 
		This was designed for multiprocessing so the function opens its pack of the pdf directly to side step pickling"""

		doc = pymupdf.open(filename)
		pix = doc[i].get_pixmap(dpi=600, colorspace="RGB")
		image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
		image,rect= rotation(image)
		image=scale(image,rect,params)

		

		self.scan=image

		#self.pil_original = PIL.Image.fromarray(self.scan)


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
		self.scan[256:512,4288:4544]=cv2.imread(r"icons\printmark.png")[:, :, ::-1]

		
		#self.pil_output = PIL.Image.fromarray(self.scan)		



	def annotate(self,params,image):
		for question in self.questions:
			if question.response=="Blank" or not question.response:
				continue
			for box in question.boxes:
				if box.bool:
					cv2.drawContours(image, [box.xy+params.outer], -1, Student.colours.get(box.colour), 5,cv2.LINE_AA)
		return image
	
	def add_markup(self,image,params):
		for question in self.questions:
			if question.number>len(params.key)-1:
				break
			if params.key[question.number] == question.response:
				question.response_box.colour="green"
				self.score+=1
			x,y=question.boxes[ord(params.key[question.number])-65].xy
			text_y = y+params.text_shift[1]
			text_x = x+params.text_shift[0]
			cv2.putText(image,params.key[question.number], (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, params.font_size,(255,255,255),20,lineType=cv2.LINE_AA) 
			cv2.putText(image,params.key[question.number], (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, params.font_size,Student.colours.get("green"),7,lineType=cv2.LINE_AA) 
		if question.response:
			self.scan = cv2.putText(self.scan,f"Score = {self.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
			self.scan= cv2.putText(self.scan,f"Score = {self.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)		
		return image

def corrections(students: list, gui: Gui.Gui, params: Parameters):
	"""Looks through list of students responses with unclear answers,
	Brings up a gui with the question and asks the marker to assign the respose."""
	
	#get a nicer war to manage choices
	gui.create_corrections_gui(4)


	for student in students:
		gui.completed_page_panels(student)	
	
	incomplete = [student for student in students if not all(student.responses)]

	for student in incomplete:
		for question in student.incomplete:
			centres = [box.xy for box in question.boxes]

			qx,qy = (centres[0][0]+centres[-1][0])//2, (centres[0][1]+centres[-1][1])//2
			x1 = qx-500+params.x1
			y1 = qy-155+params.y1
			x2 = qx+500+params.x1
			y2 = qy+115+params.y1
			unclear = student.pil_output.crop([x1,y1,x2,y2])
			gui.enter_corrections(unclear)
			question.response = gui.response.get()
			student.responses[question.number]=question.response
			if question.response == "Blank":
				continue
			if len(question.response)==1:
				question.boxes[ord(question.response)-65].colour = "red"
				question.boxes[ord(question.response)-65].bool = True
				question.response_box = question.boxes[ord(question.response)-65]

			if params.key:
				if params.key[question.number]==question.response:
					question.response_box.colour="green"
					student.score+=1
		cor_update = threading.Thread(target=correction_update, args=[student,gui,params])
		cor_update.start()

def correction_update(student: Student,gui: Gui,params:Parameters):
	q_area = student.scan[params.y1:params.y2,params.x1:params.x2]
	for question in student.incomplete:
		question.annotate(params,q_area)
	if params.key:
		student.scan = cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
		student.scan= cv2.putText(student.scan,f"Score = {student.score} / {len(params.key)}",(4270-params.score_size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)
	student.scan[params.y1:params.y2,params.x1:params.x2] = q_area
	student.pil_output = PIL.Image.fromarray(student.scan)
	try: #gui will have moved onto complete for final image if this was the last correction
		gui.completed_page_panels(student)
	except:
		pass

def core(gui: Gui,params: Parameters):
	doc = pymupdf.open(gui.filename) #probably unecessary. remove after getting the returning of image correct
	params.num = len(doc)//10+1
	pages=[[gui.filename,i,params] for i,_ in enumerate(doc)] 
	pool = multiprocessing.Pool(len(doc)) 
	students_async = pool.starmap_async(Student,pages)


	#creating tuples to pass to the parallel processing function since it cannot take the page object
	pages=[[gui.filename,i,params] for i,_ in enumerate(doc)] 
	pool = multiprocessing.Pool(len(doc)) 
	students_async = pool.starmap_async(Student,pages)


	return students_async



def load_inputs(gui):
	"""Select the question regions and an example box. 
	Multiple other important parameters are defined based on this"""
	
	doc = pymupdf.open(gui.filename)
	pix = doc[0].get_pixmap(dpi=600, colorspace="RGB")
	template = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
	template = cv2.resize(template,(4800,6840))
	template,rect = rotation(template)
	params = Parameters(rect,gui.key_input,gui.names_input,template)
	params.filename = gui.filename
	return params


def largest_cnt(image:cv2.typing.MatLike) -> cv2.typing.MatLike:
	"""Find the largest contour on the page for use with alignment functions. 
	Note that it draws a border on the image to eliminate false contours from scan edges."""

	gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1] 
	thresh = cv2.rectangle(thresh,(0,0),(4800,6840),0,200)
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
	Matrix = cv2.getRotationMatrix2D((2400,3420),angle,1)
	rotated = cv2.warpAffine(page, Matrix, (4800, 6840))
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
	image = cv2.resize(image,(round(4800*scale_x),round(6840*scale_y)))
	height, width, _ = image.shape

	if sx<rx:
		diff_x=4800-width+(rx-sx)
		print("Xdirection" ,rx-sx,diff_x)
		image = cv2.copyMakeBorder(image,0,0,rx-sx,diff_x,cv2.BORDER_CONSTANT, value=(255,255,255))	
	else:
		image = image[0:height,sx-rx:sx-rx+4800]
	if sy<ry:
		diff_y=6840-height+(ry-sy)
		print("ydirection",ry-sy,diff_y,height)
		image = cv2.copyMakeBorder(image,ry-sy,max(0,diff_y),0,0,cv2.BORDER_CONSTANT, value=(255,255,255))	
	else:
		image = image[sy-ry:sy-ry+6840,0:width]

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
	max_w = int(params.w*1.3)
	max_h = int(params.h*1.3)
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
	erode_mask = cv2.cvtColor(erode_mask,cv2.COLOR_BGR2GRAY) 								#cv2.imshow("",cv2.resize(erode_mask,(700,700)))#cv2.waitKey(0)#cv2.imshow("",cv2.resize(erode_mask,(700,700))) #cv2.waitKey(0)
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
	path = gui.filename.replace(f"{basename}","")	
	basename = basename.replace(".pdf","")
	counter = 1

	name = basename
	while os.path.exists(path+name):
		name = basename + "(" + str(counter) + ")"
		counter += 1
		print(name)
	
	basename = name
	path=path+basename

	if not(os.path.exists(path) and os.path.isdir(path)):
		os.mkdir(path)

	gui.basename = basename
	gui.path = path

	make_pdf(path,basename,students)
	make_csv(path,basename,students,params)
	gui.complete(students)

def make_pdf(path,basename,students):
	marked_pdf = pymupdf.open()
	if not(os.path.exists(f"{path}/single pages") and os.path.isdir(f"{path}/single pages")):
		os.mkdir(f"{path}/single pages")		
	for student in students:	
		student.string = student.name.replace(",", "")
		jpeg_path =f"{path}/single pages/{student.string}.jpg" #need to figure out how to make the zipfile able to add subdir
		student.pil_output= PIL.Image.fromarray(student.scan)
		student.pil_output.save(jpeg_path)
		bytes_scan = pymupdf.open(jpeg_path)                					#bytes_scan = pymupdf.open('png',student.scan)
		pdfbytes = bytes_scan.convert_to_pdf()
		rect = bytes_scan[0].rect                           					#bytes_scan.close()
		pdf_scan = pymupdf.open("pdf", pdfbytes)
		page = marked_pdf._newPage(width=rect.width, height=rect.height)
		page.show_pdf_page(rect,pdf_scan,0) 
	marked_pdf.save(f"{path}/ChilliMark-{basename}.pdf")



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
	for i in range(4):
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
	gui = Gui.Gui()
	gui.home()
	
	params = load_inputs(gui)
	gui.parameters(params)
	

	doc = pymupdf.open(gui.filename) #probably unecessary. remove after getting the returning of image correct
	params.num = len(doc)//10+1
	students = [Student(gui.filename,i,params) for i,_ in enumerate(doc)] 
	pool = multiprocessing.Pool(len(doc)) 
	results = pool.map_async(Student.get,students)
	# manager = multiprocessing.Manager()
	# queue = manager.Queue()
	gui.marking()
	def waiting(results):
		unpickle(results,students)
		corrections(students,gui,params)
		make_output(students,gui,params)

	wait_thread = threading.Thread(target = waiting, args=[results])
	wait_thread.start()

	gui.root.mainloop()
	main()

def unpickle(results,students):
	"""Multiprocess only handles certain types of object. Even with Dill. 
	This function unpacks the results back into class objects. 
	Classes are still used on this side to make managements easier and because I do not want to refactor everything"""
	
	pickles = results.get()
	for i, pickle in enumerate(pickles):
		students[i].scan = pickle[0]
		students[i].responses = pickle[1]
		students[i].score = pickle[2]

		students[i].questions = []
		for q in pickle[3]:

			question = Question(q[0])
			question.response = q[1]

			boxes = []
			for b in q[2]:
				box = Question.Box(b[0],b[1])
				box.colour = b[2]
				box.bool = b[3]
				boxes.append(box)

			question.boxes = boxes
			if question.response_box:
				question.response_box = question.boxes[ord(question.response)-65]
			students[i].questions.append(question)
		students[i].incomplete = [question for question in students[i].questions if not question.response]
		students[i].pil_output = PIL.Image.fromarray(students[i].scan)
		


if __name__ == '__main__':
	main()
	


	