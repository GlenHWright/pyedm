# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a static text display class

from enum import Enum
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField
from .edmEditWidget import edmEdit
from .edmApp import redisplay, edmApp

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPalette
from PyQt5 import QtCore

class activeButtonClass(QPushButton, edmWidget):
    menuGroup = [ "control", "Button" ]
    labelTypeEnum = Enum("labelType", "pvState literal", start=0)
    buttonTypeEnum = Enum("buttonType", "toggle push", start=0)
    objTypeEnum = Enum("objType", "unknown graphics monitors controls", start=0)
    edmEntityFields = [
            edmField("invisible", edmEdit.Bool, defaultValue=False),
            edmField("onColor", edmEdit.Color),
            edmField("offColor", edmEdit.Color),
            edmField("unknownColor", edmEdit.Color),
            edmField("topShadowColor", edmEdit.Color),
            edmField("botShadowColor", edmEdit.Color),
            edmField("indicatorPv", edmEdit.PV),
            edmField("controlPv", edmEdit.PV),
            edmField("readPv", edmEdit.PV),
            edmField("onLabel", edmEdit.String),
            edmField("offLabel", edmEdit.String),
            edmField("labelType", edmEdit.Enum, enumList=labelTypeEnum, defaultValue=1),
            edmField("buttonType", edmEdit.Bool, enumList=buttonTypeEnum, defaultValue=1),
            edmField("threeD", edmEdit.Bool, defaultValue=False),
            edmField("objType", edmEdit.Enum, enumList=objTypeEnum, defaultValue=0)
            ]
    V3propTable = {
        "2-1" : [ "fgColor", "fgAlarm", "onColor", "offColor", "unknownColor", "topShadowColor", "botShadowColor",
        "controlPv", "readPv", "onLabel", "offLabel", "labelType", "buttonType", "threeD", "invisible", "font", "ID", "downCallbackFlag", "upCallbackFlag", "activateCallbackFlag",
        "deactivateCallbackFlag", "objType", "visPv", "visInvert", "visMin", "visMax", "colorPv" ],
        "2-4" : [ "INDEX", "fgColor", "fgAlarm", "INDEX", "onColor", "INDEX", "offColor", "INDEX", "unknownColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "readPv", "onLabel", "offLabel", "labelType", "buttonType", "threeD", "invisible", "font", "ID", "downCallbackFlag", "upCallbackFlag", "activateCallbackFlag",
        "deactivateCallbackFlag", "objType", "visPv", "visInvert", "visMin", "visMax", "colorPv" ]
        }
    def __init__(self, parent=None, **kw):
        super().__init__(parent=parent, **kw)
        # if these aren't over-ridden, then they end up being the labels by default
        self.pvItem["indicatorPv"] = pvItemClass( "indicatorName", "indicatorPV", redisplay=True)

    def edmCleanup(self):
        self.disconnect()
        self.onColorInfo.edmCleanup()
        self.offColorInfo.edmCleanup()
        super().edmCleanup()

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.setCheckable( self.getToggleType() )
        self.setAutoFillBackground(True)
        self.labeltype = objectDesc.getProperty("labelType")
        if self.labeltype == self.labelTypeEnum.literal:
            self.onLabel = self.macroExpand(objectDesc.getProperty("onLabel"))
            self.offLabel = self.macroExpand(objectDesc.getProperty("offLabel"))
            self.needLabel = False
        elif self.labeltype == self.labelTypeEnum.pvState:
            self.needLabel = True
            self.onLabel, self.offLabel = "1", "0"
        if self.objectDesc.getProperty("invisible") == True:
            self.transparent = True
            self.setFlat(1)
        self.setText(self.offLabel)
        # if a toggle button, use the 'clicked' signal.
        if self.isCheckable():
            self.clicked.connect(self.onClicked)
        else:
            self.pressed.connect(self.onPress)
            self.released.connect(self.onRelease)
        self.edmParent.buttonInterest.append(self)
        redisplay(self)

    # background color is one of two possible rules.
    def findBgColor(self):
        self.onColorInfo = self.findColor("onColor", (QPalette.Button,) )
        self.offColorInfo = self.findColor("offColor", (QPalette.Button,) )
        self.offColorInfo.setColor()

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText,QPalette.Text), alarmName="fgAlarm")
        self.fgColorInfo.setColor()
        
    def getToggleType(self):
        return self.getProperty("buttonType") == self.buttonTypeEnum.toggle

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
        if self.transparent:
            return
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

activeButtonClass.buildFieldListClass("edmEntityFields", "edmFontFields")

edmApp.edmClasses["activeButtonClass"] = activeButtonClass


