import cv2
import pymupdf
import PIL.Image
import io

doc=pymupdf.open()
image = cv2.imread("linked bubbles.png")
#cv2.imshow("",image)
#cv2.waitKey()
pimage = PIL.Image.fromarray(image)
bio = io.BytesIO()
pimage.save(bio)
pdfimage = pymupdf.open(bio.getvalue())
pdfimage.convert_to_pdf()
rect=pdfimage[0].rect

#PIL.Image._show(pimage)

#pix = pymupdf.Pixmap(image)
doc.insert_page(-1)
for page in doc:
    page._insert_image(stream=pimage)
doc.save("all-my-pics.pdf")


