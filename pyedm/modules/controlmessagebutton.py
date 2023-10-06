# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget to set a PV to a value on press or release
# from pyedm.controlbutton import activeButtonClass
#
#
from pyedm import edmImport
controlbutton = edmImport("controlbutton")
activeButtonClass = controlbutton.activeButtonClass

from .edmField import edmField
from .edmWidget import pvItemClass
from .edmEditWidget import edmEdit
from .edmApp import edmApp

class activeMessageButtonClass (activeButtonClass):

    menuGroup = [ "control", "Message Button"]
    edmEntityFields = [
            edmField("pressValue", edmEdit.String),
            edmField("releaseValue", edmEdit.String),
            edmField("toggle", edmEdit.Bool, defaultValue=False),
            ] + activeButtonClass.edmEntityFields

    V3propTable = {
        "2-1" : [ "fgColor", "onColor", "offColor", "topShadowColor", "botShadowColor",
            "controlPv", "PressValue", "ReleaseValue", "onLabel", "offLabel", "toggle", "pressAction", "releaseAction", "3D", "invisible", "font",
            "password", "lock", "visPv", "visInvert", "visMin", "visMax", "colorPv", "useEnumNumeric" ] ,
        "2-5" : [ "INDEX", "fgColor", "INDEX", "onColor", "INDEX", "offColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "controlPv", "PressValue", "ReleaseValue", "onLabel", "offLabel", "toggle", "pressAction", "releaseAction", "3D", "invisible", "font",
            "password", "lock", "visPv", "visInvert", "visMin", "visMax", "colorPv", "useEnumNumeric" ]
        }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.PressedState = 0

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.pushValue = objectDesc.getProperty("pressValue")
        self.releaseValue = objectDesc.getProperty("releaseValue")
        if self.releaseValue == "":
            self.releaseValue = None

    # toggle type is determined by "toggle" property
    def getToggleType(self):
        return self.objectDesc.getProperty("toggle")

    # change the onPress() callback to set the label value
    def onPress(self):
        self.PressedState = 1
        if self.pushValue != None and self.controlPV != None:
            self.controlPV.put(self.pushValue)
        self.drawButton(self.onColorInfo, self.onLabel)

    # change the onRelease() callback to set the label value
    def onRelease(self):
        self.PressedState = 0
        if self.releaseValue != None and self.controlPV != None:
            self.controlPV.put(self.releaseValue)
        self.drawButton(self.offColorInfo, self.offLabel)

    def drawButton(self, color, text):
        self.checkVisible()
        self.fgColorInfo.setColor()
        color.setColor(force=True)
        self.setText( text)
        self.update()

    def redisplay(self):
        if self.PressedState:
            self.drawButton(self.onColorInfo, self.onLabel)
        else:
            self.drawButton(self.offColorInfo, self.offLabel)

    def onClicked(self, clicked):
        if clicked:
            self.onPress()
        else:
            self.onRelease()

activeMessageButtonClass.buildFieldListClass("edmEntityFields", "edmFontFields")

edmApp.edmClasses["activeMessageButtonClass"] = activeMessageButtonClass
