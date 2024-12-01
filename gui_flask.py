from flask import Flask, send_file, render_template, request, flash, redirect, url_for
import chillimark
import os
from waitress import serve
from werkzeug.utils import secure_filename
import zipfile
import shutil
import json

UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app  = Flask (__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods= ['POST','GET'])
def index():

    if request.method == 'POST':
        render_template('submitted.html')
        names = request.form.get('names')
        key = request.form.get('key')
        names = names.replace("\r","")
        filename = upload_file()

        path=os.path.join(app.config['UPLOAD_FOLDER'], filename).replace(".pdf","/")
        zipname= filename.replace(".pdf","")
        
        chillimark.main(os.path.join(app.config['UPLOAD_FOLDER'], filename), key, names)
        
        zipf = zipfile.ZipFile(f'{zipname}.zip','w', zipfile.ZIP_DEFLATED)
        for _,_, files in os.walk(path):
            for file in files:
                zipf.write(path+file,os.path.basename(file))
                os.remove(path+file)
        shutil.rmtree(path)
        zipf.close()
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return send_file(f'{zipname}.zip', mimetype = 'zip', as_attachment = True)
    return render_template('index.html')


def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return

# @app.route('/submitted/<input>', methods= ['POST','GET'])
# def submitted(input):
#     render_template('submitted.html', input=input)
#     filename = input.get(filename)
#     key = input.get(key)
#     names = input.get(names)
    
#     if filename:
#         path=os.path.join(app.config['UPLOAD_FOLDER'], filename).replace(".pdf","/")
#         zipname= filename.replace(".pdf","")
        
#         chillimark.main(os.path.join(app.config['UPLOAD_FOLDER'], filename), key, names)
        
#         zipf = zipfile.ZipFile(f'{zipname}.zip','w', zipfile.ZIP_DEFLATED)
#         for _,_, files in os.walk(path):
#             for file in files:
#                 zipf.write(path+file,os.path.basename(file))
#                 os.remove(path+file)
#         shutil.rmtree(path)
#         zipf.close()
#         os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         return send_file(f'{zipname}.zip', mimetype = 'zip', as_attachment = True)
#     return render_template('submitted.html')


if __name__ == '__main__':

	serve(app, host="0.0.0.0", port=8000)