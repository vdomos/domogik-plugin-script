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

Plugin purpose
==============

Run script for a command or a script for a sensor.

Implements
==========


@author: domos  (domos p vesta at gmail p com)
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin

from domogik_packages.plugin_script.lib.script import Script
from domogik_packages.plugin_script.lib.script import ScriptException


class XplScriptManager(XplPlugin):
	""" 
	"""

	def __init__(self):
		""" Init plugin
		"""
		XplPlugin.__init__(self, name='script')

		# check if the plugin is configured. If not, this will stop the plugin and log an error
		if not self.check_configured():
			return
			
		### get all config keys
		# no configuration needed
				
		# Init script functions
		self.script  = Script(self.log)
		
		# Create listeners
		self.log.info("### Creating listener for Script")    
		Listener(self.script_cmnd_cb, self.myxpl, {'xpltype': 'xpl-cmnd', 'schema': 'exec.basic'})	# exec.basic { pid='cmd_action|cmd_info' program='/path/program' arg='parameters ...' status='start' }

		
		self.ready()



	def script_cmnd_cb(self, message):
		""" Call script lib for run program
			@param message : xpl message
			
			pid: 		Command type, must be set to "cmd_action|cmd_info"
			program: 	Executable filename, including path and extension
			arg:		Command line arguments or 'none'
			status: 	'start' for running program
			
		"""
		self.log.debug("### Call script_cmnd_cb")

		commandtype = message.data['pid']
		if (commandtype != "cmd_action") and (commandtype != "cmd_info"):
			self.log.warning("### This command type %s' is not for Domogik Script plugin" % message.data['pid'] )
			return
		if message.data['status'] != "start":
			self.log.warning("### This command with status '%s' is not for Domogik Script plugin" % message.data['status'] )
			return
		program = message.data['program'].strip()
		arg = message.data["arg"].strip()
	
		# Execute program
		self.log.info("### Run program '%s' type '%s' with parameters '%s'" % (program, commandtype, arg))
		
		# call program
		if arg =="none":
			cmd_list= program.split(" ")
		else:
			cmd_list = (program + " " + arg).split(" ")					# Ex.: cmd_list = ['setchacon', 'sapin', 'on']
		resultcmd = self.script.run_cmd(cmd_list, commandtype)			# resultcmd = "executed|value|failed"
 

		# Send ACK xpl-trig message to xpl-cmnd command.
		self.log.debug("### Send xpl-trig msg for script with return '%s'" % resultcmd)     	# xpl-trig exec.basic { pid='cmd_action|cmd_info' program='/path/program' arg='parameters ...' status='executed|value' }
		mess = XplMessage()
		mess.set_type('xpl-trig')
		mess.set_schema('exec.basic')
		mess.add_data({'pid'     :  commandtype})
		mess.add_data({'program' :  program})
		mess.add_data({'arg'     :  arg})
		mess.add_data({'status'  :  resultcmd})
		self.myxpl.send(mess)


if __name__ == "__main__":
	XplScriptManager()

