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

    # -------------------------------------------------------------------------------------------------
    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='script')

        # Check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # Get the devices list in plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device=True)
        #self.log.info(u"+++ devices list: %s" % format(self.devices))
        
        # Get the sensors id per device:
        self.sensors = self.get_sensors(self.devices)
        #self.log.info(u"+++ sensors: %s" % format(self.sensors))

        # Init script functions
        self.script = Script(self.log, self.send_pub_data, self.get_stop())
        
        # Set scripts list with parameters
        self.setScriptDevicesList(self.devices)

        self.log.info(u"==> Launch 'Info Script' sensors thread") 
        thr_name = "thr_infoscriptsensors"
        self.thread_sensors = threading.Thread(None,
                                          self.script.runScheduledScripts,
                                          thr_name,
                                          (),
                                          {})
        self.thread_sensors.start()
        self.register_thread(self.thread_sensors)

        self.log.info(u"==> Add callback for new or changed devices.")
        self.register_cb_update_devices(self.reload_devices)
        
        self.ready()

    # -------------------------------------------------------------------------------------------------
    def setScriptDevicesList(self, devices):
        self.log.info(u"==> Set Script devices list ...")
        self.scriptdevices_list = {}        
        for a_device in devices:    # For each device
            # self.log.info(u"a_device:   %s" % format(a_device))
            device_interval = 0
            device_command0 = ""
            device_command1 = self.get_parameter(a_device, "command") 
            if a_device["device_type_id"] == "script.switch":
                device_command0 = self.get_parameter(a_device, "command0") 
            if "info" in a_device["device_type_id"]:  
                device_interval = self.get_parameter(a_device, "interval") 
            self.scriptdevices_list.update(
                {a_device["id"] : 
                        { 'name': a_device["name"], 
                          'scripttype': a_device["device_type_id"], 
                          'commands': [device_command0, device_command1] ,
                          'interval': device_interval
                        }
                })
            self.log.info(u"==> Device script '{0}'" . format(self.scriptdevices_list[a_device["id"]]))
        self.script.reloadScriptDevices(self.scriptdevices_list)
                        
 
    # -------------------------------------------------------------------------------------------------
    def on_mdp_request(self, msg):
        """ Called when a MQ req/rep message is received
        """
        Plugin.on_mdp_request(self, msg)
        #self.log.info(u"==> Received MQ message: %s" % format(msg))
        # => MQ Request received : <MQMessage(action=client.cmd, data='{u'state': u'1', u'command_id': 14, u'device_id': 39}')>
    
        if msg.get_action() == "client.cmd":
            data = msg.get_data()
            #self.log.debug(u"==> Received MQ REQ command message: %s" % format(data))      
            # INFO ==> Received MQ REQ command message: {u'state': u'1', u'command_id': 50, u'device_id': 139}
            # INFO ==> Received MQ REQ command message: {u'parameter1': u'World', u'device_id': 171, u'command_id': 71, u'parameter2': u'Hello'}
            device_id = data["device_id"]
            command_id = data["command_id"]
            if device_id not in self.scriptdevices_list:
                self.log.error(u"### Device ID '%s' unknown" % device_id)
                status = False
                reason = u"Plugin script: Unknown device ID %d" % device_id
                self.send_rep_ack(status, reason, command_id, "unknown") ;                      # Reply MQ REP (acq) to REQ command
                return
            else:    
                device_name = self.scriptdevices_list[device_id]["name"]
                device_type = self.scriptdevices_list[device_id]["scripttype"]
                
                # Three command Script: "script.action", "script.switch" and "script.string"
                if device_type == "script.action" or device_type == "script.switch":
                    device_state = data["state"]
                    device_command = self.scriptdevices_list[device_id]["commands"][int(device_state)]
                    
                elif device_type == "script.string":
                    # Script string:  data = {u'parameter1': u'World', u'command_id': 71, u'device_id': 171}  or  {u'parameter1': u'World', u'device_id': 171, u'command_id': 71, u'parameter2': u'Hello'}
                    device_state = "1"      # Return a DT_Trigger sensor
                    device_command = self.scriptdevices_list[device_id]["commands"][int(device_state)]
                    
                    if "parameter1" not in data:
                        self.log.error(u"### Missing 'parameter1' in command '%s' for device '%s' (type %s)" % (device_command, device_name, device_type))
                        status = False
                        reason = u"Plugin script: Missing 'parameter1' in command '%s' for device '%s' (type %s)" % (device_command, device_name, device_type)
                        self.send_rep_ack(status, reason, command_id, device_name) ;            # Reply MQ REP (acq) to REQ command
                        return
                    if "parameter2" not in data:
                        device_command = device_command + " '" + data["parameter1"] + "'"
                    else:
                        device_command = device_command + " '" + data["parameter1"] + "' '" + data["parameter2"] + "'"

                # Execute command
                # Call command in a thread ("on_mdp_request" function is not call in a thread for now and if script is too long, this can do a time-out)
                thr_name = "dev_{0}-{1}".format(device_id, device_type)
                self.log.debug(u"==> Launch command thread '%s' for '%s' device !" % (thr_name, device_name))
                threads = {}
                threads[thr_name] = threading.Thread(None,
                                                    self.script.runRequestedScript,
                                                    thr_name,
                                                    (device_id,
                                                        device_name,
                                                        device_type,
                                                        device_command,
                                                        device_state,
                                                        self.send_pub_data,
                                                        self.get_stop()
                                                    ),
                                                    {})
                threads[thr_name].start()
                self.register_thread(threads[thr_name])
                
            # Reply MQ REP (acq) to REQ command
            self.send_rep_ack(True, None, command_id, device_name) ;                 # With thread, no possible to return a error script to MQ !


    # -------------------------------------------------------------------------------------------------
    def send_rep_ack(self, status, reason, cmd_id, dev_name):
        """ Send MQ REP (acq) to command
        """
        self.log.info(u"==> Reply MQ REP (acq) to REQ command id '%s' for device '%s'" % (cmd_id, dev_name))
        reply_msg = MQMessage()
        reply_msg.set_action('client.cmd.result')
        reply_msg.add_data('status', status)
        reply_msg.add_data('reason', reason)
        self.reply(reply_msg.get())


    # -------------------------------------------------------------------------------------------------
    def send_pub_data(self, device_id, value):
        """ Send the value sensors values over MQ
        """
        data = {}
        '''    
        for sensor in self.sensors[device_id]:          # {66: {u'Script OnOff': 159}}
            self.log.info("==> Update Sensor '%s' (id:'%s') with value '%s' for device '%s'" % (sensor, self.sensors[device_id][sensor], value, "nom du device"))
            data[self.sensors[device_id][sensor]] = value
        '''    
        sensor_device = self.sensors[device_id].keys()[0]       # Example: 'temperature'
        data[self.sensors[device_id][sensor_device]] = value    # data['id_sensor'] = value
        try:
            self.log.info("==> SEND MQ PUB message '%s'" % format(data))    #  => {u'id_sensor': u'value'} => {159: u'1'}
            self._pub.send_event('client.sensor', data)
        except:
            # We ignore the message if some values are not correct ...
            self.log.error(u"Bad MQ PUB message to send : {0}".format(data))


    # -------------------------------------------------------------------------------------------------
    def reload_devices(self, devices):
        """ Called when some devices are added/deleted/updated
        """
        self.log.info(u"==> Reload Device called")
        self.setScriptDevicesList(devices)
        self.devices = devices
        self.sensors = self.get_sensors(devices)
        '''
        with 2 'Global parameters', there 2 calls:
        2017-01-28 13:20:19,754 domogik-script INFO Retrieve the devices list for this client...
        2017-01-28 13:20:19,791 domogik-script INFO Retrieve the devices list for this client...
        '''


# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    ScriptManager()


