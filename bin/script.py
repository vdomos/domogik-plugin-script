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

Run Linux script/program for a command or a sensor.

Implements
==========


@author: domos  (domos dt vesta at gmail dt com)
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage

from domogik_packages.plugin_script.lib.script import Script
from domogik_packages.plugin_script.lib.script import ScriptException

import threading
import time


class ScriptManager(Plugin):
    """
    """

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='script')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # ### get the devices list in plugin
        # for this plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device=True)
        # print(self.devices)

        # get the sensors id per device:
        self.sensors = self.get_sensors(self.devices)
        #self.log.info(u"==> sensors:   %s" % format(self.sensors))	
        # INFO ==> sensors:   {137: {u'sensor_script_info_string': 241}}

        # Init script functions
        self.script = Script(self.log)

        self.device_list = {}
        # ### For each device
        for a_device in self.devices:
            # self.log.info(u"a_device:   %s" % format(a_device))

            device_id = a_device["id"]
            device_name = a_device["name"]                              # Ex.: "Conso Elec Jour" 
            device_type = a_device["device_type_id"]                  # Ex.: "script.info_number | script.info_binary | script.info_string | script.action|..."            
            device_command1 = self.get_parameter(a_device, "command")         
            self.device_list.update({device_id : { 'commands': ["", device_command1], 'name': device_name, 'scripttype': device_type }})

            if device_type != "script.action" and device_type != "script.onoff":          # Shedule only script_info_* scripts    
                command_interval = self.get_parameter(a_device, "interval")                 # Ex.: "60" in secondes
                self.log.info(u"==> Device sensor '{0}' ({1}) for running '{2}' with interval {3}s".format(device_name, device_type, device_command1, command_interval))
                if command_interval > 0:
                    thr_name = "dev_{0}-{1}".format(a_device['id'], "script_info")
                    self.log.info(u"==> Launch command thread '%s' for '%s' device !" % (thr_name, device_name))
                    threads = {}
                    threads[thr_name] = threading.Thread(None,
                                                        self.script.runScheduledCmd,
                                                        thr_name,
                                                        (self.log,
                                                            device_id,
                                                            device_name,
                                                            device_type,
                                                            device_command1,
                                                            command_interval,
                                                            self.send_data,
                                                            self.get_stop()
                                                        ),
                                                    {})
                    threads[thr_name].start()
                    self.register_thread(threads[thr_name])
                    self.log.info(u"==> Wait some time before running the next scheduled script ...")
                    time.sleep(5)        # Wait some time to not start the script with the same interval et the same time.
                else:
                    self.log.info(u"==> Script thread '%s' for '%s' device is DISABLED (interval < 0) !" % (thr_name, device_name))

            else:
                if device_type == "script.onoff": 
                    self.device_list[device_id]['commands'][0] = self.get_parameter(a_device, "command0")
                    # {'100': {'commands': ['set lum off', 'set lum on'], 'name': 'Lum sejour'}}
                    self.log.info(u"==> Device command '{0}' ({1}) for running '{2}' if ON, for running '{3}' if OFF.".format(device_name, device_type, self.device_list[device_id]['commands'][1], self.device_list[device_id]['commands'][0]))
                else:
                    self.log.info(u"==> Device command '{0}' ({1}) for running '{2}' if TRIG".format(device_name, device_type, self.device_list[device_id]['commands'][1]))

        self.ready()


    def on_mdp_request(self, msg):
        """ Called when a MQ req/rep message is received
        """
        Plugin.on_mdp_request(self, msg)
        # self.log.info(u"==> Received 0MQ messages: %s" % format(msg))
        if msg.get_action() == "client.cmd":
            data = msg.get_data()
            self.log.info(u"==> Received 0MQ messages data: %s" % format(data))
            # INFO ==> Received 0MQ messages data: {u'state': u'1', u'command_id': 50, u'device_id': 139}
            
            if data["device_id"] not in self.device_list:
                self.log.error("### Device ID '%s' unknown, Have you restarted the plugin after device creation ?" % data["device_id"])
                status = False
                reason = "Plugin script: Unknown device ID %d" % data["device_id"]
            else:    
                # Execute command
                device_command = self.device_list[data["device_id"]]["commands"][int(data["state"])]
                device_name = self.device_list[data["device_id"]]["name"]
                device_type = self.device_list[data["device_id"]]["scripttype"]
                self.log.info(u"==> Execute requested command '%s' (%s) for device '%s'" % (device_command, device_type, device_name))
                # call command
                status, reason = self.script.runCmd(device_command, device_type)       # True, None  | False, "Error str"

                # Update sensor's command state
                if status:
                    self.send_data(data["device_id"], data["state"])
                    
            # Send MQ ACK to command
            self.log.info("Reply ACQ to command 0MQ")
            reply_msg = MQMessage()
            reply_msg.set_action('client.cmd.result')
            reply_msg.add_data('status', status)
            reply_msg.add_data('reason', reason)
            self.reply(reply_msg.get())


    def send_data(self, device_id, value):
        """ Send the value sensors values over MQ
        """
        data = {}
        if device_id not in self.device_list:
            self.log.error("### Device ID '%s' unknown, Have you restarted the plugin after device creation ?" % (device_id))
            return (False, "Plugin script: Unknown sensor device ID %d" % device_id)
            
        for sensor in self.sensors[device_id]:          # {66: {u'Script OnOff': 159}}
            self.log.info("==> Update Sensor '%s' / id '%s' with value '%s' for device '%s'" % (sensor, self.sensors[device_id][sensor], value, self.device_list[device_id]["name"]))
            # INFO ==> Update Sensor 'Script OnOff' / id '159' with value '1' for device 'Lum Sejour'
            data[self.sensors[device_id][sensor]] = value
        self.log.info("==> 0MQ PUB for device '%s' sended = %s" % (self.device_list[device_id]["name"], format(data)))			# {u'id_sensor': u'value'} => {159: u'1'}

        try:
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct ...
            self.log.debug(u"Bad MQ message to send. This may happen due to some invalid sensor data. MQ data is : {0}".format(data))
            return (False, "Plugin script: Bad MQ message to update sensor")

        return (True, None)


if __name__ == "__main__":
    ScriptManager()
