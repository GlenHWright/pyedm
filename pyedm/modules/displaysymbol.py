from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# symbolClass Use portions of an edl file based on top-level "group" classification.
# This class uses PV's to compute and index, and redisplays the "subset" with the
# computed entry.
#
from builtins import zip
from builtins import range
from builtins import object
import pyedm.edmDisplay as edmDisplay
from pyedm.edmPVfactory import buildPV
from pyedm.edmApp import redisplay
from pyedm.edmWidget import edmWidget
import pyedm.edmWindowWidget as edmWindowWidget
from pyedm.edmAbstractSymbol import AbstractSymbolClass

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPalette, QPainter
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea

class symbolState(object):
    def __init__(self, min=0, max=1):
        self.min = min
        self.max = max

class symbolPV(object):
    def __init__(self, pvname, mt, idx, andMask=0, xorMask=0, shift=0):
        self.pv = buildPV(pvname,macroTable=mt)
        self.pvno = idx
        self.val = 0.0
        self.ival = 0
        self.andMask = andMask
        self.xorMask = xorMask
        self.shift = shift

class activeSymbolClass(AbstractSymbolClass):
    '''selects a "group" from an edm symbol file based on a calculated value'''
    V3propTable = {
        "1-5" : [   "file", "gateUpPv", "gateDownPv", "gateDownValue", "continuous", "rate", "numStates", "useOriginalSize",
            "ID", "initialIndex", "colorPv", "useOriginalColors", "fgColor", "bgColor", "showOOBState", "gateOnMouseOver" ]
    }
        
    def __init__(self, parent=None):
        super().__init__(parent)

    def cleanup(self):
        AbstractSymbolClass.cleanup(self)
        for pv in self.pvList:
            pv.pv.del_callback(self)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)
        self.file = object.getStringProperty("file", "")
        self.truthTable = object.getIntProperty("truthTable", 0)
        # PV information
        self.numPvs = object.getIntProperty("numPvs", 0)
        self.controlPvs = object.decode("controlPvs", self.numPvs, None)
        self.andMask = object.decode("andMask", self.numPvs, 0)
        self.xorMask = object.decode("xorMask", self.numPvs, 0)
        self.shiftCount = object.decode("shiftCount", self.numPvs, 0)
        # State information
        self.statelist = []
        self.numStates = object.getIntProperty("numStates", 0)
        self.minValues = object.decode("minValues", self.numStates, 0)
        self.maxValues = object.decode("maxValues", self.numStates, 1)

        if(self.minValues == None):
            self.minValues = [0,0]
        if(self.maxValues == None):
            self.maxValues = [1,1]

        if self.numStates > 0:
            self.statelist = [ symbolState(item[0], item[1]) for item in zip(self.minValues, self.maxValues) ]

        self.buildStateObjects(self.file)
        self.idxState = 0

        # set up callbacks for PV's
        self.pvList = []
        mt = self.findMacroTable()
        for idx in range(0,self.numPvs):
            pv = symbolPV(self.controlPvs[idx], mt, idx)
            self.pvList.append(pv)
            try:
                pv.andMask = self.andMask[idx]
            except:
                pv.andMask = 0
            try:
                pv.xorMask = self.xorMask[idx]
            except:
                pv.xorMask = 0
            try:
                pv.shiftCount = self.shiftCount[idx]
            except:
                pv.shiftCount = 0
            pv.pv.add_callback(self.calcState, self, pv)
            
    def calcState(self, item, **kw):
        if 'userArgs' not in kw:
            return
        thispv = kw['userArgs']
        thispv.val = kw["value"]
        thispv.ival = int(thispv.val)
        if self.truthTable:
            if thispv.val == 0.0:
                self.idxState = self.idxState & ~(1<<thispv.idx)
            else:
                self.idxState = self.idxState | (1<<thispv.idx)
            self.curState = self.statelist[self.idxState]
            redisplay(self)
            return
        if self.numPvs == 1 and thispv.andMask == 0 and thispv.xorMask == 0 and thispv.shiftCount == 0:
            istate = thispv.ival
        else:
            ival = thispv.ival
            if self.andMask[idx]:
                ival = ival & self.andMask[idx]
            ival = ival ^ self.xorMask[idx]
            if self.shiftCount[idx] < 0:
                ival = ival >> (-self.shiftCount[idx])
            else:
                ival = ival << self.shiftCount[idx]
            thispv.ival = ival
            istate = 0
            for pv in self.pvList:
                istate = istate | pv.ival

        for item in self.statelist:
            if istate >= item.min and istate < item.max:
                self.curState = item
                redisplay(self)
                return
        print("No state selected: istate=%d, count=%d/%d" % (istate, len(self.statelist),self.numStates))

    def mousePressEvent(self, event):
        edmWindowWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        edmWindowWidget.mouseReleaseEvent(self, event)

edmDisplay.edmClasses["activeSymbolClass"] = activeSymbolClass


