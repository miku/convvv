#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, redirect, render_template, flash, url_for, jsonify
from werkzeug import secure_filename
import base64
import os
import time
import json
import hashlib
import json
import copy
import signal
import shutil
import subprocess, threading


app = Flask(__name__)
app.secret_key = 'cd408d0f0345b5a#933#b081b06b74927c'
app.debug = False
try:
	if os.environ['CONVVV_MODE'] == 'dev':
		app.debug = True
except:
	pass

participants = set()

def interrupted(signum, frame):
	"called when read times out"
	print 'interrupted!'

signal.signal(signal.SIGALRM, interrupted)

BASEPATH = os.path.expanduser('~/github/miku/convvv/storage')
DOWNLOAD_PATH = os.path.expanduser('~/github/miku/convvv/static/downloads')

SERVICE_EXT = {
	"pdftotext" : "txt",
	"pdftohtml" : "html",
	"pdftops" : "ps",
	"pngtojpeg" : "jpg",
	"pngtogif" : "gif",
	"wavtomp3" : "mp3",
	"xlstocsv" : "csv",
	"doctotxt" : "txt",
	"giftojpeg" : "jpg",
	"giftopng" : "png",
	"resumetopdf" : "pdf",
}

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

def get_storage_dir_from_path(path):
	"""
	Return the absolute sha/parts only."""
	return '/'.join(path.split('/')[:-1])

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

def get_expected_path(filename, service, timestamp):
	"""
	Return the expected path for a uploaded (original) file
	and a service, e.g. pdftotext
	"""
	directory = get_storage_dir_from_path(filename)
	return os.path.join(
		directory, '{0}-{1}.{2}'.format(timestamp, service, SERVICE_EXT[service]))

def get_download_path(filename, public=False):
	"""
	For an internal path, get the download path.
	"""
	subdir = '/'.join(filename.split('/')[-3:-1])
	static_directory = os.path.join(os.path.dirname(__file__), 'static')
	basename = os.path.basename(os.path.basename(filename))
	if public == True:
		return os.path.join('downloads', subdir, basename)
	else:
		return os.path.join(DOWNLOAD_PATH, subdir, basename)

def copy_to_download_dir(path):
	target = get_download_path(path, public=False)
	target_directory = os.path.dirname(target)
	if not os.path.exists(target_directory):
		os.makedirs(target_directory)
	shutil.copyfile(path, target)

# Welcome to the web

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.route('/', methods=('GET',))
def hello():
	return redirect(url_for('index'))

@app.route('/doneq', methods=('GET',))
def doneq():
	print request.args['data']
	data = json.loads(request.args['data'])
	for public_handle in data['scheduled']:
		private_handle = get_private_handle(public_handle)
		print 'Checking if arrived:', public_handle, private_handle
		if os.path.exists(private_handle):
			data['scheduled'].remove(public_handle)
			copy_to_download_dir(private_handle)
			try:
				data['links'].append(url_for('static', filename=get_download_path(private_handle, public=True)))
			except KeyError:
				data['links'] = []
				data['links'].append(url_for('static', filename=get_download_path(private_handle, public=True)))
	data.update({ 
		'done' : (0 == len(data['scheduled'])),
		'tries' : data['tries'] + 1
	})
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
		
		timestamp = int(time.time())
		
		print "Got :", storage_obj.content_type
		
		data = {
			'tries' : 0,
			'status' : 200,
			'url' : '/doneq',
			'scheduled' : [],
		}
		
		if storage_obj.content_type == 'application/pdf':
			data.update({
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'pdftotext', timestamp)),
					get_public_handle(get_expected_path(given, 'pdftohtml', timestamp)),
					get_public_handle(get_expected_path(given, 'pdftops', timestamp)),
				]
			})
			
			target = get_expected_path(given, 'pdftotext', timestamp)
			command = Command("pdftotext {0} {1}".format(given, target))
			command.run(timeout=3)

			target = get_expected_path(given, 'pdftohtml', timestamp)
			command = Command("pdftotext {0} {1}".format(given, target))
			command.run(timeout=3)

			target = get_expected_path(given, 'pdftops', timestamp)
			command = Command("pdftops {0} {1}".format(given, target))
			command.run(timeout=3)
			
		elif storage_obj.content_type == 'image/png':
			data.update({
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'pngtojpeg', timestamp)),
					get_public_handle(get_expected_path(given, 'pngtogif', timestamp)),
				]
			})
			
			target = get_expected_path(given, 'pngtojpeg', timestamp)
			command = Command("convert {0} {1}".format(given, target))
			command.run(timeout=3)

			target = get_expected_path(given, 'pngtogif', timestamp)
			command = Command("convert {0} {1}".format(given, target))
			command.run(timeout=3)
		
		elif storage_obj.content_type in ('audio/vnd.wave', 'audio/wav'):
			data.update({
				'status' : 200,
				'url' : '/doneq',
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'wavtomp3', timestamp)),
				]
			})

			target = get_expected_path(given, 'wavtomp3', timestamp)
			command = Command("lame -h -V 0 {0} {1}".format(given, target))
			command.run(timeout=3)
		
		elif storage_obj.content_type == 'application/vnd.ms-excel':

			data.update({
				'status' : 200,
				'url' : '/doneq',
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'xlstocsv', timestamp)),
				]
			})

			target = get_expected_path(given, 'xlstocsv', timestamp)
			command = Command("/usr/bin/env xls2csv {0} > {1}".format(given, target))
			command.run(timeout=3)

		elif storage_obj.content_type == 'application/msword':
			data.update({
				'status' : 200,
				'url' : '/doneq',
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'doctotxt', timestamp)),
				]
			})

			target = get_expected_path(given, 'doctotxt', timestamp)
			command = Command("/usr/bin/env catdoc {0} > {1}".format(given, target))
			command.run(timeout=3)
		
		elif storage_obj.content_type == 'image/gif':
			data.update({
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'giftojpeg', timestamp)),
					get_public_handle(get_expected_path(given, 'giftopng', timestamp)),
				]
			})
			
			target = get_expected_path(given, 'giftojpeg', timestamp)
			command = Command("convert {0} {1}".format(given, target))
			command.run(timeout=3)

			target = get_expected_path(given, 'giftopng', timestamp)
			command = Command("convert {0} {1}".format(given, target))
			command.run(timeout=3)

		elif storage_obj.content_type == 'text/plain':
			data.update({
				'scheduled' : [
					get_public_handle(get_expected_path(given, 'resumetopdf', timestamp)),
				]
			})
			
			target = get_expected_path(given, 'resumetopdf', timestamp)
			# command = Command("pdflatex -jobname={1} {0}".format(given, target))
			command = Command("pdflatex -jobname={1} {0}".format(
				os.path.expanduser('~/github/miku/convvv/templates/resume6.tex'), 
				target[:-4]))
			command.run(timeout=3)

		return jsonify(data=data)

		# now we got hold of the file ...
	return render_template('index.html', flash="Hello")


if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)
