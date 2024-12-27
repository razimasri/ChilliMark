![ChilliMark Logo](/icons/Banner.png)
# ChilliMark 


ChilliMark Heuristical Identification of Landmark-Less Input Multiple-choice Answer Recognition Kernel

[Download](https://github.com/razimasri/ChilliMark/blob/1b78ac374ade0c9d9ad71d4611741c46c9f0335e/ChilliMark-Free.exe)

ChilliMark is able to mark some multiple choice sheets without the use of QR code or other landmarks and predefined templates 

It was developed against the multiple choice sheets for the IBDP and IGCSE exams boards. Specifically it was developed for the science version of the multiple choice sheets.

It was designed to match the work flow of teachers who should have ready access to auto-feed scanners. Note: Due to this is does not do any deskewing, only rotation and scaling.

## Features

### No template
Use your own worksheets. You do not need to use any special template. It only works with square boxes for now because it was developed against thh IBDP and Cambridge IGCSE papers. It does technically require one large box on the page that it uses to determine rotation and scale.

### Annotations
Generate annotated pages with the student name, test score, Detected responses, and Correct Answer Key.

![Snippet from IGCSE Cambridge Test](/RDimages/image-7.png)		![Snippet from IBDP Test](/RDimages/image-2.png)

### Output data
Generate a CSV with both each students score and individual question response rates for further processing.

### Clear up ambiguous choices
If two boxes are detected with answers the user can choose the correct questions

## Usage
1. Scan your completed exams using 600 DPI. 

2. Load your PDF - Drag and drop is supported


3. Enter Students names and answer key and hit continue 

![Load Pages](/RDimages/image-3.png)

4. Select the question area and define one empty box. This needs to be quite tightly around the box for the best results. Since this is the box used to detect and understand the image it is worth find the best one free of any scanning artifacts

![Highlight key area](/RDimages/image-4.png)

5. Enter corrections

![Clear up ambiguities](/RDimages/image-5.png)

6. Finished. Review the output for any mistakes. Run again is there are issue. I hope to allow finer corrections in future updates

## Future Improvements
1. Round bubbles
1. Full Manual Mode
1. Resizable Gui
1. Web app
1. Detection realignment
1. Page reordering
1. Multi regions marking
1. JPEG in put
1. Phone and Tablet version
1. IOS Version
1. Appends statistics to a report page

## Known Issues
1. Sometimes the detected boxes do not line up with the real boxes. 
1. Boxes that seem perfectly fine visually are processed differently resulting in errors and rejections.









