

To Do:
C.H.I.L.L.I – Computer Heuristical Input Locus Logical Identifier.


pip install -U tk PyMuPDF pillow opencv-python imutils Nuitka opencv-python numpy


nuitka --onefile --enable-plugin=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icons\Icon.ico --product-version=0.7 ChilliMark.py

Next major changes are
uses classes
change to **kwargs
Have each page process in own thread to allow for error scans
Experiment use Canny insteaf of threshold
way to address unclear answers
reintroduc progress bar
Reintroduce skew and rotation fixing 

