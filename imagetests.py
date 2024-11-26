import cv2
import pymupdf
import numpy
import time

start= time.time()
doc = pymupdf.open("sample\igsample.pdf")
end= time.time()
print("open",end-start)

start= time.time()
first_page = doc[0].get_pixmap(dpi=70, colorspace="rgb")

end= time.time()
print("pixmap",end-start)
start= time.time()
image = numpy.frombuffer(buffer=first_page.samples, dtype=numpy.uint8).reshape((first_page.height, first_page.width, -1))
#image = numpy.array(first_page)
end= time.time()
print("numpy",end-start)
start= time.time()
image = cv2.resize(image,(500,705))	

end= time.time()
print("resize",end-start)

print(cv2.selectROI("",image))
