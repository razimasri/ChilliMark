import cv2
import numpy

image = cv2.imread("tests\ib.png")


def test(image):
	i=3   
	input = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)  
	while i <101:
		#blur = cv2.GaussianBlur(input,(i,i),0) 
		input = cv2.medianBlur(input,i) 
		output = image.copy()
		#cv2.imshow(f"blur is {i}", blur)
		#cv2.waitKey(0)
		j=25
		while j<250:cv2.threshold(input, 200, 200, cv2.THRESH_BINARY_INV)[1]
			thresh = 
			#thresh = cv2.adaptiveThreshold(input,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, i,2)
			cv2.imshow(f"blur is {i} and thres is {j}",thresh)
			cv2.waitKey(0)
			contours,hier = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
			cv2.drawContours(output, contours,-1,(0,0,255))
			cv2.imshow(f"blur is {i} and thres is {j}",output)
			cv2.waitKey(0)
			j+=25
		cv2.destroyAllWindows()
		i+=2


input = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
input = cv2.medianBlur(input,13) 
thresh = cv2.adaptiveThreshold(input,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 29,5)
contours,_ = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
areas = []

in_bub = contours[0]
x_bub = contours[1]


cv2.drawContours(image,[x_bub],-1,(255,0,0))
cv2.imshow("", image)
cv2.waitKey()
