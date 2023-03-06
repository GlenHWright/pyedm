# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
#
# Note that this is the only module that intefaces directly with pyedm.
# This module is dynamically loaded by __init__, and can be over-ridden
# 

from epics import ca, __version__ as epicsVersion
ca.PREEMPTIVE_CALLBACK = False
import sys

from PyQt5.QtCore import QTimer, QMutex

from pyedm.edmPVfactory import pvClassDict, edmPVbase, convText
from pyedm.edmApp import edmApp

import traceback

watcher = None
# list of channels that have been created, indexed by CHID.
pvDictionary = {}
# list of channels that have been created, indexed by name.
channelList = {}
unknownCHID = {}

pvTypeFromFtype = [ edmPVbase.typeString, edmPVbase.typeInt, edmPVbase.typeFloat,
                    edmPVbase.typeEnum, edmPVbase.typeInt, edmPVbase.typeInt,
                    edmPVbase.typeFloat ]

# number of "ticks" before notification of a failed connection
connectTicks = 50

# This is necessary because pyCa can't call the callback setup from within a
# callback, so we trigger a different monitor to watch for callback setup
# requests and create them.
#
class watchPV(QTimer):
    def __init__(self):
        super().__init__()
        self.pvList = []
        self.pvGone = []
        self.mutex = QMutex()
        self.timeout.connect(self.run)
        self.start(100)

    def run(self):
        ca.pend_event()
        # set up the callbacks, notify of connection
        self.mutex.lock()
        pvList, self.pvList = self.pvList[:], []
        self.mutex.unlock()
        for who in pvList:
            who.isValid = True
            if epicsVersion >= "3.1":
                who.eventID = ca.create_subscription(who.chid, use_ctrl=True,
                callback=subscriptionCallback)
            else:
                who.eventID = ca.create_subscription(who.chid, use_ctrl=True,
                userfcn=subscriptionCallback)
            for ePV in who.connectorList:
                ePV.isValid = True
                ePV.connect()

        # notify of disconnection
        self.mutex.lock()
        pvGone, self.pvGone = self.pvGone[:], []
        self.mutex.unlock()
        for who in pvGone:
            who.isValid = False
            for ePV in who.connectorList:
                ePV.disconnect()

# one element per PV name. an epicsPV connects a widget to a channel
class channel:
    def __init__(self, pvName=None):
        self.connectorList = []
        self.isValid = False
        self.pvType = edmPVbase.typeUnknown
        self.severity = 99
        if pvName != None:
            self.setPVname(pvName)

    def __repr__(self):
        return f"<edmchannel {self.name} severity {self.severity}>"

    def setPVname(self, name):
        self.name = name
        if edmApp.debug(): print("call create_channel", name)
        # Ugly race condition: ca.create_channel(), in pyepics, may call "poll()"
        # which can cause "createCallback to be called early and unexpectedly.
        # To make the unexpected expected, a dictionary based on pv names that
        if epicsVersion >= "3.1":
            self.chid = ca.create_channel(name, False, callback=createCallback)
        else:
            self.chid = ca.create_channel(name, False, createCallback)
        if self.chid == None:
            print(f"ca.create_channel failure for {name}!")
            sys.exit(1)
        chidStr = self.chidStr()
        if edmApp.debug(): print("setPVname CHID=", chidStr)
        if chidStr in pvDictionary:
            print("Duplicate CHID!", chidStr)
        else:
            if edmApp.debug():print("Adding CHID", chidStr, "for", self)
        pvDictionary[chidStr] = self
        if chidStr in unknownCHID:
            handleConnectionState(self.chid, chidStr, unknownCHID[chidStr][2])
        if edmApp.debug():print("done setPVname")

    def chidStr(self, chid=None):
        if chid == None:
            return makeChidStr(self.chid)
        return makeChidStr(chid)

    def setField(self, kw, field, emptytest):
        '''
            setField - update a field from keywords if incoming isn't "empty"
            return either new non-empty value or old value, and
            emptytest if nothing else defined.
        '''
        try:
            if kw[field] != emptytest:
                setattr(self,field,kw[field])
                if edmApp.debug(): print("set ", field, " to ", kw[field])
        except KeyError:
            pass

        return getattr(self, field, emptytest)

    def getEnumStrings(self):
        if self.isValid == False:
            return None
        try:
            if len(self.enums) > 0: return self.enums
        except AttributeError:  # self.enums not set yet
            pass
        except TypeError:       # self.enums type None - can't do len(None)
            pass

        try:
            self.enums = self.enum_strs[:]
        except AttributeError:  #self.chan.enum_strs not set yet
            self.enums = ca.get_enum_strings(self.chid)    # no "try" on this - even though the code is correct, the .edl file isn't.
            if self.enums == None:
                return []

        if edmApp.debug():
            print("convert enums?", self.enums, self.enum_strs)
        if len(self.enums) > 0 and type(self.enums[0]) == bytes:
            self.enums = [ str(en, "utf-8") for en in self.enums ]
        return self.enums

    def setPvType(self, epicsType):
        global pvTypeFromFtype
        self.pvType = pvTypeFromFtype[epicsType % len(pvTypeFromFtype)]

def makeChidStr(chid):
    '''return the chid as a string that can be used as a dictionary index'''
    if type(chid) == int:
        return str(chid)
    return str(chid.value)

def addChannel(pvName, connector):
    '''add a channel to a connector'''
    global channelList
    if pvName in channelList:
        ch = channelList[pvName]
    else:
        ch = channel(pvName)
        channelList[pvName] = ch
    ch.connectorList.append(connector)
    return ch

def delChannel(ch, connector):
    try:
        ch.connectorList.remove(connector)
    except KeyError:
        print(f"PV {connector} not in channel list {ch}")

# Called when the channel connection status changes.
def createCallback(pvname=None,chid=None,conn=None):
    if edmApp.debug(): print('createCallback', pvname, chid)
    chidStr = makeChidStr(chid)

    if chidStr not in pvDictionary:
        unknownCHID[chidStr] = (pvname, chid, conn)
        return
    handleConnectionState(chid, chidStr, conn)

def handleConnectionState(chid, chidStr, conn):
    if conn == True:
        me = pvDictionary[chidStr]
        me.setPvType(ca.field_type(chid))
        watcher.mutex.lock()
        watcher.pvList.append(me)
        watcher.mutex.unlock()
    elif conn == False:
        me = pvDictionary[chidStr]
        watcher.mutex.lock()
        watcher.pvGone.append(me)
        watcher.mutex.unlock()
    else:
        print("Unknown connection state:", conn, chidStr)
    if edmApp.debug(): print('Done createCallback', chidStr)

# Called when a value changes for a PV
def subscriptionCallback(value, **kw):
    chid = str(kw['chid'])
    if edmApp.debug(): print("subscription CHID", chid, kw)
    if chid not in pvDictionary: return

    epicsChan = pvDictionary[chid]
    epicsChan.value = value
    epicsChan.severity = kw['severity']
    precision = epicsChan.setField(kw, 'precision', 0)
    epicsChan.setField(kw, "lower_disp_limit", 0.0)
    epicsChan.setField(kw, "upper_disp_limit", 0.0)
    if epicsChan.setField(kw, "count", None) != 1:
        epicsChan.char_value = ""
    else:
        try:
            enums = epicsChan.setField(kw, 'enum_strs', () )
            epicsChan.char_value = convText(epicsChan.value, epicsChan.pvType, Precision=precision, Enums=epicsChan.getEnumStrings())
        except BaseException as exc:
            # do a conversion of float or double
            print(f"text convert failure {epicsChan.value} {exc}")
            epicsChan.char_value = convText(epicsChan.value, epicsChan.pvType, Precision=precision)

    if edmApp.debug(): print("Value callback", epicsChan.name, "Value", epicsChan.value, epicsChan.char_value, "for CHID", chid, kw)

    units = epicsChan.setField(kw, 'units', "")
    for ePV in epicsChan.connectorList:
        ePV.isValid = True
        ePV.precision = precision
        ePV.value = epicsChan.value
        ePV.pvType = epicsChan.pvType
        ePV.char_value = epicsChan.char_value
        ePV.units = units
        for fn in ePV.callbackList:
            fn[0](fn[1], pvname=epicsChan.name,
            chid=chid,pv=ePV,value=value,count=epicsChan.count,units=units,severity=epicsChan.severity,userArgs=fn[2])

#
# the epicsPV class is returned when a build is done
#
class epicsPV(edmPVbase):

    def __init__(self, **kw):
        self.chan = None
        super().__init__(**kw)
        self.prefix = "EPICS\\"

    def __repr__(self):
        return f"<epicsPV {self.name} valid:{self.isValid}>"

    def edmCleanup(self):
        if self.debug(): print("epicsPV cleanup", self.name)
        if hasattr(self, "chan"):
            delChannel(self.chan, self)
        super().edmCleanup()
        
    def setPVname(self, pvName):
        ''' set the PV name.
            if already connected, disconnect from the existing channel.
        '''
        if pvName == getattr(self,"name", None): # if name hasn't changed, the connection hasn't changed.
            return
        # if we're already connected, drop the channel.
        if self.chan != None:
            delChannel(self.chan, self)

        edmPVbase.setPVname(self, pvName)
        self.chan = addChannel(pvName, self)
        # try and avoid race condition: a channel can be "valid", but not have read
        # any data back yet.
        if self.chan.isValid and hasattr(self.chan, "value"):
            # attempt various initializations. These can fail if caught in a poor
            # initialization state. Only record the PV as valid if all else succeeds.
            # If this fails, connect doesn't occur properly
            try:
                self.value = self.chan.value
                self.count = self.chan.count
                self.char_value = self.chan.char_value
                self.severity = self.chan.severity
                self.pvType = self.chan.pvType
                self.precision = getattr(self.chan, "precision", 0)
                self.units = getattr(self.chan, "units", "")
                self.isValid = self.chan.isValid
            except:
                print("Failed on setup with 'valid' channel", pvName)
                traceback.print_exc()
                return
            self.connect()

    def getPVname(self):
        return ca.name(self.chan.chid.value)

    def get(self):
        if self.isValid:
            return ca.get(self.chan.chid.value)
        return None

    def getLimits(self):
        if self.isValid == False:
            raise ValueError
        min = getattr(self.chan, "lower_disp_limit", 0.0)
        max = getattr(self.chan, "upper_disp_limit", 0.0)
        if max == min:
            raise ValueError( "Requested PV display limits are identical")
        return (min, max)
        
    def getEnumStrings(self):
        if self.isValid == False:
            return None
        return self.chan.getEnumStrings()

    def connect(self):
        # called when a connection to the PV is made
        self.getEnumStrings()
        if self.connectCallback != None:
            self.connectCallback(self, self.connectCallbackArg)

    def put(self, value):
        if self.isValid:
            if ca.write_access( self.chan.chid) == False:
                return None
            # if we're sending a string, check if it is an enum, and
            # if so, then convert it to the integer index before sending.
            if isinstance(value, str):
                enums = ca.get_enum_strings(self.chan.chid)
                if enums != None and value in enums:
                    enums = [ enums ]   # convert tuple to list?
                    value = enums.index(value)
            return ca.put( self.chan.chid, value)
        return None
   
def buildPV(**kw):
    global watcher
    if watcher == None:
        watcher = watchPV()
    return epicsPV(**kw)


pvClassDict["EPICS"] = buildPV
