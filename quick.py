import tkinter.filedialog
import pymupdf
import PIL.Image
import PIL.ImageTk
import numpy
import math
import test_grader
import cv2
from matplotlib import pyplot
import imutils



#filename = tkinter.filedialog.askopenfilename()
image = cv2.imread("linked bubbles.png")

cv2.imshow("",image)
cv2.waitKey(0)
cv2.destroyAllWindows
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)	
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_TOZERO_INV | cv2.THRESH_OTSU)[1]
cv2.imshow("",thresh)
cv2.waitKey(0)
cv2.destroyAllWindows
contours,_ =cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

#contours = imutils.grab_contours(contours)

cv2.drawContours(image,contours,-1,(0,0,255),10)
cv2.imshow("",image)
cv2.waitKey(0)
cv2.destroyAllWindows

for c in contours:
    x,y,w,h=cv2.boundingRect(c)
    cv2.line(image,(x+w//2,y),(x+w//2,y+h),(255,255,255),10)
    cv2.imshow("",image)
    cv2.waitKey(0)
    cv2.destroyAllWindows







