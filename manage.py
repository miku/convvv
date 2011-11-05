#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from flaskext.script import Manager
from flaskext.celery import install_commands as install_celery_commands
from convvv import app

manager = Manager(app)
install_celery_commands(manager)

@manager.command
def hello():
	print "hello"

if __name__ == "__main__":
	manager.run()

