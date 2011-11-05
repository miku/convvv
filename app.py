from flask import Flask, request, redirect, render_template, flash, url_for
from forms import UploadForm
from werkzeug import secure_filename
import base64
import os
import time
import json
import hashlib
import json
import copy

app = Flask(__name__)
app.secret_key = 'cd408d0f0345b5a#933#b081b06b74927c'

def get_storage_dir(filelike):
	basepath = os.path.expanduser('~/github/miku/convvv/storage')
	sha1 = hashlib.sha1()
	sha1.update(filelike.read())
	filelike.stream.seek(0) # rewind
	digest = sha1.hexdigest()
	shard, subdir = digest[:2], digest[2:]
	destination = os.path.join(basepath, shard, subdir)
	if not os.path.exists(destination):
		os.makedirs(destination)
	return destination

@app.route('/', methods=('GET', 'POST'))
def index():
	# debugging
	for key, value in request.__dict__.items():
		if isinstance(value, dict):
			print key, '==>'
			for k, v in sorted(value.items()):
				print '\t', k, v
		else:
			print key, value

	if request.method == 'POST':
		# werkzeug.FileStorage
		# http://www.pocoo.org/~blackbird/werkzeug-docs/utils.html
		storage_obj = request.files['x-file-name']
		directory = get_storage_dir(storage_obj)
		filepath = os.path.join(directory, secure_filename(storage_obj.filename))
		
		# metadata ...
		with open(os.path.join(directory, 'headers.json'), 'w') as handle:
			handle.write(json.dumps(storage_obj.headers.to_list()))
		with open(os.path.join(directory, 'content-type.txt'), 'w') as handle:
			handle.write(storage_obj.content_type)
		storage_obj.save(filepath)
		
		# now we got hold of the file ...
	return render_template('index.html')

if __name__ == "__main__":
	app.run(debug=True)
