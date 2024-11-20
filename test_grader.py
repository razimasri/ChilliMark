# import the necessary packages
# as a beginner I am avoiding renaming and only importing specifics so that I can be clear where each thing comes from
#from imutils.perspective import four_point_transform #will needto import again when I deal with scans

import imutils.contours
import imutils

import numpy
import cv2
import tkinter
import tkinter.messagebox

from matplotlib import pyplot

def select_area(image, instructions="Select Area",blur=False):
    """ Create temporary small version then rescale to input image"""
    
    height, width = image.shape[:2]
    
    temp = image.copy()
    if blur:
        temp = cv2.GaussianBlur(temp,(5,5),0) 
    scale = height/705
    width = int(width/scale)
    height = 705

    
    temp = cv2.resize(temp, (width,height)) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(255, 255, 255),10,lineType=cv2.LINE_AA) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(1, 1, 1),2,lineType=cv2.LINE_AA) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(200, 10, 145),1,lineType=cv2.LINE_AA) 
    
    x,y,w,h = cv2.selectROI(instructions, temp, fromCenter=False,showCrosshair=True)
    x= int((x-3)*scale) 
    y= int((y-3)*scale) 
    w= int((w+6)*scale) 
    h= int((h+6)*scale)
    
    cv2.destroyAllWindows()
    
    return [y,x,h,w]

def manual_bubble():
	yxhw = select_area(q_area[0:500,0:800],"Select one EMPTY Bubble")
	q_box = q_area[yxhw[0]:yxhw[0]+yxhw[2],yxhw[1]:yxhw[1]+yxhw[3]]
	cnts,hier = get_contour(q_box,cv2.RETR_EXTERNAL,False)
	areas = []
	for c in cnts:
		areas.append(cv2.contourArea(c))

	bub = cnts[numpy.argmax(areas)]
	bub = cv2.approxPolyDP(bub, 0.01*cv2.arcLength(bub, True), True)
		
	(_, _, w, h) = cv2.boundingRect(bub)

	bub_hw = [h,w]
	bub = bub-contour_center(bub)

	return bub_hw, bub

def get_contour(image,contour_retrieval_mode,blur=True):
	thresh = get_thresh(image)
	cnts,heir = cv2.findContours(thresh, contour_retrieval_mode, cv2.CHAIN_APPROX_SIMPLE)

	return cnts, heir 

def get_thresh(image,blur=True):
    
    if blur:
        image = cv2.GaussianBlur(image,(5,5),0)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    return thresh

def check_fill(contour,image):
	
    thresh = get_thresh(image,False)
    mask = create_mask(thresh,contour)
    fill = cv2.countNonZero(mask)
    
    return fill

def create_mask(thresh,contour):
    
    mask = numpy.zeros(thresh.shape, dtype="uint8") 
    x,y,w,h = cv2.boundingRect(contour)
    mask = cv2.rectangle(mask, (x+10,y+10),(x+w-20,y+h-20),(255,255,255),-1)
    
    mask = cv2.bitwise_and(thresh, thresh, mask=mask)	
    
    
    return mask

def	contour_center(cnt):
	M = cv2.moments(cnt)
	cx = int(M['m10']/M['m00'])
	cy = int(M['m01']/M['m00'])
	return [cx,cy]

def find_bubbles(bub_hw,bub):
	"""Goes through contour and returns List of only those of similar size to user defined bubble"""

	global q_area

	bubbles = []
	cnts,hier = get_contour(q_area,cv2.RETR_CCOMP)

	for i,c in enumerate(cnts):
		(x, y, w, h) = cv2.boundingRect(c)
		add_good_bubble(bubbles,c,hier,i)
		#turn into missing bubbles function?
		if bub_hw[1]*2<w<bub_hw[1]*4 or bub_hw[0]*2<w<bub_hw[0]*4: #this is where i can alter the logic to get if the box is close to multiples
				
			x_scale = w//bub_hw[1]
			y_scale = h//bub_hw[0]

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

			mask =cv2.bitwise_not(mask)
			mask=get_thresh(mask,False)
			#show_image(q_area,mask)
			messy,_= cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
			for mess in messy: 
				add_good_bubble(bubbles,mess)

	return bubbles

def add_good_bubble(array, c, hier=[[[0,0,0,-1]]],i=0):
	peri=cv2.arcLength(c,True)
	c=cv2.approxPolyDP(c,peri*0.02,True) #approx polly N is not in latest. will need to build from source
	(x, y, w, h) = cv2.boundingRect(c)
	if bub_hw[1]*0.8<= w <= bub_hw[1]*1.3 and bub_hw[0]*0.9 <= h <= bub_hw[0]*1.3 and hier[0][i][3]==-1: #q_ratio*0.9 <= ar <= q_ratio*1.1 and 
		bub_img = q_area.copy()	
		
		#This maps the default empty bubble onto all
		array.append(bub + contour_center(c))	

def sort_into_columns(bubbles):
	"""Sorts them from left to right. 
	Then if the gap between the left side of a bubble is more than half the width of a bubble of the previous it makes a new column
	Columns are then sorted from top to bottom"""

	columns = [[]]
	bubbles,_ = imutils.contours.sort_contours(bubbles, method="left-to-right")
	prev_x=0
	jump = 1000
	col_index = 0
	temp_image = q_area.copy()
	count=[1]
	for i, bubble in enumerate(bubbles):	 
		x,y,w,h= cv2.boundingRect(bubble)
		
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
		colour_index = (i%choices) 
		cv2.drawContours(temp_image, columns[i], -1, colours[colour_index], 10)

	#show_image(q_area,temp_image)
	#missing_bubbles(temp_image)

	return columns, choices

	
def find_questions(columns,choices):
	"""Goes through the columns to buid sets of contours based on use define number of choices"""

	temp_image = q_area.copy()
	questions=[]
	c=0
	while c < len(columns): #did not use zip as I would have to import zip longest to iterate through flexible choices lenght
		for r, row in enumerate(columns[c]):
			i=0
			question=[]
			while i<choices:
				question.append(columns[c+i][r])
				i+=1
				

			questions.append(question)
		c+=choices
	
	for q, question in enumerate(questions):
		cv2.drawContours(temp_image, question, -1, colours[q%6], 3)
	
	return questions

def find_answers(questions):
	answers = []
	temp_image = q_area.copy()
	for q,question in enumerate(questions):
		answer = []
		for b,bubble in enumerate(question):
			fill = check_fill(question[b],q_area)
			if fill <700:
				fill = 0
			else:
				temp_image = cv2.drawContours(temp_image, question, b, colours[0], 3)
				#print(fill)
			
			answer.append(fill)
		if ans_key_nums.get(q) != None:
			temp_image = add_markup(colours[1],question[ans_key_nums.get(q)],ans_key_letters.get(q),temp_image)	
		max_fill = max(answer)
		if not max_fill:
			answers.append("Blank")
		elif answer.count(0) < 3:
			answers.append("Unclear")
			#clarify() need to make this once i get better with UI
		else:
			answers.append(answer.index(max(answer)))
			
		
	
	let_answers=answers[:]
	score = 0
	for a, answer in enumerate(answers):
		if answer == ans_key_nums.get(a):
			score+=1
			temp_image = cv2.drawContours(temp_image, questions[a], answer, colours[1], 5)
		if type(answer) == int:
			let_answers[a] = chr(answer+65)
			let_answers[a]
		else:
			let_answers[a] = answer

	temp_image= cv2.putText(temp_image,"Score = " + str(score) + "/"+ str(len(ans_key_letters)),(50,50),cv2.FONT_HERSHEY_SIMPLEX, 2,(0,0,0),4,cv2.LINE_AA)
	show_image(temp_image)

	#show_image(q_area,temp_image)
		
	return answers, let_answers, temp_image, score

def set_markup_size(contour):
	global bub_hw
	h=bub_hw[0]
	w=bub_hw[1]

	text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, 4, 4)[0]
	text_shift = [0,0]
	if text_size [1]>h*1.2:	
		font_size=1.5
		text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, font_size, 4)[0]
		text_shift[1] = -h//2
	else:
		font_size=4
		text_shift[1] = h//2+text_size[1]//2
	
	text_shift[0]=w//2-text_size[0]//2

	return text_shift, font_size

def add_markup(colour,contour,choice,image):
	x,y,_,_ = cv2.boundingRect(contour)
	text_y = y+text_shift[1]
	text_x = x+text_shift[0]
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,(255,255,255),15,lineType=cv2.LINE_AA) 
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,colour,4,lineType=cv2.LINE_AA) 
	return image

def show_image(original,modified=None):
	pyplot.subplot(121),pyplot.imshow(original,cmap = 'gray')
	pyplot.title('Original Image'), pyplot.xticks([]), pyplot.yticks([])
	if modified: 
		pyplot.subplot(122),pyplot.imshow(modified,cmap = 'gray')
		pyplot.title('modified Image'), pyplot.xticks([]), pyplot.yticks([])
	pyplot.show()

def main(scan,ans_nums,ans_letters):	#saw some stuff on git on the proper way to do this.

	global colours, text_shift, font_size, q_area,ans_key_nums,ans_key_letters, bub, bub_hw

	ans_key_nums = ans_nums
	ans_key_letters = ans_letters

	colours = [(200,0,0),(0,170,0),(0,0,200),(220,200,0),(200,0,200),(0,200,200)] 
	image = numpy.array(scan)
	yxhw = select_area(image,"Select question area",True)
	
	q_area = image[yxhw[0]:yxhw[0]+yxhw[2],yxhw[1]:yxhw[1]+yxhw[3]]
	bub_hw, bub = manual_bubble() 
	text_shift, font_size = set_markup_size(bub)
	bubbles = find_bubbles(bub_hw,bub)
	columns,choices = sort_into_columns(bubbles)	#if jump//jump==1 count, if all counts agree, set as choices. otherwise prompt to ask?
	questions = find_questions(columns,choices)
	#split here
	_, let_ans, marked_img, score = find_answers(questions)

	
	
	return [let_ans, score, marked_img]


    
    

