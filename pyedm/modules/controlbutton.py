# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a static text display class

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmApp import redisplay

from PyQt4.QtGui import QPushButton, QPalette
from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

class activeButtonClass(QPushButton, edmWidget):
    V3propTable = { "2-4" : [ "INDEX", "fgColor", "fgAlarm", "INDEX", "onColor", "INDEX", "offColor", "INDEX", "unknownColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "readPv", "onLabel", "offLabel", "labelType", "buttonType", "threeD", "invisible", "font", "ID", "downCallbackFlag", "upCallbackFlag", "activateCallbackFlag",
        "deactivateCallbackFlag", "objType", "visPv", "visInvert", "visMin", "visMax", "colorPv" ]
        }
    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        edmWidget.__init__(self, parent)
        # if these aren't over-ridden, then they end up being the labels by default
        self.onLabel = "1"
        self.offLabel = "0"
        self.labeltype = "pvState"
        self.needLabel = True
        self.pvItem["indicatorPv"] = [ "indicatorName", "indicatorPV", 1 ]

    def cleanup(self):
        edmWidget.cleanup(self)
        self.onColorInfo.cleanup()
        self.offColorInfo.cleanup()

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        type = self.getToggleType()
        self.setCheckable( type )
        self.setAutoFillBackground(True)
        self.labeltype = object.getStringProperty("labelType", "literal")
        if self.labeltype == "literal" or self.labeltype == "1":
            self.onLabel = self.macroExpand(object.getStringProperty("onLabel", ""))
            self.offLabel = self.macroExpand(object.getStringProperty("offLabel", ""))
            self.needLabel = False
        elif self.labeltype == "pvState" or self.labeltype == "0":
            self.needLabel = True
        if self.object.getIntProperty("invisible",0) == 1:
            self.transparent = 1
            self.setFlat(1)
        self.setText(self.offLabel)
        # if a toggle button, use the 'clicked' signal.
        if self.isCheckable():
            self.connect(self, SIGNAL("clicked(bool)"), self.onClicked)
        else:
            self.connect(self, SIGNAL("pressed()"), self.onPress)
            self.connect(self, SIGNAL("released()"), self.onRelease)
        self.edmParent.buttonInterest.append(self)
        redisplay(self)

    # background color is one of two possible rules.
    def findBgColor(self):
        self.onColorInfo = self.findColor("onColor", (QPalette.Button,) )
        self.offColorInfo = self.findColor("offColor", (QPalette.Button,) )
        self.offColorInfo.setColor()

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText,QPalette.Text), "FGalarm", "fgAlarm")
        self.fgColorInfo.setColor()
        
    def getToggleType(self):
        type = self.object.getStringProperty("buttonType")
        return (type != "push" or type != "1")

    # toggle button changed
    def onClicked(self,checked):
        if self.controlPV != None:
            self.controlPV.put(checked)

    # push putton
    def onPress(self):
        if self.controlPV != None:
            self.controlPV.put(1)

    def onRelease(self):
        if self.controlPV != None:
            self.controlPV.put(0)

    def getPositionState(self):
        try: return self.indicatorPV.value != 0
        except: pass
        try: return self.controlPV.value != 0
        except: return 0

    # completely over-ride the default redisplay
    def redisplay(self, **kw):
        self.checkVisible()
        pos = self.getPositionState()
        if self.needLabel:
            if hasattr(self,"indicatorPV") and self.indicatorPV.isValid :
                enums = self.indicatorPV.getEnumStrings()
                self.needLabel = False
            elif hasattr(self, "controlPV") and self.controlPV.isValid :
                enums = self.controlPV.getEnumStrings()
                self.needLabel = hasattr(self, "indicatorPV")
            else:
                enums = [ "0", "1" ]
            self.offLabel, self.onLabel = enums[0:2]
            
        if pos == 1:
            txt = self.onLabel
            cr = self.onColorInfo
        else:
            txt = self.offLabel
            cr = self.offColorInfo
        if txt == None:
            txt = str(pos)
        self.fgColorInfo.setColor()
        cr.setColor(force=True)
        if self.isCheckable():
            self.setChecked( pos)
        else:
            self.setDown( pos)
        self.setText( txt)
        self.update()

edmDisplay.edmClasses["activeButtonClass"] = activeButtonClass


