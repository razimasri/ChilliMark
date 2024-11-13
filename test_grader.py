# import the necessary packages
from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
#import argparse
import imutils
import cv2
from tkinter.filedialog import askopenfilename
from matplotlib import pyplot as plt



def crop_area(image):
    #find height of image and 
    #scale to be slightly smaller than 900ish pixels
    #show shrunken image, select box,
    #return coordinates. 
    # this will also be used in the future to highlight and store the student name
    #as secotn function or as multiple regions of interest
    height, width = image.shape[:2]
    scale = height/800
    width = int(width/scale)
    
    small =cv2.resize(image , (width,800),cv2.INTER_NEAREST) 
    
    x,y,w,h =cv2.selectROI("Select Area", small, fromCenter=False,showCrosshair=True)
    x= int(x*scale) 
    y= int(y*scale) 
    w= int(w*scale) 
    h= int(h*scale)
    
    cropped = image[y:y+h,x:x+w]
    
    return cropped
    
def show_image(original,modified):
	plt.subplot(121),plt.imshow(original,cmap = 'gray')
	plt.title('Original Image'), plt.xticks([]), plt.yticks([])
	plt.subplot(122),plt.imshow(modified,cmap = 'gray')
	plt.title('modified Image'), plt.xticks([]), plt.yticks([])
	plt.show()

# construct the argument parse and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", required=True,
	#help="path to the input image", default="omr_test_01.png" )
#args = vars(ap.parse_args())

# define the answer key which maps the question number
# to the correct answer
ANSWER_KEY = {0: 1, 1: 4, 2: 0, 3: 3, 4: 1}

# load the image, convert it to grayscale, blur it
# slightly, then find edges
filename = askopenfilename()  #need to add pdf and multiple images option

image = cv2.imread(filename)

#This will have to become a function, question area.


q_area = crop_area(image)
q_row = crop_area(q_area)
q_box = crop_area(q_row)


q_h_w = q_box.shape[:2]
q_ratio = q_h_w[1]/q_h_w[0]


gray = cv2.cvtColor(q_area, cv2.COLOR_BGR2GRAY)		#i don't think this section is needed if i scan them in vs camera


thresh = cv2.threshold(gray, 0, 255,			
	cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]		

# find contours in the thresholded image, then initialize
# the list of contours that correspond to questions
cnts = cv2.findContours(thresh.copy(), cv2.RETR_LIST,
	cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
questionCnts = []
#loop over the contours
for c in cnts:
	#compute the bounding box of the contour, then use the
	#bounding box to derive the aspect ratio
	(x, y, w, h) = cv2.boundingRect(c)
	ar = w / float(h)
	#in order to label the contour as a question, region
	#should be sufficiently wide, sufficiently tall, and
	#have an aspect ratio approximately equal to 1
		#note this is not true for my one
	
	if ar >= q_ratio*0.8 and ar <= q_ratio*1.2:
		questionCnts.append(c)

print(questionCnts)


unculled = cv2.drawContours(q_area.copy(), cnts, -1, (0,255,0), 3)
culled = cv2.drawContours(q_area.copy(), questionCnts, -1, (0,255,0), 3)

#cv2.imshow('Contours', image)
#cv2.waitKey(0) 
#cv2.destroyAllWindows()

show_image(image,culled)

