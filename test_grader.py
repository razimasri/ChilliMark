import imutils.contours
import imutils
import numpy
import cv2
import time
import math



def select_area(image, instructions="Select Area",blur=False):
	image = image.copy()
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
	while not x:
		x,y,w,h = cv2.selectROI(instructions, image)
	cv2.destroyAllWindows()
	x1= int((x-3)*scale) 
	y1= int((y-3)*scale) 
	x2= int((w+6)*scale) + x1
	y2= int((h+6)*scale) + y1

	return y1,x1,y2,x2,

def manual_bubble(image):
	

	y1,x1,y2,x2 = select_area(image[0:500,0:800],"Select one EMPTY Bubble")
	thresh = get_thresh(image[y1:y2,x1:x2],blur=True)
	outer, _ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	outer=outer[0]
	outer = cv2.approxPolyDP(outer, 0.01*cv2.arcLength(outer, True), True)		

	x, y, w, h = cv2.boundingRect(outer)
	img = cv2.bitwise_not(thresh)
	img = cv2.rectangle(img,(x,y),(x+w,y+h),0,14)
	img = img[y:y+h,x:x+w]
	inner, _ = cv2.findContours(img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	
	bub_h, bub_w = h, w
	inner = inner[0]
	outer = outer-contour_center(outer)
	inner = inner-contour_center(inner)

	return bub_h, bub_w, outer, inner

def get_thresh(image,blur=True):
	if blur:
		image = cv2.medianBlur(image,7)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	return cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25,4)

def	contour_center(contour):
	M = cv2.moments(contour)
	cx = int(M['m10']/M['m00'])
	cy = int(M['m01']/M['m00'])
	return [cx,cy]


def find_bubbles(q_area,outer,bub_h, bub_w):
	"""Goes through contour and returns List of only those of similar size to user defined bubble"""

	start = time.time()
	bubbles = []
	thresh = get_thresh(q_area)
	cnts,hier = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
	version = None
	limit = 0.8*bub_h*bub_w
	min_w= bub_w*0.8
	min_h = bub_h*0.8
	max_w = bub_w*2
	max_h = bub_h*2
	if bub_w>bub_h*2:
		version = "ig"
	for i,c in enumerate(cnts):
		if hier[0][i][3]==-1 and cv2.contourArea(c)>limit:
			x, y, w, h = cv2.boundingRect(c)
			if min_w<= w <= max_w and min_h*0.8 <= h <= max_h: 
				bubbles.append(outer + contour_center(c))
				continue
			if version == "ig":
				continue
			messy_mask(c,x,y,w,h,q_area,bub_h,bub_w,outer,bubbles)		
	end = time.time()
	print("bubbles", end - start)
	return bubbles


def messy_mask(c,x,y,w,h,q_area,bub_h,bub_w,outer,bubbles):
	x_scale = w//bub_w
	y_scale = h//bub_h
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
		if bub_w*0.8<= w <= bub_w*1.4 and bub_h*0.8 <= h <= bub_h*1.4:
			bubbles.append(outer + contour_center(mess))	


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

def find_answers(questions,temp_image,ans_key_nums,ans_key_letter,inner,text_shift,font_size,):

	start = time.time()
	answers = []
	gray = cv2.cvtColor(temp_image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray,(5,5),4)
	thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV| cv2.THRESH_OTSU)[1]
	area = cv2.contourArea(inner)
	limit = 5*math.sqrt(area)
	for q,question in enumerate(questions):
		answer = []
		for bubble in question:
			fill_con = inner + contour_center(bubble)
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
		if ans_key_nums.get(q) != None:
			temp_image = add_markup((0,170,0),question[ans_key_nums.get(q)],ans_key_letter.get(q),temp_image,text_shift,font_size,)	

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
		if answer == ans_key_nums.get(a):
			score+=1
			temp_image = cv2.drawContours(temp_image, questions[a], answer, (0,170,0), 10)
		if type(answer) == int:
			let_answers[a] = chr(answer+65)
			#let_answers[a]
		else:
			let_answers[a] = answer
	end = time.time()
	print("answer", end - start)
	return let_answers, temp_image, score

def set_markup_size(contour,bub_h,bub_w):
	text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, 4, 4)[0]
	text_shift = [0,0]
	if text_size [1]>bub_h*1.2:	
		font_size=3
		text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, font_size, 4)[0]
		text_shift[1] = -bub_h//2
	else:
		font_size=4
		text_shift[1] = bub_h//2+text_size[1]//2
	text_shift[0]=bub_w//2-text_size[0]//2

	return text_shift, font_size

def add_markup(colour,contour,choice,image,text_shift,font_size,):
	x,y,_,_ = cv2.boundingRect(contour)
	text_y = y+text_shift[1]
	text_x = x+text_shift[0]
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,(255,255,255),20,lineType=cv2.LINE_AA) 
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,colour,7,lineType=cv2.LINE_AA) 
	return image



def set_parameters(scans):	#saw some stuff on git on the proper way to do this.

	template = numpy.array(scans[0])
	template = cv2.resize(template,(4800,6835))
	y1,x1,y2,x2 = select_area(template,"Select question area",True)
	bub_h, bub_w, outer,inner = manual_bubble(template[y1:y2,x1:x2]) 
	text_shift, font_size = set_markup_size(outer,bub_h,bub_w)
	return inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2

def process(scans,ans_key_nums,ans_key_letter,inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2):

	marked = []
	score_x,score_y = x1+x2//2,y2+50
	for scan in scans:
		start = time.time()
		image = numpy.array(scan)
		image = cv2.resize(image,(4800,6835))
		q_area = image[y1:y2,x1:x2]
		bubbles = find_bubbles(q_area,outer,bub_h, bub_w)
		columns,choices = sort_into_columns(bubbles)
		questions = find_questions(columns,choices)
		let_ans, q_area, score = find_answers(questions,q_area,ans_key_nums,ans_key_letter,inner,text_shift,font_size,)

		image[y1:y2,x1:x2]=q_area

		if ans_key_letter:
			image= cv2.putText(image,f"Score = {score} / {len(ans_key_letter)}",(score_x,score_y),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA,False)
			image= cv2.putText(image,f"Score = {score} / {len(ans_key_letter)}",(score_x,score_y),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA,False)
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		marked.append([image,score,let_ans])
		end = time.time()
		print("Loop", end - start)
	

	return marked



