# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Allow a PV to be an indirect name: a text string that
# is the name of the real connection.

import pyedm.edmPVfactory as edmPVfactory

# Track the changing PV names
#
def valueCallback(ipv, **kw):
    ipv.redirectPV = edmPVfactory.buildPV(ipv.value)

#
# When the value of the indirect PV changes, pass this on!
def redirectCallback(starpv, **kw):
    if "userArgs" in kw:
        ipv = kw["userArgs"]
    else:
        return 0


class indirectPV:
    def __init__(self, name=None):
        self.callbackList = []
        self.value = None
        self.str_value = None

    def __del__(self):
        pass

    def setPVname(self, pvName):
        pass

    def getName(self):
        pass

    def getStatus(self):
        pass

    def get(self):
        pass

    def put(self, value):
        pass

    def add_callback(self, fn_name, widget=None):
        pass

    def add_redisplay(self, widget):
        pass

def buildPV(name,parent=None,tag=None,macroTable=None):
    return indirectPV(name)

edmPVfactory.pvClassDict["INDIRECT"] = buildPV


