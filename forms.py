# -*- coding: utf-8 -*-

from wtforms import Form, FileField, TextField, validators

class UploadForm(Form):
	upload = FileField('Up')