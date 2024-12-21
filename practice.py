import time
import pymupdf

filename="gui_desk.onefile-build\D&D 5E - Tomb of Annihilation.pdf"

doc = pymupdf.open(filename)

#maybe over here. make it return just the list
doc = pymupdf.open(filename) #probably unecessary. remove after getting the returning of image correct
num = len(doc)//10+1
start=time.time()
#students = [] 
pages = [] #creating tupples to pass to the parallel processing function
for i,_ in enumerate(doc): #get this running in the background while doing get parameters
	#student = Student(f"Student {i+1:0{num}}")
	#students.append(student)
	pages.append([filename,i])

print("Loops",time.time()-start)

start=time.time()
pages=[[filename,i,params] for i,_ in enumerate(doc)]


print("List",time.time()-start)
#print(hier)