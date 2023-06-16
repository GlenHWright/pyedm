# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a display for drop-down menu

# Oct/2022 reads the description, but doesn't implement anything yet
#
# MenuMux takes the value of the control PV, and uses this as an index
# into the list of symbols and values for Macros, and resets macro
# values based on the symbol. this doesn't effect any of the current
# screen values, but should update values for new screens getting called.
#
from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmField import edmField, edmTag
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtCore
#from PyQt5.QtCore import SIGNAL

class menuMuxClass(QComboBox,edmWidget):
    menuGroup = ["control", "Menu Mux"]
    edmEntityFields = [
            edmField("controlPv", edmEdit.PV, defaultValue=None),
            edmField("numItems", edmEdit.Int, defaultValue=2),
            edmField("initialState", edmEdit.Int, defaultValue=0),
            edmField("symbolTag", edmEdit.String, array=True),
            edmField("symbol0", edmEdit.String, array=True, hidden=True),
            edmField("value0", edmEdit.String, array=True, hidden=True),
            edmField("symbol1", edmEdit.String, array=True, hidden=True),
            edmField("value1", edmEdit.String, array=True, hidden=True),
            edmField("symbol2", edmEdit.String, array=True, hidden=True),
            edmField("value2", edmEdit.String, array=True, hidden=True),
            edmField("symbol3", edmEdit.String, array=True, hidden=True),
            edmField("value3", edmEdit.String, array=True, hidden=True),
            edmField("symbol4", edmEdit.String, array=True, hidden=True),
            edmField("value4", edmEdit.String, array=True, hidden=True),
            edmField("symbol5", edmEdit.String, array=True, hidden=True),
            edmField("value5", edmEdit.String, array=True, hidden=True),
            edmField("symbol6", edmEdit.String, array=True, hidden=True),
            edmField("value6", edmEdit.String, array=True, hidden=True),
            edmField("symbol7", edmEdit.String, array=True, hidden=True),
            edmField("value7", edmEdit.String, array=True, hidden=True),
            ] + edmWidget.edmFontFields
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
    def setV3PropertyList(classRef, values, obj):
        '''explicit conversion of the variable length paramenter list in V3 files
        '''
        print("controlmenumux tags=", obj.tags, "values=", values)
        idx = "%s-%s" % (obj.tags['major'].value, obj.tags['minor'].value)
        
        try:
            for name in menuMuxClass.V3propTable[idx]:
                obj.addTag(name, values.pop(0))
        except:
            print("menuMuxClass V3 tags/values failure:", idx, obj.tags, values)

        numItems = int(tags["numItems"].value)
        st = []
        for idx in range(0,numItems):
            st.append(values.pop(0))
        obj.addTag("symbolTag", st)
        for idx in range(0,numItems):
            names=[]
            symbols=[]
            for idx2 in range(0,4):
                names.append( values.pop(0))
                symbols.append( values.pop(0))
            obj.addTag(f"value{idx}", names)
            obj.addTag(f"symbol{idx}", symbols)

        obj.addTag("initialState", values.pop(0))
        print("controlmenumux tags=", obj.tags, "values=", values)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.initialState = self.objectDesc.getProperty("initialState")
        self.numItems = self.objectDesc.getProperty("numItems")
        self.symbolTag = self.objectDesc.getProperty("symbolTag",arrayCount=1)
        self.valueList = [None]*self.numItems
        self.symbolList = [None]*self.numItems
        for i in range(0, self.numItems):
            valname = "value%d"%(i,)
            self.valueList[i] =  self.objectDesc.getProperty(valname)
            symname = "symbol%d"%(i,)
            self.symbolList[i] =  self.objectDesc.getProperty(symname)
        while self.count() > 0:
            self.removeItem(0)
        self.addItems( self.symbolTag)
        self.setCurrentIndex(self.initialState)
        self.activated.connect(self.gotNewValue)

    def gotNewValue(self, value):
        if hasattr(self, "controlPV"):
            if self.controlPV.value == value:
                return
            self.controlPV.put( value)

    def redisplay(self):
    # called when the control PV changes
        self.checkVisible()
        if self.controlPV.value < 0 or self.controlPV.value >= self.numItems:
            return
        if self.controlPV.value != self.currentIndex():
            self.setCurrentIndex(self.controlPV.value)


edmApp.edmClasses["menuMuxClass"] = menuMuxClass
