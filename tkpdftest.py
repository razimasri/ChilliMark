from tkPDFViewer import tkPDFViewer
import tkinter


root = tkinter.Tk()

variable1 = tkPDFViewer.ShowPdf()
variable2 = variable1.pdf_view(root,pdf_location="sample\igsample.pdf",width=0,height=0,bar=True)
variable2.pack()

root.mainloop()


