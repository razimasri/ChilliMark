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

def crop_area(image):
    #find height of image and scale to be 800 pixels
    #show shrunken image, select box,
    #return coordinates. 
    # this will also be used in the future to highlight and store the student name
    height, width = image.shape[:2]
    
    if height>width:
        scale = height/800
        width = int(width/scale)
        height = 800
    else:
        scale = width/1200
        height = int(height/scale)
        width = 1200
    
    small =cv2.resize(image , (width,height),cv2.INTER_NEAREST) 
    
    x,y,w,h =cv2.selectROI("Select Area", small, fromCenter=False,showCrosshair=True)
    x= int(x*scale) 
    y= int(y*scale) 
    w= int(w*scale) 
    h= int(h*scale)
    
    cropped = image[y:y+h,x:x+w]
    
    return cropped

def manual_bubble():
	
	q_row = crop_area(q_area)
	q_box = crop_area(q_row)
	bub_hw = q_box.shape[:2]
	#q_ratio = bub_hw[1]/bub_hw[0]
	return bub_hw #q_ratio, 

def find_bubbles(q_area):
    
	gray = cv2.cvtColor(q_area, cv2.COLOR_BGR2GRAY)		#i don't think this section is needed if i scan them in vs camera
	thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]	
	# find contours in the thresholded image, then initialize
	# the list of contours that correspond to questions
	cnts,hier = cv2.findContours(thresh.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
	#cnts = imutils.grab_contours(cnts)
	#print(cnts[0][-1])
	#Need to add first try an auto detect based on most frequent. if fail then go through the select on smaller areas
	for i,c in enumerate(cnts):
		#compute the bounding box of the contour, then use the bounding box to derive the aspect ratio
		
		#ar = w / float(h)
		peri=cv2.arcLength(c,True)
		c=cv2.approxPolyDP(c,peri*0.02,True) #approx polly N is not in latest. will need to build from source
		#print(c)
		(x, y, w, h) = cv2.boundingRect(c)
		
		if bub_hw[1]*0.7<= w <= bub_hw[1]*1.3 and bub_hw[0]*0.7 <= h <= bub_hw[0]*1.3 and hier[0][i][3]==-1: #q_ratio*0.9 <= ar <= q_ratio*1.1 and 
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
q_area = crop_area(image)
#s_name = crop_area(image)
bub_hw = manual_bubble() #no need to improve upon manual bubbles yet until i program the auto way

#find_bubbles(image)
bubbles=[]
find_bubbles(q_area)

#print(questionCnts[0])

#sortbubble, then see number of columns
columns =[]

bubbles = imutils.contours.sort_contours(bubbles, method="left-to-right")
bubbles = imutils.grab_contours(bubbles)

prev=0
for i, bubble in enumerate(bubbles):
    x,y,w,h= cv2.boundingRect(bubble)
    print(x)
    

