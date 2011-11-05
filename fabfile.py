#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import *

def production():
	env.hosts = ['hdp@phiservera.philol.uni-leipzig.de:22']
	env.directory = '/home/hdp/github/miku/convvv'
	env.activate = 'source /home/hdp/.virtualenvs/convvv/bin/activate'
	env.deploy_user = 'hdp'

def virtualenv(command):
	with cd(env.directory):
		sudo(env.activate + '&&' + command, user=env.deploy_user)

def git_pull():
	'Updates the repository.'
	with cd(env.directory):	   
		sudo('git pull origin master', user=env.deploy_user)

def pip_install_req():
	virtualenv('pip install -r devel-req.txt')

def deploy():
	local('git push origin master')
	git_pull()
	pip_install_req()

# def deploy():
# 	local("git push origin master")
# 	with prefix('workon myvenv'):
# 		run("cd ~/convvv && ls -lah")
