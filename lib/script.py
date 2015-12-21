#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.


@author: domos  (domos p vesta at gmail p com)
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time
import traceback
import subprocess
import shlex

class ScriptException(Exception):
	"""
	Script exception
	"""

	def __init__(self, value):
		Exception.__init__(self)
		self.sensorvalue = value

	def __str__(self):
		return repr(self.value)



class Script:
	""" 
	"""

	def __init__(self, log):
		""" 
		"""
		self.log = log
		
		
	def runCmd(self, script, type):
		""" Execute shell command.
			script : 	script (list)
			type :		Script type
		"""
		
		if any(i in script for i in '<|>'):
			self.log.error(u"### Script '%s' is refused: specials characters like '>','<', '|' are not authorized" % script)
			return "failed"
			
		cmd = shlex.split(script.strip())			# For spliting with spaces and quote(s) like a script like: setchacon.sh "salon off" => ['setchacon.sh', 'salon off']

		self.log.info(u"==> Execute subprocess for '%s'" % cmd)		
		try:
			outputcmd = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False).strip()
		except subprocess.CalledProcessError, e:
			self.log.error(u"### Script '%s' failed with error : %d, (%s)" % (script, e.returncode, e.output))
			return "failed"
		except OSError, e: 
			self.log.error(u"### Script '%s' failed with OSerror : %d, (%s)" % (script, e.errno, e.strerror))
			return "failed"

		if  (type == "script_action"): 
			return "executed"
		elif  (type == "script_info_number"): 
			if not self.is_number(outputcmd):
				self.log.error(u"### Script type Number '%s' not return a number: '%s'" % (script, outputcmd))
				return "failed"
		elif  (type == "script_info_binary"): 
			if outputcmd not in ['0', '1']:	
				self.log.error(u"### Script type Binary '%s' not return a binary: '%s'" % (script, outputcmd))
				return "failed"

		return outputcmd	# Return value for "script.info_number | script.info_binary | script.info_string"

			
	def is_number(self, s):
		''' Return 'True' if s is a number
		'''
		try:
			float(s)
			return True
		except ValueError:
			return False


	def runScheduledCmd(self, log, devname, scripttype, script, interval, sendxpl, stop):
		""" Execute shell command evry interval secondes.
			@param 
			devname :		Device name
			scripttype :	Scritp type
			script : 		script (list)
			interval : 		Interval in seconde to execute script
		"""
		while not stop.isSet():
			log.info(u"==> Execute scheduled script '%s' for device '%s' (type %s)" % (script, devname, scripttype))
			resultcmd = self.runCmd(script, scripttype)	
			log.debug(u"==> Send xpl-trig msg for script with return '%s'" % resultcmd)     	# xpl-trig exec.basic { pid='cmd_action|cmd_info' program='/path/program' arg='parameters ...' status='executed|value' }
			sendxpl("xpl-trig", {"program" : script, "type" : scripttype, "status" : resultcmd})
			stop.wait(interval)
	




