# import the necessary packages
#from imutils.perspective import four_point_transform
import imutils.contours
import numpy as np
#import argparse
import imutils	
import cv2
from tkinter.filedialog import askopenfilename
from matplotlib import pyplot as plt
#from statistics import mode
#from collections import Counter

def crop_area(image, instructions,blur):

    height, width = image.shape[:2]
    temp = image.copy()
    if height>width:
        scale = height/800
        width = int(width/scale)
        height = 800
    else:
        scale = width/1200
        height = int(height/scale)
        width = 1200
    
    if blur:
    	temp = cv2.GaussianBlur(temp,(5,5),0)
    
    small =cv2.resize(temp, (width,height),cv2.INTER_NEAREST) 
    cv2.putText(small,instructions, (50,75),cv2.FONT_HERSHEY_TRIPLEX, 1,(72, 66, 245),1,lineType=cv2.LINE_AA) 
    x,y,w,h =cv2.selectROI("Select Area", small, fromCenter=False,showCrosshair=True)
    x= int(x*scale) 
    y= int(y*scale) 
    w= int(w*scale) 
    h= int(h*scale)
    
    cropped = image[y:y+h,x:x+w]
    
    return cropped

def get_contour(image,contour_retrieval_mode):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
	cnts,heir = cv2.findContours(thresh, contour_retrieval_mode, cv2.CHAIN_APPROX_SIMPLE)
	
	return cnts, heir 

def manual_bubble():
	

	q_box = crop_area(q_area[0:300,0:300],"Select one Bubble",False)

	cnts,hier = get_contour(q_box,cv2.RETR_EXTERNAL)
	
	areas = []
	for c in cnts:
		areas = cv2.contourArea(c)
	max_index = np.argmax(areas)
	(_, _, w, h) = cv2.boundingRect(cnts[max_index])
	bub_hw = [h,w]

	return bub_hw #q_ratio, 

def find_bubbles(q_area):
    	

	cnts,hier = get_contour(q_area,cv2.RETR_CCOMP)


	for i,c in enumerate(cnts):

		peri=cv2.arcLength(c,True)
		c=cv2.approxPolyDP(c,peri*0.02,True) #approx polly N is not in latest. will need to build from source
		#print(c)
		(_, _, w, h) = cv2.boundingRect(c)
		
		if bub_hw[1]*0.9<= w <= bub_hw[1]*1.1 and bub_hw[0]*0.9 <= h <= bub_hw[0]*1.1 and hier[0][i][3]==-1: #q_ratio*0.9 <= ar <= q_ratio*1.1 and 
			bubbles.append(c)
			
	bubbles_image = cv2.drawContours(q_area.copy(), bubbles, -1, (0,255,0), 3)
	show_image(image,bubbles_image)



def show_image(original,modified):
	plt.subplot(121),plt.imshow(original,cmap = 'gray')
	plt.title('Original Image'), plt.xticks([]), plt.yticks([])
	plt.subplot(122),plt.imshow(modified,cmap = 'gray')
	plt.title('modified Image'), plt.xticks([]), plt.yticks([])
	plt.show()


ANSWER_KEY = {0: 1, 1: 4, 2: 0, 3: 3, 4: 1}
choices = 4

# load the image, and define key areas
filename = askopenfilename()  #need to add pdf and multiple images option

image = cv2.imread(filename)
q_area = crop_area(image.copy(),"Select question area",True)
#s_name = crop_area(image)
bub_hw = manual_bubble() 

#find_bubbles(image)
bubbles=[]
find_bubbles(q_area)

# #print(questionCnts[0])

# #sortbubble, then see number of columns
# columns =[]

# bubbles = imutils.contours.sort_contours(bubbles, method="left-to-right")
# bubbles = imutils.grab_contours(bubbles)

# prev=0
# for i, bubble in enumerate(bubbles):
#     x,y,w,h= cv2.boundingRect(bubble)
    
    

