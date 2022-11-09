# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a display for drop-down menu
from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtCore
#from PyQt5.QtCore import SIGNAL

class activeMenuButtonClass(QComboBox,edmWidget):
    menuGroup = [ "control", "Menu Button" ]
    edmEntityFields = [
            edmField("controlPv", edmEdit.PV),
            edmField("readPv", edmEdit.PV),
            edmField("indicatorPv", edmEdit.PV),
            edmField("inconsistentColor", edmEdit.Color)
            ]
    edmFieldList = \
        edmWidget.edmBaseFields + edmWidget.edmColorFields  \
        + edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields

    V3propTable = {
        "2-4" : [ "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "bgAlarm", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "font", "readPv", "inconsistentColor", "visPv", "colorPv" ]
        }

    def __init__(self,parent=None):
        super().__init__(parent)
        self.pvItem["controlPv"] = pvItemClass( "controlName", "controlPV", redisplay=True, conCallback=self.onConnect )
        self.pvItem["indicatorPv"] = pvItemClass( "indicatorName", "indicatorPV", redisplay=True, conCallback=self.onConnect )
        self.edmParent.buttonInterest.append(self)
        self.menu = ()
        self.displayPV = None
        self.lastIndex = -1

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.displayPV = self.indicatorPV if hasattr(self, "indicatorPV") else getattr(self,"controlPV",None)
        self.activated.connect(self.gotNewValue)

    def gotNewValue(self, value):
        if hasattr(self, "controlPV"):
            if value != self.lastIndex:
                self.lastIndex = value
                self.controlPV.put( value)

    def redisplay(self):
    # called when the indicator PV changes
        self.checkVisible()
        if self.menu == () or self.menu == None:
            self.menu = self.displayPV.getEnumStrings();
            if self.menu == None or self.menu == ():
                return
            self.clear()
            self.addItems(self.menu)
        if self.displayPV != None and self.displayPV.isValid :
            self.lastIndex = self.displayPV.value
            self.setCurrentIndex(self.displayPV.value)

    def onConnect(self, pv, arg, **kw):
        if pv != self.displayPV:
            return
        self.menu = pv.getEnumStrings()
        if self.menu == None or self.menu == ():
            return
        self.clear()
        self.addItems(self.menu)

edmApp.edmClasses["activeMenuButtonClass"] = activeMenuButtonClass
