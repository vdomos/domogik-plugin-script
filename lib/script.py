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
import requests
import time
import json


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
        
        self.numberSensors = ["script.info_value", "script.info_level", "script.info_temperature", "script.info_humidity", "script.info_jsonvalue"]                              
        self.boolSensors = ["script.info_state", "script.info_switch", "script.info_opening", "script.info_jsonstate"]
        
        self.boolStrValue = {"false": "0", "true": "1", "off": "0", "on": "1", "disable": "0", 
                             "enable": "1", "low": "0", "high": "1", "decrease": "0", "increase": "1", 
                             "up": "0", "down": "1", "open": "0", "close": "1", "closed": "1", "stop": "0",
                             "start": "1", "inactive": "0", "active": "1", "nomotion": "0", "motion": "1",
                             "0": "0", "1": "1"}


    # -------------------------------------------------------------------------------------------------
    def runCmd(self, name, script):
        """ Execute shell command.
            name :      device name
            script :    script (list)
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
            errorstr = u"### Script '%s' for device '%s' failed with error : %d, %s" % (script, name, e.returncode, e.output.decode('ascii', errors='ignore'))
            self.log.error(errorstr)
            return False, errorstr
        except OSError, e:
            errorstr = u"### Script '%s for device '%s'' failed with OSerror : %d, (%s)" % (script, name, e.errno, e.strerror)
            self.log.error(errorstr)
            if e.errno == 8:
                errorstr = u"### Script '%s' for device '%s': missing 'shebang' at top of the script or bad arch for binary program !" % (script, name)
                self.log.error(errorstr)
            return False, errorstr

        return True, outputcmd    # Return value for "script.info_* if no error"


    # -----------------------------------------------------------------------------
    def runHttpCmd(self, name, url):
        """ Call requect url
            name :      device name
            url : url (the answer must return only one value !)
        """
        try:
            req = requests.get(url)
        except requests.exceptions.RequestException as err:
            errorstr = u"### Http Script '%s' for device '%s' failed with Request Exception : %s" % (url, name, err)
            self.log.error(errorstr)
            return False, errorstr
        if req.status_code > 304:
            errorstr = u"### Http Script '%s' for device '%s' failed with HTTP Code : %s" % (url, name, req.status_code)
            self.log.error(errorstr)
            return False, errorstr

        return True, req.text    # Return value for "script.info_* if no error"


    # -----------------------------------------------------------------------------
    def checkValueType(self, name, script, type, strvalue):
        """ Check if a number sensor script return a number value and  boolean script return a boolean value
            name :      device name
            script:     script
            strvalue:   value in string format
            type:       sensor type
        """
        if type in self.numberSensors:
            if not self.is_number(strvalue):
                errorstr = u"### Script '%s' type %s for device '%s' not return a number: '%s'" % (script, name, strvalue)
                self.log.error(errorstr)
                return False
        elif type in self.boolSensors:
            if strvalue.lower() not in self.boolStrValue:
                errorstr = u"### Script '%s' type %s for device '%s' not return a boolean: '%s'" % (script, name, strvalue)
                self.log.error(errorstr)
                return False
            strvalue = self.boolStrValue[strvalue.lower()]
        return True


    # -----------------------------------------------------------------------------
    def parseJsonQuery(self, name, script, strjson, jsonquery):
        """ Parse value with jsonquery
            name :      device name
            script:     script
            strjson:    json string
            jsonquery:  json query
            http://www.meteofrance.com/mf3-rpc-portlet/rest/pluie/543950
            "dataCadran|0|niveauPluieText"
            "dataCadran|0|niveauPluie"
            "isAvailable"
        """
        try:
             jsonvalue = json.loads(strjson)
        except ValueError, err:
            errorstr = u"### Json Script '%s' for device '%s' failed with query '%s': No JSON data (%s)" % (script, name, jsonquery, err)
            self.log.error(errorstr)
            return False, errorstr
            
        jsonquerylist= jsonquery.split('|')
        
        for elem in jsonquerylist:
            self.log.debug(u"==> Search '%s' key or index in json value" % elem)
            try:
                if self.is_number(elem):
                    jsonvalue = jsonvalue[int(elem)]
                else:
                    jsonvalue = jsonvalue[elem]
            except KeyError:
                errorstr = u"### Json Script '%s' for device '%s' failed with query '%s', KeyError with key '%s'" % (script, name, jsonquery, elem)
                self.log.error(errorstr)
                return False, errorstr
            except IndexError:
                errorstr = u"### Json Script '%s' for device '%s' failed with query '%s', IndexError with index '%s'" % (script, name, jsonquery, elem)
                self.log.error(errorstr)
                return False, errorstr

        return True, str(jsonvalue)
    
    
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
                scripttype = self.scriptdevices[scriptdeviceid]["scripttype"]
                if "info" in scripttype: 
                    name = self.scriptdevices[scriptdeviceid]["name"]
                    script = self.scriptdevices[scriptdeviceid]["commands"][1]
                    interval = self.scriptdevices[scriptdeviceid]["interval"]

                    if scriptdeviceid not in scriptinfo_nextread:  scriptinfo_nextread.update({scriptdeviceid: 0})
                    if time.time() >= scriptinfo_nextread[scriptdeviceid]:
                        if interval > 0:
                            scriptinfo_nextread[scriptdeviceid] = time.time() + interval
                            self.log.info(u"==> EXECUTE scheduled 'Info Script' '%s' for device '%s' (type %s)" % (script, name, scripttype))
                            
                            if "http://" in script:
                                execstatus, val = self.runHttpCmd(name, script)
                            else:
                                execstatus, val = self.runCmd(name, script)

                            if execstatus:
                                if "json" in scripttype:
                                    status, val = self.parseJsonQuery(name, script, val, self.scriptdevices[scriptdeviceid]["jsonquery"])
                                    if status:
                                        status = self.checkValueType(name, script, scripttype, val)
                                else:
                                    status = self.checkValueType(name, script, scripttype, val)

                                if status:
                                    self.log.info(u"==> UPDATE Sensor for device '%s' with value '%s' " % (name, val.decode('utf-8')))
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
            state :        Return state for script
        """
        self.log.debug(u"==> EXECUTE requested script '%s' for device '%s' (type %s)" % (script, devname, scripttype))
        if "http://" in script:
            execstatus, val = self.runHttpCmd(devname, script)
        else:
            execstatus, val = self.runCmd(devname, script)

        if execstatus:
            send(devid, state)

