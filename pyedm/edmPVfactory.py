# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# PV factory support
#
# MODULE LEVEL: Low
#
import traceback
from .edmApp import edmApp, debugClass

class edmPVbase(debugClass):
    typeNames = [ "unknown", "int", "float", "string", "enum" ]
    typeUnknown, typeInt, typeFloat, typeString, typeEnum = list(range(0,5))
    def __init__(self, name=None, connectCallback=None, connectCallbackArg=None, *args, **kw):
        self.callbackList = []
        self.value = None
        self.char_value = None
        self.count = 1
        self.severity = 3
        self.isValid = False
        self.chid = 0
        self.enums = ()
        self.connectCallback = connectCallback
        self.connectCallbackArg = connectCallbackArg
        self.pvType = self.typeUnknown
        self.prefix = "base\\"
        self.units = ""

        if name != None:
            self.setPVname(name)
        else:
            self.name = None

    def edmCleanup(self):
        if self.debug() : print("edmPVbase: cleanup", self.name)
        self.connectCallback = None
        self.connectCallbackArg = None
        self.callbackList.clear()

    def setPVname(self, name):
        self.name = name

    def getPVname(self):
        return self.prefix + self.name

    def getStatus(self):
        pass

    def getLimits(self):
        return (0.0,0.0)

    def get(self):
        pass

    def getEnumStrings(self):
        return self.enums

    def connect(self):
        pass

    def disconnect(self):
        pass

    def newSeverity(self):
        pass

    def put(self, value):
        pass

    def getType(self):
        return self.pvType

    def getTypeName(self):
        return self.typeNames[self.pvType]

    def convText(self, fmt="%.*f", precision=None, enums=None):
        if precision == None:
            try:
                precision = self.precision
            except: precision = 0

        if enums == None:
            try: enums = self.getEnumStrings()
            except: pass

        return convText( self.value, self.pvType, Fmt=fmt, Precision=precision, Enums=enums)

    def add_callback(self, fn_name, widget=None, userArgs=None):
        if self.debug() : print("Add callback", self.name, widget)
        self.callbackList.append((fn_name,widget,userArgs))
        if self.isValid:
            fn_name(widget, pvname=self.name, chid=self.chid, pv=self,
                    value=self.value, count=self.count,
                    severity=self.severity, userArgs=userArgs)

    def del_callback(self, widget=None, *, callback=None):
        ''' delete all callbacks for this PV associated with 'widget'.
            if callback set, look for explicit instances of 'callback'
        '''
        if self.debug(2) : print("del_callback: before:", widget, callback, self.callbackList)
        if callback != None:
            self.callbackList = [ idx for idx in self.callbackList if idx[0] != callback ]
        if widget != None:
            self.callbackList = [ idx for idx in self.callbackList if idx[1] != widget ]
        if self.debug(2) : print("del_callback: after:", self.callbackList)

    def add_redisplay(self, widget, userArgs=None):
        self.callbackList.append((edmApp.redisplay, widget, userArgs))
        if self.isValid:
            edmApp.redisplay(widget)

def convText(Value, PvType, Fmt='%.*f', Precision=None, Enums=None):
        '''convert the value to a String. Use str(value) if not a float.
        If the precision is supplied, use that, otherwise use a default precision'''
        if PvType == edmPVbase.typeFloat:
            if Precision != None:
                return Fmt%(Precision, float(Value))

        if PvType == edmPVbase.typeEnum and Enums != None:
            idx = int(Value)
            if idx >= 0 and idx < len(Enums):
                return Enums[idx]
        return str(Value)

def expandPVname(name, macroTable=None):
    if macroTable != None:
        name = macroTable.expand(name)
    prefix = name.split('\\', 1)
    if len(prefix) == 1:
        return "EPICS", prefix[0]
    else:
        return prefix
    
def buildPV(pvname, *, macroTable=None, **kw):
    '''takes a PV name with an optional PV factory indicator prefix, and
    builds returns a class instance which should inherit from edmPVbase.
    macroTable is used to expand the name, all arguments are passed to the factory method with
    identical parameter names'''
    if edmApp.debug(): print("buildPV(", pvname, macroTable, kw, ")")
    prefix, name = expandPVname(pvname, macroTable)
    if name == None or name == "":
        raise ValueError(f"illegal PV name {pvname}")
    try:
        return pvClassDict[prefix.upper()](name=name, macroTable=macroTable, **kw)
    except KeyError:
        print("Unknown PV type", prefix.upper() , name)
        traceback.print_exc()
    except:
        print("buildPV failed for", prefix, name)
        traceback.print_exc()

    return pvClassDict["LOC"](name="UNKNOWN TYPE", **kw)

pvClassDict = {}
