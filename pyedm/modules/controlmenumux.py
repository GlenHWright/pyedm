# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a display for drop-down menu
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt4.QtGui import QComboBox
from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

class menuMuxClass(QComboBox,edmWidget):
    def __init__(self,parent=None):
        QComboBox.__init__(self,parent)
        edmWidget.__init__(self,parent)
        self.edmParent.buttonInterest.append(self)
        self.lastIndex = -1

    # over-ride the default method.
    @classmethod
    def setV3PropertyList(classRef, values, tags):
        '''explicit conversion of the variable length paramenter list in V3 files
        '''
        for name in [ "x", "y", "w", "h", "INDEX", "fgColor", "fgColorMode", "INDEX", "bgColor", "bgColorMode",
                "INDEX", "topShadowColor", "INDEX", "botShadowColor", "controlPv", "font", "numItems" ]:
            tags[name] = values.pop(0)

        numItems = int(tags["numItems"])
        st = []
        for idx in range(0,numItems):
            st.append(values.pop(0))
        tags["symbolTag"] = st
        for idx in range(0,numItems):
            names=[]
            symbols=[]
            for idx2 in range(0,4):
                names.append( values.pop(0))
                symbols.append( values.pop(0))
            tags[ "value%d"%(idx,)] = names
            tags[ "symbol%d"%(idx,)] = symbols

        tags["initialState"] = values.pop(0)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.initialState = self.object.getIntProperty("initialState", 0)
        self.numItems = self.object.getIntProperty("numItems", 0)
        self.symbolTag = self.object.decode("symbolTag")
        self.valueList = [None]*self.numItems
        self.symbolList = [None]*self.numItems
        for i in range(0, self.numItems):
            valname = "value%d"%(i,)
            self.valueList[i] =  self.object.decode(valname)
            symname = "symbol%d"%(i,)
            self.symbolList[i] =  self.object.decode(symname)
        self.addItems( self.symbolTag)
        self.setCurrentIndex(self.initialState)
        self.connect( self, SIGNAL("activated(int)"), self.gotNewValue)

    def gotNewValue(self, value):
        if hasattr(self, "controlPV"):
            self.controlPV.put( value)

    def redisplay(self):
    # called when the control PV changes
        self.checkVisible()
        if self.controlPV.value < 0 or self.controlPV.value >= self.numItems:
            return
        self.setCurrentIndex(self.controlPV.value)


edmDisplay.edmClasses["menuMuxClass"] = menuMuxClass
