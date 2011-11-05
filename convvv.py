from flask import Flask, request, redirect, render_template, flash, url_for, jsonify
from forms import UploadForm
from werkzeug import secure_filename
import base64
import os
import time
import json
import hashlib
import json
import copy
import signal
import subprocess, threading


app = Flask(__name__)
app.secret_key = 'cd408d0f0345b5a#933#b081b06b74927c'
app.debug = True

participants = set()

def interrupted(signum, frame):
	"called when read times out"
	print 'interrupted!'

signal.signal(signal.SIGALRM, interrupted)

BASEPATH = os.path.expanduser('~/github/miku/convvv/storage')

class Command(object):
	"""
	Interesting find on SO:
	http://stackoverflow.com/questions/1191374/subprocess-with-timeout
	Usage //
	command = Command("echo 'Process started'; sleep 2; echo 'Process finished'")
	command.run(timeout=3)
	command.run(timeout=1)
	"""
	def __init__(self, cmd):
		self.cmd = cmd
		self.process = None

	def run(self, timeout):
		def target():
			print 'Thread started'
			self.process = subprocess.Popen(self.cmd, shell=True)
			self.process.communicate()
			print 'Thread finished'

		thread = threading.Thread(target=target)
		thread.start()

		thread.join(timeout)
		if thread.is_alive():
			print 'Terminating process'
			self.process.terminate()
			thread.join()
		print self.process.returncode

def get_storage_dir(filelike):
	sha1 = hashlib.sha1()
	sha1.update(filelike.read())
	filelike.stream.seek(0) # rewind
	digest = sha1.hexdigest()
	shard, subdir = digest[:2], digest[2:]
	destination = os.path.join(BASEPATH, shard, subdir)
	if not os.path.exists(destination):
		os.makedirs(destination)
	return destination

def get_public_handle(filename):
	"""
	Shorten something like 
	~/github/miku/convvv/storage/ae/c9d4259d467c0883b10bdb584fe7add7e42c20/Getting_Started.pdf 
	to ae/c9d4259d467c0883b10bdb584fe7add7e42c20/Getting_Started.pdf
	"""
	return '/'.join(filename.split('/')[-3:])

def get_private_handle(filename):
	"""
	Inverse of get_public_handle()
	"""
	return os.path.join(BASEPATH, filename)

@app.route('/', methods=('GET',))
def hello():
	return redirect(url_for('index'))


@app.route('/doneq', methods=('GET',))
def doneq():
	data = {
		'stillinq' : 2,
		'done' : ['url_to_coverted_file_1', 'url_to_coverted_file_2']
	}
	return jsonify(data=data)

@app.route('/index/', methods=('GET', 'POST'))
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
		given = os.path.join(directory, secure_filename(storage_obj.filename))
		
		# metadata ...
		with open(os.path.join(directory, 'headers.json'), 'w') as handle:
			handle.write(json.dumps(storage_obj.headers.to_list()))
		with open(os.path.join(directory, 'content-type.txt'), 'w') as handle:
			handle.write(storage_obj.content_type)
		storage_obj.save(given)
		
		if storage_obj.content_type == 'application/pdf':
			timestamp = int(time.time())
			data = {
				'status' : 200,
				'url' : '/doneq',
				'scheduled' : 
					{ 'given' : get_public_handle(given), 'converter' : 'pdftotext' },
				# add more here
			}
			# text_file = os.path.join(directory, 'out.{0}.pdftotext.txt'.format(int(time.time())))
			# 
			# command = Command("pdftotext {0} {1}".format(given, text_file))
			# command.run(timeout=3)

		return jsonify(data=data)

		# now we got hold of the file ...
	return render_template('index.html')


if __name__ == "__main__":
	app.run(debug=True)