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

import traceback
import subprocess


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
		
		
	def run_cmd(self, cmd, type):
		""" Execute shell command.
		"""
		self.log.info("### Execute subprocess '%s'" % cmd)
		try:
			outputcmd = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False)
		except subprocess.CalledProcessError, e:
			self.log.error("### Command '%s' failed with error : %d, (%s)" % (cmd, e.returncode, e.output))
			return "failed"
		except OSError, e: 
			self.log.error("### Command '%s' failed with OSerror : %d, (%s)" % (cmd, e.errno, e.strerror))
			return "failed"

		if  (type == "cmd_action"): 
			return "executed"
		else:
			if not self.is_number(outputcmd):
				self.log.error("### Sensor DT_Number Command '%s' not return a number: '%s'" % (cmd, outputcmd))
				return "failed"
			return outputcmd.rstrip()

			
	def is_number(self, s):
		try:
			float(s)
			return True
		except ValueError:
			return False


	def script_info_number(self, log, devname, script, interval, sendxpl, stop):
		while not stop.isSet():
			time.sleep(interval)
	
	def script_info_binary(self, log, devname, script, interval, sendxpl, stop):	

		while not stop.isSet():
			time.sleep(interval)





