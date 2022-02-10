# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a display for drop-down menu
from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtCore
#from PyQt5.QtCore import SIGNAL

class menuMuxClass(QComboBox,edmWidget):
    V3propTable = {
        "2-0" : 
        [ "x", "y", "w", "h", "fgColor", "fgColorMode", "bgColor", "bgColorMode",
                "topShadowColor", "botShadowColor", "controlPv", "font", "numItems" ], 
        "2-2" :
        [ "x", "y", "w", "h", "INDEX", "fgColor", "fgColorMode", "INDEX", "bgColor", "bgColorMode",
                "INDEX", "topShadowColor", "INDEX", "botShadowColor", "controlPv", "font", "numItems" ]
    }
    def __init__(self,parent=None):
        super().__init__(parent)
        self.edmParent.buttonInterest.append(self)
        self.lastIndex = -1

    # over-ride the default method.
    @classmethod
    def setV3PropertyList(classRef, values, tags):
        '''explicit conversion of the variable length paramenter list in V3 files
        '''
        print("controlmenumux tags=", tags, "values=", values)
        idx = "%s-%s" % (tags['major'], tags['minor'])
        
        try:
            for name in menuMuxClass.V3propTable[idx]:
                tags[name] = values.pop(0)
        except:
            print("menuMuxClass V3 tags/values failure:", idx, tags, values)

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
        print("controlmenumux tags=", tags, "values=", values)

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
        #self.connect( self, SIGNAL("activated(int)"), self.gotNewValue)
        self.activated.connect(self.gotNewValue)

    def gotNewValue(self, value):
        print("menumux: ignoring new value")
        return
        if hasattr(self, "controlPV"):
            self.controlPV.put( value)

    def redisplay(self):
    # called when the control PV changes
        self.checkVisible()
        if self.controlPV.value < 0 or self.controlPV.value >= self.numItems:
            return
        self.setCurrentIndex(self.controlPV.value)


edmDisplay.edmClasses["menuMuxClass"] = menuMuxClass
