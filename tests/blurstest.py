import cv2

image = cv2.imread("tests\ig.png")


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
		while j<250:
			thresh = cv2.threshold(input, 200, 200, cv2.THRESH_BINARY_INV)[1]
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
contours,hier = cv2.findContours(thresh,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
	cv2.drawContours(image, contours,-1,(0,0,255),1,cv2.LINE_AA)
	cv2.imshow(f"blur is {15} and thres is {200}",image)
	cv2.waitKey(0)