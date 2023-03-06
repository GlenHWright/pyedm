# Copyright 2011-2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# NOT IMPLEMENTED!
# Allow a PV to be an indirect name: a text string that
# is the name of the real connection.

# MODULE LEVEL: low

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


class indirectPV(edmPVfactory.edmPVbase):
    def __init__(self, name=None, **kw):
        super().init(name, **kw)
        self.callbackList = []
        self.value = None
        self.str_value = None
        self.prefix = "INDIRECT\\"

    def edmCleanup(self):
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

def buildPV(**kw):
    return indirectPV(**kw)

edmPVfactory.pvClassDict["INDIRECT"] = buildPV

