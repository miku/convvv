from flask import Flask, request, redirect, render_template, flash, url_for
from forms import UploadForm
from werkzeug import secure_filename
import base64
import os
import time
import json

app = Flask(__name__)
app.secret_key = 'cd408d0f0345b5a#933#b081b06b74927c'

# def get_internal_filename(filename, timestamp=None):
# 	if timestamp == None:
# 		timestamp = time.time()
# 	fname, ext = os.path.splitext(filename)
# 	namepart = base64.b64encode(filename)
# 	timepart = base64.b64encode(str(time.time()))
# 	return '{0}-{1}'.format(namepart, timepart)


	
@app.route('/', methods=('GET', 'POST'))
def debug():
	print "XXX"
	for key, value in request.__dict__.items():
		if isinstance(value, dict):
			print key, '==>'
			for k, v in sorted(value.items()):
				print '\t', k, v
		else:
			print key, value
	
	if request.method == 'POST':
		print request.files['x-file-name'].__dict__
		print request.files['x-file-name'].__class__
		print request.files['x-file-name'].content_type
		request.files['x-file-name'].save('/tmp/heyheyhey')
		
	# 	print _file
	# 	if _file:
	# 		filename = secure_filename(_file.filename)
	# 		_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	# 		return redirect(url_for('upload', filename=filename))
	return json.dumps({'img' : '', 'filename' : '', 'path' : ''})

# @app.route('/upload', methods=['GET', 'POST'])
# def upload():
# 	if request.method == 'POST' and 'upload' in request.files:
# 		original_filename = request.files['upload'].filename
# 		filename = media.save(request.files['upload'], name=get_internal_filename(original_filename))
# 		print filename
# 		flash("File uploaded.")
# 		return redirect(url_for('upload'))
# 	return render_template('upload.html')

@app.route("/hello")
def hello():
	return "Hello World!"

if __name__ == "__main__":
	app.run(debug=True)
