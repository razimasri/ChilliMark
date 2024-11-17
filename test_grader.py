# import the necessary packages
# as a beginner I am avoiding renaming and only importing specifics so that I can be clear where each thing comes from
#from imutils.perspective import four_point_transform #will needto import again when I deal with scans
import tkinter.filedialog
import imutils.contours
import imutils
import PIL
import numpy
import cv2
import tkinter
#from tkinter.filedialog import askopenfilename
from matplotlib import pyplot

def crop_area(image, instructions="Select Area",blur=False):
    """ Create temporary small version then rescale to input image"""
    
    height, width = image.shape[:2]
    temp = image.copy()
    if blur:
    	temp = cv2.GaussianBlur(temp,(5,5),0)
    
    if height>width:
        scale = height/800
        width = int(width/scale)
        height = 800
    else:
        scale = width/1200
        height = int(height/scale)
        width = 1200
    
    temp = cv2.resize(temp, (width,height)) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(255, 255, 255),10,lineType=cv2.LINE_AA) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(1, 1, 1),2,lineType=cv2.LINE_AA) 
    cv2.putText(temp,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(200, 10, 145),1,lineType=cv2.LINE_AA) 
    
    x,y,w,h = cv2.selectROI(instructions, temp, fromCenter=False,showCrosshair=True)
    x= int((x-5)*scale) 
    y= int((y-5)*scale) 
    w= int((w+10)*scale) 
    h= int((h+10)*scale)
    
    return image[y:y+h,x:x+w]

def get_thresh_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)	
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]	
    return thresh

def get_contour(image,contour_retrieval_mode):
	cnts,heir = cv2.findContours(get_thresh_image(image), contour_retrieval_mode, cv2.CHAIN_APPROX_SIMPLE)
	#single line why is this its own function?
	return cnts, heir 

def check_fill(contour,thresh,index):
    mask = numpy.zeros(thresh.shape, dtype="uint8") 
    mask = cv2.drawContours(mask, contour, index, 255, -1)
    mask = cv2.bitwise_and(thresh, thresh, mask=mask)	
    #show_image(thresh, mask)
    fill = cv2.countNonZero(mask)
    return fill

def manual_bubble(q_area):
	
	q_box = crop_area(q_area[0:300,0:400],"Select one EMPTY Bubble")

	cnts,hier = get_contour(q_box,cv2.RETR_EXTERNAL)
	
	areas = []
	for c in cnts:
		areas.append(cv2.contourArea(c))

	bub = cnts[numpy.argmax(areas)]
	(_, _, w, h) = cv2.boundingRect(bub)
	bub_hw = [h,w]
	bub_fill = check_fill(cnts,get_thresh_image(q_box),-1)
	
	bub -= contour_center(bub)
	return bub_hw, bub_fill, bub

def	contour_center(cnt):
	M = cv2.moments(cnt)
	cx = int(M['m10']/M['m00'])
	cy = int(M['m01']/M['m00'])
	return [cx,cy]

def find_bubbles(q_area):
	"""Goes through contour and returns List of only those of similar size to user defined bubble"""

	bubbles = []
	cnts,hier = get_contour(q_area,cv2.RETR_CCOMP)

	for i,c in enumerate(cnts):
		peri=cv2.arcLength(c,True)
		c=cv2.approxPolyDP(c,peri*0.02,True) #approx polly N is not in latest. will need to build from source
		(_, _, w, h) = cv2.boundingRect(c)
		if bub_hw[1]*0.8<= w <= bub_hw[1]*1.3 and bub_hw[0]*0.9 <= h <= bub_hw[0]*1.3 and hier[0][i][3]==-1: #q_ratio*0.9 <= ar <= q_ratio*1.1 and 
			
			#This maps the default empty bubble onto all
			bubbles.append(bub + contour_center(c))	

	return bubbles

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
		cv2.drawContours(temp_image, columns[i], -1, colours[colour_index], 3)
		
		


	show_image(q_area,temp_image)
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
	
	show_image(q_area,temp_image)
	return questions

def find_answers(q_area,questions,bub_fill):
	answers = []
	temp_image = q_area.copy()
	q_thresh = get_thresh_image(q_area)
	for q,question in enumerate(questions):
		answer = []
		for b,bubble in enumerate(question):
			#break out this mask into a function so I can 
			fill = check_fill(question,q_thresh,b)
			if fill < bub_fill*1.3:
				fill = 0
			else:
				#temp_image = add_markup(colours[0],bubble,key.get(b),temp_image)
				temp_image = cv2.drawContours(temp_image, question, b, colours[0], 3)	
			answer.append(fill)
		
		max_fill = max(answer)
		if not max_fill:
			answers.append("Blank")
		elif answer.count(0) < 3:
			answers.append("Unclear")
		else:answers.append(answer.index(max(answer)))
		
		if ANSWER_KEY.get(q) != None:
			temp_image = add_markup(colours[1],question[ANSWER_KEY.get(q)],key.get(ANSWER_KEY.get(q)),temp_image)
			temp_image = cv2.drawContours(temp_image, question, ANSWER_KEY.get(q), colours[1], 3)		
	show_image(q_area,temp_image)
		
	let_answers=answers[:]

	for a, answer in enumerate(answers):
		let_answers[a] = key.get(answer)

	return answers, let_answers, temp_image
def set_markup_size(contour):
	_,_,w,h = cv2.boundingRect(contour)
	text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, 3, 3)[0]
	text_shift = [0,0]
	if text_size [1]>h:	
		font_size=1.5
		text_size = cv2.getTextSize("A",cv2.FONT_HERSHEY_SIMPLEX, font_size, 3)[0]
		text_shift[1] = -h//2
	else:
		font_size=3
		text_shift[1] = h//2+text_size[1]//2
	
	text_shift[0]=w//2-text_size[0]//2

	return text_shift, font_size

def add_markup(colour,contour,choice,image):
	x,y,_,_ = cv2.boundingRect(contour)
	text_y = y+text_shift[1]
	text_x = x+text_shift[0]
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,(255,255,255),15,lineType=cv2.LINE_AA) 
	cv2.putText(image,choice, (text_x,text_y),cv2.FONT_HERSHEY_SIMPLEX, font_size,colour,3,lineType=cv2.LINE_AA) 
	return image

def get_score(let_ans,ANSWER_KEY):
	score = 0
	for a, answer in enumerate(let_ans):
		if answer == ANSWER_KEY.get(a):
			score+=1
	return score

def show_image(original,modified):
	pyplot.subplot(121),pyplot.imshow(original,cmap = 'gray')
	pyplot.title('Original Image'), pyplot.xticks([]), pyplot.yticks([])
	pyplot.subplot(122),pyplot.imshow(modified,cmap = 'gray')
	pyplot.title('modified Image'), pyplot.xticks([]), pyplot.yticks([])
	pyplot.show()

key = {0:"A",1:"B",2:"C",3:"D",4:"E",5:"F", "Unclear":"Unclear"}
ANSWER_KEY = {0: 0, 1: 1, 2: 1, 3: 2, 4:1} #do not turn into list. otherwise i>ans_key will return error

#choices = 4
colours = [(200,0,0),(0,200,0),(0,0,200),(220,200,0),(200,0,200),(0,200,200)] #this can be related to binary 1-6 backwards

# load the image, and define key areas
filename = tkinter.filedialog.askopenfilename()  #need to add pdf and multiple images option
image = cv2.imread(filename)
q_area = crop_area(image.copy(),"Select question area",True)
bub_hw, bub_fill, bub = manual_bubble(q_area) 
text_shift, font_size = set_markup_size(bub)
bubbles = find_bubbles(q_area)
columns,choices = sort_into_columns(bubbles)	#if jump//jump==1 count, if all counts agree, set as choices. otherwise prompt to ask?
questions = find_questions(columns,choices)
num_ans, let_ans, marked_img = find_answers(q_area,questions,bub_fill)

score = get_score(num_ans,ANSWER_KEY)

print(score)

    
    

