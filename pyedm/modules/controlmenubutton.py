# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a display for drop-down menu
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt4.QtGui import QComboBox
from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

class activeMenuButtonClass(QComboBox,edmWidget):
    V3propTable = {
        "2-4" : [ "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "bgAlarm", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "font", "readPv", "inconsistentColor", "visPv", "colorPv" ]
        }

    def __init__(self,parent=None):
        QComboBox.__init__(self,parent)
        edmWidget.__init__(self,parent)
        self.pvItem["controlPv"] = [ "controlName", "controlPV", 1, None, None, self.onConnect, None ]
        self.pvItem["indicatorPv"] = [ "indicatorName", "indicatorPV", 1, None, None, self.onConnect, None ]
        self.edmParent.buttonInterest.append(self)
        self.menu = ()
        self.displayPV = None
        self.lastIndex = -1

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.displayPV = self.indicatorPV if hasattr(self, "indicatorPV") else getattr(self,"controlPV",None)
        self.connect( self, SIGNAL("activated(int)"), self.gotNewValue)

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

edmDisplay.edmClasses["activeMenuButtonClass"] = activeMenuButtonClass
