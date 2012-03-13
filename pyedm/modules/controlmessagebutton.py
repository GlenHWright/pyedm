# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget to set a PV to a value on press or release
# from pyedm.controlbutton import activeButtonClass
controlbutton = __import__("controlbutton", globals(), locals(), 1)
activeButtonClass = controlbutton.activeButtonClass

import pyedm.edmDisplay as edmDisplay

class activeMessageButtonClass (activeButtonClass):

    V3propTable = {
        "2-5" : [ "INDEX", "fgColor", "INDEX", "onColor", "INDEX", "offColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "controlPv", "PressValue", "ReleaseValue", "onLabel", "offLabel", "toggle", "pressAction", "releaseAction", "3D", "invisible", "font",
            "password", "lock", "visPv", "visInvert", "visMin", "visMax", "colorPv", "useEnumNumeric" ]
        }

    def __init__(self, parent=None):
        activeButtonClass.__init__(self, parent)
        self.PressedState = 0

    def buildFromObject(self, object):
        activeButtonClass.buildFromObject(self, object)
        self.pushValue = object.getStringProperty("pressValue")
        self.releaseValue = object.getStringProperty("releaseValue")

    # toggle type is determined by "toggle" property
    def getToggleType(self):
        ty = self.object.getIntProperty("toggle")
        return ty==1

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

edmDisplay.edmClasses["activeMessageButtonClass"] = activeMessageButtonClass
