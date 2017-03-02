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
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import subprocess
import shlex
import time


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

    # -------------------------------------------------------------------------------------------------
    def __init__(self, log, send, stop):
        """ Init Weather object
            @param log : log instance
            @param send : callback to send values to domogik
            @param stop : Event of the plugin to handle plugin stop
            @param get_parameter : a callback to a plugin core function
        """
        self.log = log
        self.send = send
        self.stopplugin = stop


    # -------------------------------------------------------------------------------------------------
    def runCmd(self, script, type):
        """ Execute shell command.
            script :      script (list)
            type :        script type
        """

        if any(i in script for i in '<|>'):
            errorstr = u"### Script '%s' is refused: specials characters like '>', '<', '|' are not authorized" % script
            self.log.error(errorstr)
            return False, errorstr

        script = script.strip()
        if script[-1] == '&':  script = script[:-1]     # Delete '&' for disable backgrounding command
        cmd = shlex.split(script.strip())    # For spliting with spaces and quote(s) for a command like: setchacon.sh "salon off" => ['setchacon.sh', 'salon off']

        #self.log.debug(u"==> Execute subprocess for '%s'" % cmd)
        try:
            outputcmd = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False).strip()
        except subprocess.CalledProcessError, e:
            errorstr = u"### Script '%s' failed with error : %d, %s" % (script, e.returncode, e.output.decode('ascii', errors='ignore'))
            self.log.error(errorstr)
            return False, errorstr
        except OSError, e:
            errorstr = u"### Script '%s' failed with OSerror : %d, (%s)" % (script, e.errno, e.strerror)
            self.log.error(errorstr)
            if e.errno == 8:
                errorstr = u"### Script '%s': missing 'shebang' at top of the script or bad arch for binary program !" % script
                self.log.error(errorstr)
            return False, errorstr

        if type in ["script.info_number", "script.info_temperature", "script.info_humidity"]:
            if not self.is_number(outputcmd):
                errorstr = u"### Script type Number '%s' not return a number: '%s'" % (script, outputcmd)
                self.log.error(errorstr)
                return False, errorstr
        elif type in ["script.info_binary", "script.info_onoff", "script.info_openclose"]:
            if outputcmd not in ['0', '1']:
                errorstr = u"### Script type Binary '%s' not return a binary: '%s'" % (script, outputcmd)
                self.log.error(errorstr)
                return False, errorstr

        return True, outputcmd    # Return value for "script.info_number | script.info_binary | script.info_string"


    # -------------------------------------------------------------------------------------------------
    def is_number(self, s):
        ''' Return 'True' if s is a number
        '''
        try:
            float(s)
            return True
        except ValueError:
            return False
        except TypeError:
            return False


    # -------------------------------------------------------------------------------------------------
    def reloadScriptDevices(self, devices):
        """ Called by the bin part when starting or devices added/deleted/updated
        """
        self.scriptdevices = devices


    # -------------------------------------------------------------------------------------------------
    def runScheduledScripts(self):
        """ Execute info scripts every interval secondes.
        """
        self.log.info(u"==> Thread for 'Info Script' sensors started")
        scriptinfo_nextread = {}
        while not self.stopplugin.isSet():
            for scriptdeviceid in self.scriptdevices:
                name = self.scriptdevices[scriptdeviceid]["name"]
                scripttype = self.scriptdevices[scriptdeviceid]["scripttype"]
                command = self.scriptdevices[scriptdeviceid]["commands"][1]
                interval = self.scriptdevices[scriptdeviceid]["interval"]

                if "info" not in scripttype: 
                    self.stopplugin.wait(0.5)
                    continue
                if scriptdeviceid not in scriptinfo_nextread:  scriptinfo_nextread.update({scriptdeviceid: 0})
                if time.time() >= scriptinfo_nextread[scriptdeviceid]:
                    scriptinfo_nextread[scriptdeviceid] = time.time() + interval
                    if interval <= 0: continue
                    self.log.info(u"==> EXECUTE scheduled 'Info Script' '%s' for device '%s' (type %s)" % (command, name, scripttype))
                    rc, val = self.runCmd(command, scripttype)
                    if rc:
                        self.log.info("==> UPDATE Sensor for device '%s' with value '%s' " % (name, val))
                        self.send(scriptdeviceid, val)
                    self.log.info(u"==> WAIT {0} seconds before the next execution of 'Info Script' sensor for device '{1}' ".format(interval, name))
                self.stopplugin.wait(0.5)
        self.log.info(u"==> Thread for 'Info Script' sensors stopped")
   

    # -------------------------------------------------------------------------------------------------
    def runRequestedScript(self, devid, devname, scripttype, script, state, send, stop):
        """ Execute script/program every interval secondes.
            @param
            devid :        Device id
            devname :      Device name
            scripttype :   Scritp type
            script :       script
            state :        Return state for command sensor
        """
        self.log.debug(u"==> EXECUTE requested command '%s' for device '%s' (type %s)" % (script, devname, scripttype))
        rc, val = self.runCmd(script, scripttype)
        if rc:
            send(devid, state)
            
            
            
            
