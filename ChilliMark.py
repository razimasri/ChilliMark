import imutils.contours
import imutils
import numpy
import cv2
import time
import math
import base64
import pymupdf
import csv
import os
import PIL
import PIL.Image


#classes to create Students, question, markup

class Parameters:
	def __init__(self,y1,x1,y2,x2):
		self.y1	= y1
		self.x1	= x1
		self.y2 = y2
		self.x2 = x2
		self.outer = []
		self.inner = []
		self.h = 0
		self.w = 0
		self.text_shift = []
		self.font_size = 0 #maybe shift this to markup class
	
	def __str__(self):
		return f"Questions dimensions are {self.h}, {self.w}"
	
	def set_bubble(self,template):
		image = template[self.y1:self.y2,self.x1:self.x2]
		y1,x1,y2,x2 = select_area(image[0:500,0:800],"Select one EMPTY Bubble")
		
		thresh = get_thresh(image[y1:y2,x1:x2],blur=True)
		outer, _ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		outer=outer[0]
		outer = cv2.approxPolyDP(outer, 0.01*cv2.arcLength(outer, True), True)		

		x, y, w, h = cv2.boundingRect(outer)
		img = cv2.bitwise_not(thresh)
		img = cv2.rectangle(img,(x,y),(x+w,y+h),0,16)
		img = img[y:y+h,x:x+w]
		inner, _ = cv2.findContours(img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)	
		if len(inner)==0:
			return inner == False
		inner = inner[0]
		self.h = h
		self.w = w
		self.outer = outer-contour_center(outer)
		self.inner = inner-contour_center(inner)

	def set_markup_size(self):
		text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, 4, 4)[0]
		text_shift = [0,0]
		if text_size [1]>self.h*1.2:	
			self.font_size=3
			text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, self.font_size, 4)[0]
			text_shift[1] = -self.h//2
		else:
			self.font_size=4
			text_shift[1] = self.h//2+text_size[1]//2
		text_shift[0]=self.w//2-text_size[0]//2
		self.text_shift = text_shift

class Student:
	def __init__(self,scan):
		self.name = None
		self.scan = scan
		self.answer = None
	def set_name(self,name):
		self.name = name

def main(filename,key_input=None,names_input=None,first_page=None):
	if not first_page:

		doc = pymupdf.open(filename)
		first_page = doc[0].get_pixmap(dpi=600, colorspace="RGB")

	first_scan = numpy.frombuffer(buffer=first_page.samples, dtype=numpy.uint8).reshape((first_page.height, first_page.width, -1))	
	bub = set_parameters(first_scan)


	students = []
	doc = pymupdf.open(filename)
	start=time.time()

	for page in doc:
		pix = page.get_pixmap(dpi=600, colorspace="RGB")
		image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
		student = Student(image)
		students.append(student)
	end = time.time()
	print("open PDF", end-start)

	key_letter, key_nums = inputs(key_input,names_input,students)	

	icon_bytes = numpy.frombuffer(base64.b64decode("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"), numpy.uint8)
	
	icon = cv2.imdecode(icon_bytes, cv2.IMREAD_COLOR)
	size = cv2.getTextSize(f"Score = 40 / {len(key_letter)}",cv2.FONT_HERSHEY_SIMPLEX, 5,7)[0]

	for student in students: #figure out multithreading or multiprocessing to deal with errors
		process(student,bub,size,icon,key_nums,key_letter)#see what classs can reduce this

	make_output(filename,key_letter,students)

def process(student,bub,size,icon,key_nums,key_letter):
	start = time.time()
	image = numpy.array(student.scan)
	image = cv2.resize(image,(4800,6835))
	q_area = image[bub.y1:bub.y2,bub.x1:bub.x2]
	bubbles = find_bubbles(q_area,bub)
	columns,choices = sort_into_columns(bubbles)
	questions = find_questions(columns,choices)
	let_ans, q_area, score = find_answers(questions,q_area,key_nums,key_letter,bub)

	image[bub.y1:bub.y2,bub.x1:bub.x2] = q_area

	if key_letter:
		image= cv2.putText(image,f"Score = {score} / {len(key_letter)}",(4270-size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
		image= cv2.putText(image,f"Score = {score} / {len(key_letter)}",(4270-size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)
	image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
	image[256:512,4288:4544]=icon
	
	student.scan = image
	student.answer= let_ans
	student.score = score
	end = time.time()
	print("Loop", end - start)

def select_area(image, instructions="Select Area",blur=False):
	if blur:
		image = cv2.GaussianBlur(image,(19,19),3) 

	height, width = image.shape[:2]
	
	scale = height/705
	width = int(width/scale)
	height = 705

	image = cv2.resize(image, (width,height)) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(255, 255, 255),10,lineType=cv2.LINE_AA) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(1, 1, 1),2,lineType=cv2.LINE_AA) 
	cv2.putText(image,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(200, 10, 145),1,lineType=cv2.LINE_AA) 
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
	return cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25,4)

def	contour_center(contour):
	M = cv2.moments(contour)
	cx = int(M['m10']/M['m00'])
	cy = int(M['m01']/M['m00'])
	return [cx,cy]

def find_bubbles(q_area,bub):
	"""Goes through contour and returns List of only those of similar size to user defined bubble"""

	start = time.time()
	bubbles = []
	thresh = get_thresh(q_area)
	cnts,hier = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)

	sorted_cnts = []
	for i, c in enumerate(cnts):
		if hier[0][i][3]==-1:
			sorted_cnts.append(c)
	sorted_cnts = sorted(sorted_cnts, key=cv2.contourArea, reverse=True)

	limit = 0.8*bub.h*bub.w
	min_w= bub.w*0.8
	min_h = bub.h*0.8
	max_w = bub.w*2
	max_h = bub.h*2
	version = None
	if bub.w>bub.h*2:
		version = "ig"
	for i,c in enumerate(sorted_cnts):

		if cv2.contourArea(c)>limit:#   and 
			x, y, w, h = cv2.boundingRect(c)
			if min_w<= w <= max_w and min_h <= h <= max_h: 
				bubbles.append(bub.outer + contour_center(c))
				continue
			if version == "ig":
				continue
			messy_mask(c,x,y,w,h,q_area,bub,bubbles)
		elif cv2.contourArea(c)<limit:	

			break
	end = time.time()
	print("bubbles", end - start)


	return bubbles

def messy_mask(c,x,y,w,h,q_area,bub,bubbles):
	x_scale = w//bub.w
	y_scale = h//bub.h
	mask = numpy.zeros(q_area.shape, dtype="uint8") 
	mask = cv2.drawContours(mask,[c],-1,(255,255,255),-1)
	j=1
	while j<x_scale:
		cv2.line(mask,(x+j*w//x_scale,y-10),(x+j*w//x_scale,y+h+10),(0,0,0),15)
		j+=1
	k=1
	while k<y_scale:
		cv2.line(mask,(x-10,y+k*h//y_scale),(x+w+10,y+k*h//y_scale),(0,0,0),15)
		k+=1
	mask = cv2.cvtColor(mask,cv2.COLOR_RGB2GRAY)
	messy,_= cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	for mess in messy: 
		_, _, w, h = cv2.boundingRect(mess)
		if bub.w*0.8<= w <= bub.w*1.4 and bub.h*0.8 <= h <= bub.h*1.4:
			bubbles.append(bub.outer + contour_center(mess))	

def sort_into_columns(bubbles,img=None):
	"""Sorts them from left to right. 
	Then if the gap between the left side of a bubble is more than half the width of a bubble of the previous it makes a new column
	Columns are then sorted from top to bottom"""
	start = time.time()
	columns = [[]]
	bubbles,_ = imutils.contours.sort_contours(bubbles, method="left-to-right")
	
	prev_x=0
	jump = 1000
	col_index = 0
	count=[1]
	for i, bubble in enumerate(bubbles):	 
		x,_,w,_= cv2.boundingRect(bubble)
		if abs(x-prev_x) > w//2 and i>0:
			col_index +=1
			columns.append([])
			if abs(prev_x-x)/jump > 1.1:
				count.append(0)  
			count[-1] += 1
			jump = x-prev_x
		columns[col_index].append(bubble)
		prev_x = x	
	for item in count:
		if item == count[0]:
			choices = count[0]
		else:
			return print("Detecting inconsistent choice number")
	for i, column in enumerate(columns):
		columns[i],_ = imutils.contours.sort_contours(column, method="top-to-bottom")
	end = time.time()
	print("sort",end - start)
	return columns, choices

def find_questions(columns,choices):
	"""Goes through the columns to buid sets of contours based on use define number of choices"""
	start = time.time()
	questions=[]
	c=0
	while c < len(columns): 
		for r, _ in enumerate(columns[c]):
			i=0
			question=[]
			while i<choices:
				if len(columns[c])>len(columns[c+i]):
					i+=1
					break
				question.append(columns[c+i][r])
				i+=1
			questions.append(question)
		c+=choices
	end = time.time()
	print("questions", end - start)
	return questions

def find_answers(questions,temp_image,key_nums,key_letter,bub):

	start = time.time()
	answers = []
	gray = cv2.cvtColor(temp_image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray,(5,5),4)
	thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1] 
	area = cv2.contourArea(bub.inner)
	limit = 6*math.sqrt(area)
	for q,question in enumerate(questions):

		answer = []	
		for bubble in question:
			fill_con = bub.inner + contour_center(bubble)
			x,y,w,h= cv2.boundingRect(fill_con)
			temp = thresh[y:y+h,x:x+w]
			mask = numpy.zeros(temp.shape, dtype="uint8") 
			mask = cv2.bitwise_and(temp, temp, mask)
			fill = cv2.countNonZero(mask)
			if fill < limit:
				
				fill = 0
			else:
				temp_image = cv2.drawContours(temp_image, [bubble], -1, (200,0,0), 7)
			answer.append(fill)
			
		if key_nums.get(q) != None:
			temp_image = add_markup((0,170,0),question[key_nums.get(q)],key_letter.get(q),temp_image,bub)	

		max_fill = max(answer)
		if not max_fill:
			answers.append("Blank")
		elif answer.count(0) < 3:
			answers.append("Unclear")
		else:
			answers.append(answer.index(max(answer)))
	
	let_answers=answers[:]
	score = 0
	for a, answer in enumerate(answers):
		if answer == key_nums.get(a):
			score+=1
			temp_image = cv2.drawContours(temp_image, questions[a], answer, (0,170,0), 10)
		if type(answer) == int:
			let_answers[a] = chr(answer+65)

		else:
			let_answers[a] = answer
	end = time.time()
	print("answer", end - start)
	return let_answers, temp_image, score

def add_markup(colour,contour,choice,image,bub):
	x,y,_,_ = cv2.boundingRect(contour)
	text_y = y+bub.text_shift[1]
	text_x = x+bub.text_shift[0]
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, bub.font_size,(255,255,255),20,lineType=cv2.LINE_AA) 
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, bub.font_size,colour,7,lineType=cv2.LINE_AA) 
	return image

def set_parameters(first_page):
	template = numpy.array(first_page)
	template = cv2.resize(template,(4800,6835))
	
	y1,x1,y2,x2 = (select_area(template,"Select question area",True))
	bub = Parameters(y1,x1,y2,x2)
	
	while bub.set_bubble(template)==False:
		bub.set_bubble(template)
	bub.set_markup_size()
	return bub

def make_output(filename,key_letter,students):
	
	basename = os.path.basename(filename)
	basename = basename.replace(".pdf","")
	path_to_save = filename.replace(".pdf","")
	
	if not(os.path.exists(path_to_save) and os.path.isdir(path_to_save)):
		os.mkdir(path_to_save)

	file = open(f"{path_to_save}/{basename}.csv", 'w' ,newline='')
	writer = csv.writer(file, dialect='excel', )
	writer.writerow(["Student Name"]+[f"Out of {len(key_letter)}"]+list(key_letter.values()))
	marked_pdf = pymupdf.open()
	#if not(os.path.exists(f"{path_to_save}/single pages") and os.path.isdir(f"{path_to_save}/single pages")):
		#os.mkdir(f"{path_to_save}/single pages")
	stats_raw = []
	for i, student in enumerate(students):
		writer.writerow([student.name]+[student.score]+student.answer)
		string = student.name.replace(",", "")
		student.scan=cv2.putText(student.scan,string,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(255,255,255),25)
		student.scan=cv2.putText(student.scan,string,(512,512),cv2.FONT_HERSHEY_DUPLEX,6,(0,0,0),10)
		#jpeg_path =f"{path_to_save}/single pages/{string}.jpg" #need to figure out how to make the zipfile able to download
		jpeg_path =f"{path_to_save}/{string}.jpg"

		pil_scan = PIL.Image.fromarray(student.scan[:,:,::-1])
		#bio = io.BytesIO()
		#pil_scan.save(bio,"jpeg")
		#bytes_scan = pymupdf.open('jpg',bio.getvalue()) (save incase web version cannot write)
		pil_scan.save(jpeg_path)
		bytes_scan = pymupdf.open(jpeg_path)                #bytes_scan = pymupdf.open('png',student.scan)
		pdfbytes = bytes_scan.convert_to_pdf()
		rect = bytes_scan[0].rect                           #bytes_scan.close()
		pdf_scan = pymupdf.open("pdf", pdfbytes)
		page = marked_pdf._newPage(width=rect.width, height=rect.height)
		page.show_pdf_page(rect,pdf_scan,0) 
		stats_raw.append(student.answer)
	stats_raw= zip(*stats_raw)

	marked_pdf.save(f"{path_to_save}/ChilliMark-{basename}.pdf")
	#deal with stats of answers

	stats = [] 
	options = sorted(set(key_letter.values()))
	csv_stats = [["Correct"]]
	rates = {"Correct": 0}
	for option in options:
		rates.update({option : 0})
		csv_stats.append([option])    

	for i, row in enumerate(stats_raw):
		rate = rates.copy()
		for ans in row:
			if rate.get(ans)!= None:
				rate[ans]=rate.get(ans) + 1
			if ans == key_letter.get(i) and key_letter:
				rate["Correct"] = rate.get("Correct") +1
		stats.append(rate.values())

	for row in stats:
	
		for k, r in enumerate(row):
			csv_stats[k].append(r)

	writer.writerow([""])
	for x in csv_stats:
		writer.writerow([""]+x)


def inputs(key_input,names_input,students):
	
	key_nums={}
	key_letter={}
	stu_names = None
	print(names_input)

	if key_input:
		key_input = "".join(x for x in key_input if x.isalpha())
		key_input = key_input.upper()
	for i, ans in enumerate(key_input):    
		key_nums[i]=ord(ans)-65
		key_letter[i]=ans

	if names_input:
		names_input = names_input.title()
		stu_names = names_input.split("\n")
		
		for i, name in enumerate(stu_names.copy()):
			if name:
				name = name.rstrip(", ")
				stu_names[i]=name.rstrip(", ")
				students[i].set_name(name)
			if not name and i < len(students)//10+1:
				students[i].set_name(f"Student {i+1:0{num}}")
	else:
		num = len(students)//10+1
		for i, student in enumerate(students):
			student.set_name(f"Student {i+1:0{num}}") 
	return key_letter, key_nums

def first_page(filename):
	doc = pymupdf.open(filename)
	return doc[0].get_pixmap(dpi=600, colorspace="RGB")



if __name__ == '__main__':
    main()


