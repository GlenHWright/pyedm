# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a text monitor class

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmTextFormat import convDefault, convDecimal, convHex, convEngineer, convExp
from pyedm.edmPVfactory import edmPVbase

from PyQt4.QtGui import QLineEdit, QPalette
from PyQt4.QtCore import Qt

class activeXTextDspClass_noedit(QLineEdit,edmWidget):
    displayModeList = { "default" : convDefault, "float" :convDefault, "exponential": convExp, "decimal":convDecimal, "hex":convHex, "string":convDefault }
    typeList = [ "unknown", "graphics", "monitors", "controls" ]
    V3propTable = {
        "2-12" : [ "controlPv", "font", "useDisplayBg", "fontAlign", "INDEX", "fgColor", "INDEX", "bgColor", "format", "bgAlarm", "editable", "autoHeight", "isWidget",
                "limitsFromDb", "precision", "ID", "changeCallbackFlag", "activateCallback", "deactivateCallbackFlag", "pvExprStr", "SvalColor", "nullAlarm", "fgPvExpStr", "smartRefresh", "useKp", 
                "changeValOnLoseFocus", "fastUpdate", "isDate", "isFile", "defDir", "pattern", "objType", "autoSelect", "updatePvOnDrop", "useHexPrefix", "fileComponent", "dateAsFileName",
                "showUnits", "useAlarmBorder" ]
                }

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        edmWidget.__init__(self, parent)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.setReadOnly(1)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrame(0)
        if object.getIntProperty("major") == 2:
            self.formatType = [ "default", "float", "exponential", "decimal", "hex", "string" ] [ object.getIntProperty("format", 0) ]
        else:
            self.formatType = object.getStringProperty("format", "default")
        self.precision = object.getEfIntProperty("precision", 3)
        self.showUnits = object.getIntProperty("showUnits", 0)
        self.limitsFromDb = object.getIntProperty("limitsFromDb", 0)

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,))

    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,))

    def redisplay(self, **kw):
        if self.controlPV == None:  # Where does this come from?
            return
        self.checkVisible()
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        if self.controlPV.pvType == edmPVbase.typeEnum:
            self.setText(self.controlPV.char_value)
            return
        try:
            precision = self.precision
            if self.limitsFromDb and hasattr(self.controlPV, "precision"):
                precision = self.controlPV.precision
            txt = self.displayModeList[self.formatType] (self.controlPV.value, charValue=self.controlPV.char_value, precision=precision, units=self.controlPV.units, showUnits=self.showUnits)
            self.setText(txt)
            return
        except: print "activeXTextDspClass:noedit : conversion failure"
        self.setText(self.controlPV.char_value)

edmDisplay.edmClasses["activeXTextDspClass:noedit"] = activeXTextDspClass_noedit
