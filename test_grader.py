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

	#image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
	x,y,w,h = cv2.selectROI(instructions, image)
	if not x:
		return

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
	img = cv2.rectangle(img,(x,y),(x+w,y+h),0,16)
	img = img[y:y+h,x:x+w]
	inner, _ = cv2.findContours(img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)	
	bub_h, bub_w = h, w
	inner = inner[0]
	outer = outer-contour_center(outer)
	inner = inner-contour_center(inner)
	return bub_h, bub_w, outer, inner

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

def find_bubbles(q_area,outer,bub_h, bub_w):
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
 
	limit = 0.8*bub_h*bub_w
	min_w= bub_w*0.8
	min_h = bub_h*0.8
	max_w = bub_w*2
	max_h = bub_h*2
	version = None
	if bub_w>bub_h*2:
		version = "ig"
	for i,c in enumerate(sorted_cnts):

		if cv2.contourArea(c)>limit:#   and 
			x, y, w, h = cv2.boundingRect(c)
			if min_w<= w <= max_w and min_h <= h <= max_h: 
				bubbles.append(outer + contour_center(c))
				continue
			if version == "ig":
				continue
			messy_mask(c,x,y,w,h,q_area,bub_h,bub_w,outer,bubbles)
		elif cv2.contourArea(c)<limit:	

			break
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
	limit = 6*math.sqrt(area)
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

def make_output(marked_work,filename,ans_key_letter,stu_names):
	
	basename = os.path.basename(filename)
	basename = basename.replace(".pdf","")
	path_to_save = filename.replace(".pdf","")
	
	if not(os.path.exists(path_to_save) and os.path.isdir(path_to_save)):
		os.mkdir(path_to_save)

	file = open(f"{path_to_save}/answers.csv", 'w' ,newline='')
	writer = csv.writer(file, dialect='excel', )
	writer.writerow(["Student Name"]+[f"Out of {len(ans_key_letter)}"]+list(ans_key_letter.values()))
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
		


		page = marked_pdf._newPage(width=rect.width, height=rect.height)
		page.show_pdf_page(rect,pdf_scan,0) 

		if i>0:
			stats_raw = zip(stats_raw,mark[2])

	marked_pdf.save(f"{path_to_save}/answers.pdf")
	#deal with stats of answers
	stats = [] 
	options = sorted(set(ans_key_letter.values())) #currently randomly makes 6 choices. Can automate with sets 
	csv_stats = [["Correct"]]
	rates = {"Correct": 0}
	for option in options:
		rates.update({option : 0})
		csv_stats.append([option])       
	for i, row in enumerate(stats_raw):
		rate = rates.copy()
		if i == len(ans_key_letter):
			break
		for ans in row:
			if rate.get(ans)!= None:
				rate[ans]=rate.get(ans) + 1
			if ans == ans_key_letter[i] and ans_key_letter:
				rate["Correct"] = rate.get("Correct") +1
		stats.append(rate.values())

	for row in stats:
		for k, r in enumerate(row):
			csv_stats[k].append(r)

	writer.writerow([""])
	for x in csv_stats:
		writer.writerow([""]+x)

	os.startfile(path_to_save)

def clean_inputs(ans_key_input,stu_names_input):
	
	ans_key_nums={}
	ans_key_letter={}
	stu_names = None

	if ans_key_input:
		ans_key_input = "".join(x for x in ans_key_input if x.isalpha())
		ans_key_input = ans_key_input.upper()
	for i, ans in enumerate(ans_key_input): #should make the ans_key in number rather than letters to prevent repeated conversion    
		ans_key_nums[i]=ord(ans)-65
		ans_key_letter[i]=ans
	if stu_names_input:
		stu_names_input = stu_names_input.title()
		stu_names = stu_names_input.split("\n")

		for i, name in enumerate(stu_names.copy()):
			if not name:
				stu_names.pop(i)
			else:
				stu_names[i]=name.rstrip(", ")
	return stu_names, ans_key_letter, ans_key_nums

def main(filename,ans_key_input=None,stu_names_input=None):

	stu_names, ans_key_letter, ans_key_nums = clean_inputs(ans_key_input,stu_names_input)


	scans = []
	doc = pymupdf.open(filename)
	for page in doc:
		pix = page.get_pixmap(dpi=600, colorspace="RGB")
		image = numpy.frombuffer(buffer=pix.samples, dtype=numpy.uint8).reshape((pix.height, pix.width, -1))
		scans.append(image)

	inner,outer,bub_h,bub_w,text_shift,font_size, y1,x1,y2,x2 = set_parameters(scans)


	marked = []
	icon_bytes = numpy.frombuffer(base64.b64decode("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"), numpy.uint8)
	icon = cv2.imdecode(icon_bytes, cv2.IMREAD_COLOR)
	size = cv2.getTextSize(f"Score = 40 / {len(ans_key_letter)}",cv2.FONT_HERSHEY_SIMPLEX, 5,7)[0]
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
			image= cv2.putText(image,f"Score = {score} / {len(ans_key_letter)}",(4270-size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(255,255,255),15,cv2.LINE_AA)
			image= cv2.putText(image,f"Score = {score} / {len(ans_key_letter)}",(4270-size[0],512),cv2.FONT_HERSHEY_SIMPLEX, 5,(0,0,0),7,cv2.LINE_AA)
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		image[256:512,4288:4544]=icon
		#image = cv2.imencode('.png', image)[1].tobytes()
		marked.append([image,score,let_ans])
		end = time.time()
		print("Loop", end - start)

	
	make_output(marked,filename,ans_key_letter,stu_names)



