# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Support for LOC pv types
from pyedm.edmPVfactory import edmPVbase, pvClassDict
from pyedm.edmApp import edmApp
# from __future__ import print_function

chanDict = {}

def enumConverter(value, enums):
    # return str(value), str(value)
    if isinstance(value, int) or isinstance(value, float):
        val = int(value)
        if val >= 0 or val <= len(enums):
            return (val, enums[val])
        return (val, str(val))
    if isinstance(value, str):
        return( enums.index(value), value)
    return (0, "")

def intConverter(value, enums):
    # return int(value), str(value)
    if isinstance(value, str):
        val = int(float(value))
    else:
        val = int(value)
    return val, str(value)
class channel:
    # these types match the general types from edmPVbase
    types = { "i":edmPVbase.typeInt,
              "d":edmPVbase.typeFloat,
              "s":edmPVbase.typeString,
              "e":edmPVbase.typeEnum,
              "U":edmPVbase.typeUnknown}

    converter = { edmPVbase.typeInt : intConverter,
                  edmPVbase.typeFloat : lambda v,e:(float(v), str(v)),
                  edmPVbase.typeString: lambda v,e:(str(v), str(v)),
                  edmPVbase.typeEnum: enumConverter,
                  edmPVbase.typeUnknown: lambda v,e:(str(v), str(v))
                  }


    def __init__(self, name, pv=None, flags=None):
        self.connectList = []
        self.enums = []
        self.name = name
        if flags == None:
            self.initType("U", "")
        else:
            words = flags.split(":",1)
            if len(words) > 1:
                self.initType(words[0], words[1])
            else:
                self.initType(words[0], "")
        self.addPV(pv)

    def initType(self, pvType, value):
        self.pvType = self.types[pvType]
        if self.pvType == edmPVbase.typeEnum:
            value, self.enums = value.split(",",1)
            value = int(value)
        try:
            self.value, self.char_value = self.converter[self.pvType](value, self.enums)
        except:
            print "Local PV initialization failed:", self.name, value
            self.value = 0
            self.char_value = ""

    def addPV(self, pv, chantype=None):
        if pv == None : return
        self.connectList.append(pv)
        if pv.connectCallback:
            pv.connectCallback(pv, pv.connectCallbackArg)
        if chantype != None:
            words = chantype.split(":", 1)
            if self.types[words[0]] != self.pvType:
                if self.pvType == edmPVbase.typeUnknown:
                    self.pvType = self.types[words[0]]
                else:
                    print "Type conflict for PV", self.name, self.types[words[0]], self.pvType

    def setValue(self, value):
        if edmApp.DebugFlag > 0: print 'setValue(', self, value, ')'
        try:
            self.value, self.char_value = self.converter[self.pvType](value, self.enums)
        except:
            print "ERROR: setValue() failure for", self.name, value, type(value)
            return

        for ePV in self.connectList:
            ePV.value = self.value
            ePV.char_value = self.char_value
            if ePV.DebugFlag > 0: print "callback LOCAL", self.name, "value=", value
            for fn in ePV.callbackList:
                    fn[0](fn[1], pvname=self.name, chid=0,pv=ePV,value=self.value,count=1,units=ePV.units,severity=0,userArgs=fn[2])


# create a new channel, and connect this PV to it.
def findChannel(name, init=0, pv=None):
    words = name.split("=", 1)
    if words[0] in chanDict:
        ch = chanDict[words[0]]
        if len(words) > 1:
            ch.addPV(pv, words[1])
        else:
            ch.addPV(pv)
        return ch

    if init == 0 or pv == None:
        return None

    if len(words) > 1:
        newchan = channel(words[0], flags=words[1],pv=pv)
    else:
        newchan = channel(words[0], pv=pv)

    chanDict[words[0]] = newchan
    return newchan


class edmPVlocal(edmPVbase):
    def __init__(self, **kw):
        edmPVbase.__init__(self, **kw)
        self.chan = findChannel(kw.get("name"), init=1, pv=self)
        self.value = self.chan.value
        self.char_value = self.chan.char_value
        self.precision = 3
        self.pvType = self.chan.pvType
        self.prefix = "LOC\\"
        self.isValid = True

    def get(self):
        return self.chan.value

    def put(self, value):
        self.chan.setValue(value)

def buildPV(name,**kw):
    return edmPVlocal(name=name,**kw)

# Track names used to ensure we only have 1 instance and many references of a
# local variable
localPVlist = {}

pvClassDict["LOC"] = buildPV
