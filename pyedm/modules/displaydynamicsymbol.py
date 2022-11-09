# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Manage the display of a dynamic symbol
#
# There are variations on combinations of operation mode:
#     Use items for gate OR just cycle continuously
#     Use mouse focus-in and focus-out for the gate.
#     Use PV Up/PV Down and value and transition comparisons for the gate
#     Use up/down or just up (selected by continuous?)
#
# It's really hard to tell what the intention was for the various combinations of values.
# Neither the code, nor the executable, nor the documentation really helps.
#   the gate up and down seems needlessly complicated for determining when to start and stop
#   a gate: it has to do with transitions in and out of gate mode, not the actual value.
#   What are the circumstances where this is useful?
#   useGate and gateUP enables - opposite direction of my thinking, but OK
# It only runs in the up direction. This is a 'stop'.
#
# I think this would benefit from a 'mode' that would be:
#   UpPV mask - run only when startPV is the comparison value
#   Start/Stop - much like the gate; start/stop PVs with values.
#   oneshot - move to next, then stop.
#   continuous - when at a limit, reset to other end
#   selectable - not sure - messy?
#

from .edmApp import redisplay, edmApp
from .edmWidget import edmWidget, pvItemClass
from . import edmWindowWidget
from .edmAbstractSymbol import AbstractSymbolClass
from .edmEditWidget import edmEdit
from .edmField import edmField

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea
from PyQt5.QtGui import QPalette, QPainter

# Placeholder for widget list.
class symbolState:
    def __init__(self, stateno):
        self.stateNo = stateno

class activeDynSymbolClass(AbstractSymbolClass):
    menuGroup = ["display", "Dynamic Symbol"]

    edmEntityFields = [
            edmField("gateUpPv", edmEdit.PV),
            edmField("gateDownPv", edmEdit.PV),
            edmField("file", edmEdit.String),
            edmField("useGate", edmEdit.Bool),
            edmField("gateUpValue", edmEdit.Int, defaultValue=0),
            edmField("gateDownValue", edmEdit.Int, defaultValue=1),
            edmField("initialIndex", edmEdit.Int),
            edmField("continuous", edmEdit.Bool),
            edmField("rate", edmEdit.Real),
            edmField("numStates", edmEdit.Int),
            edmField("showOOBState", edmEdit.Int),
            edmField("gateOnMouseOver", edmEdit.Bool),
            ]
                
    V3propTable = {
        "1-5" : [ "file", "gateUpPv", "gateDownPv", "useGate", "gateUpValue", "gateDownValue", "continuous", "rate", "numStates", "useOriginalSize",
                "ID", "initialIndex", "colorPv", "useOriginalColors","fgColor", "bgColor", "showOOBState", "onMouseOver" ]
                }

    def __init__(self,parent=None):
        super().__init__(parent)
        self.useGate = False        # this gets referenced in PV callbacks, that can occur before 'buildFromObject()'
        self.pvItem["gateUpPv"] = pvItemClass("gateUpName", "gateUpPV",
                                    dataCallback=self.onGateUp, dataCallbackArg=self,
                                    conCallback=self.onGateUpConnect)
        self.pvItem["gateDownPv"] = pvItemClass("gateDownName", "gateDownPV",
                                    dataCallback=self.onGateDown, dataCallbackArg=self,
                                    conCallback=self.onGateDownConnect)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.file = objectDesc.getProperty("file", None)
        self.useGate = objectDesc.getProperty("useGate",False)
        self.gateUpValue = objectDesc.getProperty("gateUpValue", 0.0)
        self.gateDownValue = objectDesc.getProperty("gateDownValue", 0.0)
        self.continuous = objectDesc.getProperty("continuous", False)
        self.rate = objectDesc.getProperty("rate", 0.0)
        self.numStates = objectDesc.getProperty("numStates", 0)
        self.initialIndex = objectDesc.getProperty("initialIndex", 0)
        self.showOOBState = objectDesc.getProperty("showOOBState", False)
        self.gateOnMouseOver = objectDesc.getProperty("gateOnMouseOver", False)

        self.statelist = [ symbolState(idx) for idx in range(0,self.numStates) ]
        self.buildStateObjects(self.file)
        self.curState = self.statelist[self.initialIndex]
        self.timerActive = False
        if self.useGate == False:
            self.needGateUp = True
            self.startOperation()
        else:
            self.needGateUp = False
        redisplay(self)

    def onGateUp(self, widget, value=None, **kw):
        # print value, self.gateUpValue
        if self.useGate == False:
            return
        self.needGateUp = (int(value) == self.gateUpValue)
        if self.needGateUp:
            self.startOperation()

    def onGateDown(self, widget, value=None, **kw):
        if self.useGate == False:
            return
        self.needGateDown = (int(value) == self.gateDownValue)
        if self.needGateDown:
            self.stopOperation()

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
        self.needGateUp = (self.useGate == False)
        self.timerActive = False
        self.killTimer(self.timerID)

    def timerEvent(self, event):
        if self.needGateUp:
            idx = self.curState.stateNo+1
            # print "need gate up:", idx, self.numStates, self.continuous
            if idx >= self.numStates:
                if self.continuous == 0:
                    self.stopOperation()
                    return
                self.curState = self.statelist[0]
            else:
                self.curState = self.statelist[idx]
        redisplay(self)

    def onGateUpConnect(self, pv, userArg, **kw):
        pass

    def onGateDownConnect(self, pv, userArg, **kw):
        pass

    def enterEvent(self, event):
        if self.useGate == False:
            return
        if self.gateOnMouseOver:
            self.needGateUp = True
            self.startOperation()

    def leaveEvent(self, event):
        if self.useGate == False:
            return
        if self.gateOnMouseOver:
            self.needGateUp = False # more nuanced than this...

    def mousePressEvent(self, event):
        edmWindowWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        edmWindowWidget.mouseReleaseEvent(self, event)

edmApp.edmClasses["activeDynSymbolClass"] = activeDynSymbolClass


