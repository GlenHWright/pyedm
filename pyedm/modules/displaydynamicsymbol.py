# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Manage the display of a dynamic symbol
#
# There are variations on combinations of operation mode:
#     Use items for gate OR just cycle continuously
#     Use mouse focus-in and focus-out for the gate.
#     Use PV Up/PV Down and value comparisons for the gate
#     Use up/down or just up (selected by continuous)

from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmApp import redisplay
from pyedm.edmWidget import edmWidget
import pyedm.edmWindowWidget as edmWindowWidget
from pyedm.edmAbstractSymbol import AbstractSymbolClass

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea
from PyQt5.QtGui import QPalette, QPainter

# Placeholder for widget list.
class symbolState:
    def __init__(self, stateno):
        self.stateNo = stateno

class activeDynSymbolClass(AbstractSymbolClass):

    V3propTable = {
        "1-5" : [ "file", "gateUpPv", "gateDownPv", "useGate", "gateUpValue", "gateDownValue", "continuous", "rate", "numStates", "useOriginalSize",
                "ID", "initialIndex", "colorPv", "useOriginalColors","fgColor", "bgColor", "showOOBState", "onMouseOver" ]
                }

    def __init__(self,parent=None):
        super().__init__(parent)
        self.pvItem["gateUpPv"] = ["gateUpName", "gateUpPV", 0 , self.onGateUp, self, self.onGateUpConnect, None]
        self.pvItem["gateDownPv"] = ["gateDownName", "gateDownPV", 0, self.onGateDown, self, self.onGateDownConnect, None]
        self.useGate = False

    def buildFromObject(self, objectDesc):
        AbstractSymbolClass.buildFromObject(self,objectDesc)
        self.file = objectDesc.getStringProperty("file", None)
        self.useGate = objectDesc.getIntProperty("useGate",0)
        self.gateUpValue = objectDesc.getDoubleProperty("gateUpValue", 0.0)
        self.gateDownValue = objectDesc.getDoubleProperty("gateDownValue", 1.0)
        self.continuous = objectDesc.getIntProperty("continuous", False)
        self.rate = objectDesc.getDoubleProperty("rate", 0.0)
        self.numStates = objectDesc.getIntProperty("numStates", None)
        self.initialIndex = objectDesc.getIntProperty("initialIndex", None)
        self.showOOBState = objectDesc.getIntProperty("showOOBState", None)
        self.gateOnMouseOver = objectDesc.getIntProperty("gateOnMouseOver", None)

        self.statelist = [ symbolState(idx) for idx in range(0,self.numStates) ]
        self.buildStateObjects(self.file)
        self.curState = self.statelist[1]
        self.timerActive = False
        self.needGateUp = False
        self.needGateDown = False
        redisplay(self)

    def onGateUp(self, widget, value=None, **kw):
        # print value, self.gateUpValue
        if self.useGate == False:
            return
        self.needGateUp = (float(value) == self.gateUpValue)
        if hasattr(self, "gateDownPV") == 0 and float(value) == self.gateDownValue:
            self.needGateDown = self.continuous
        # print self.needGateUp, self.needGateDown
        if self.needGateUp or self.needGateDown:
            self.startOperation()

    def onGateDown(self, widget, value=None, **kw):
        if self.useGate == False:
            return
        self.needGateDown = ( self.continuous and (float(value) == self.gateDownValue))
        if hasattr(self, "gateUpPV") == 0 and float(value) == self.gateUpValue:
            self.needGateUp = True
        # print self.needGateUp, self.needGateDown
        if self.needGateUp or self.needGateDown:
            self.startOperation()

    def startOperation(self):
        if self.timerActive:
            return
        self.timerActive = True
        if self.rate <= 0.0:
            self.rate = 1.0
        self.timerID = self.startTimer(self.rate*1000)
    
    def stopOperation(self):
        if not self.timerActive:
            return
        self.timerActive = False
        self.killTimer(self.timerID)

    def timerEvent(self, event):
        # print 'timerEvent'
        if self.needGateDown:
            idx = self.curState.stateNo
            if idx < 0:
                if self.continuous == 0:
                    self.stopOperation()
                    return
                self.curState = self.statelist[-1]
            else:
                self.curState = self.statelist[idx-1]
        elif self.needGateUp:
            idx = self.curState.stateNo
            # print "need gate up:", idx, self.numStates, self.continuous
            if idx >= self.numStates-1:
                if self.continuous == 0:
                    self.stopOperation()
                    return
                self.curState = self.statelist[1]
            else:
                self.curState = self.statelist[idx+1]
        redisplay(self)

    def onGateUpConnect(self, pv, userArg, **kw):
        pass

    def onGateDownConnect(self, pv, userArg, **kw):
        pass

    def enterEvent(self, event):
        if self.useGate == False:
            return
        if self.gateOnMouseOver:
            self.needGateUp = 1

    def leaveEvent(self, event):
        if self.useGate == False:
            return
        if self.gateOnMouseOver:
            self.needGateDown = self.continuous

    def mousePressEvent(self, event):
        edmWindowWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        edmWindowWidget.mouseReleaseEvent(self, event)

edmDisplay.edmClasses["activeDynSymbolClass"] = activeDynSymbolClass


