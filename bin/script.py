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


@author: domos  (domos dt vesta at gmail dt com)
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin

from domogik_packages.plugin_script.lib.script import Script
from domogik_packages.plugin_script.lib.script import ScriptException

import threading


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
			
		### get the devices list
		# for this plugin, if no devices are created we won't be able to use devices.
		self.devices = self.get_device_list(quit_if_no_device = True)
		#print(self.devices)		# List devices créés dans plugin ?

				
		# Init script functions
		self.script  = Script(self.log)
		
		### For each device
		for a_device in self.devices:
			#self.log.info(u"a_device:   %s" % format(a_device))
			
			device_name = a_device["name"]										# Ex.: "Conso Elec Jour"
			device_typeid = a_device["device_type_id"]							# Ex.: "script.info_number | script.info_binary | script.info_string | script.action"
			device_statname = device_typeid.replace('.', '_')					# Ex.: "script_info_number | script_info_binary | script_info_string | script_action"
			command_script = self.get_parameter_for_feature(a_device, "xpl_stats", "stat_" + device_statname, "program")	# Ex.: "/home/user/getElec.sh -jour"
			if device_typeid != "script.action":								# Shedule only script_info_* scripts
				command_interval = self.get_parameter(a_device, "interval")		# Ex.: "60" in secondes
				self.log.info(u"==> Device '{0}' ({1}) to call = '{2}' with interval = {3}s".format(device_name, device_typeid, command_script, command_interval))
				if command_interval <= 0:
					command_interval = 0
				thr_name = "dev_{0}-{1}".format(a_device['id'], "script_info")
				self.log.info(u"==> Launch thread '%s' for '%s' device !" % (thr_name, device_name))
				threads = {}
				threads[thr_name] = threading.Thread(None, 
										self.script.runScheduledCmd,
										thr_name,
										(self.log,
											device_name,
											device_statname,
											command_script, 
											command_interval,
											self.send_xpl,
											self.get_stop()
										),
									{})
				threads[thr_name].start()
				self.register_thread(threads[thr_name])
			else:
				self.log.info(u"==> Device '{0}' ({1}) to call = '{2}'".format(device_name, device_typeid, command_script))
		
		
		# Create listeners
		self.log.info(u"==> Creating listener for Script")    
		Listener(self.scriptCmnd_cb, self.myxpl, {'xpltype': 'xpl-cmnd', 'schema': 'exec.basic'})
				
		self.ready()



	def scriptCmnd_cb(self, message):
		""" Call script lib for run program
			@param 
			message :	xpl message
			type : 		Command type, must be set to "script.info_number | script.info_binary | script.action"
			program : 	Executable filename, including path and extension
			status : 	'start' for running program
		"""
		self.log.debug(u"==> Call scriptCmnd_cb")

		scripttype = message.data['type']
		if (scripttype != "script_info_number") and (scripttype != "script_info_binary") and (scripttype != "script_action"):
			self.log.error(u"### This command type %s' is not for Domogik Script plugin" % message.data['type'] )
			return
		if message.data['status'] != "start":
			self.log.error(u"### This command with status '%s' is not for Domogik Script plugin" % message.data['status'] )
			return
		program = message.data['program'].strip()
	
		# Execute program
		self.log.info(u"==> Execute requested script '%s' type '%s'" % (program, scripttype))
		
		# call program
		resultcmd = self.script.runCmd(program, scripttype)		# resultcmd = "executed|value|failed"
 
		# Send ACK xpl-trig message to xpl-cmnd command.
		self.log.debug(u"==> Send xpl-trig msg for script with return '%s'" % resultcmd)
		self.send_xpl("xpl-trig", {"program" : program, "type" : scripttype, "status" : resultcmd})


	def send_xpl(self, type, data):
		""" Send data on xPL network
			@param data : data to send (dict)
		"""
		msg = XplMessage()
		msg.set_type(type)
		msg.set_schema("exec.basic")
		for element in data:
			msg.add_data({element : data[element]})
		self.log.debug(u"==> Send xpl message...")
		self.log.debug(msg)
		self.myxpl.send(msg)


if __name__ == "__main__":
	XplScriptManager()

