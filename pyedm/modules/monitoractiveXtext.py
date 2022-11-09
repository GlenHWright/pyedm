# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a text monitor class

from enum import Enum

from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmTextFormat import convDefault, convDecimal, convHex, convEngineer, convExp
from .edmPVfactory import edmPVbase
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

class activeXTextDspClass_noedit(QLineEdit,edmWidget):
    menuGroup = [ "monitor", "Active Text" ]
    typeList = [ "unknown", "graphics", "monitors", "controls" ]
    formatEnum = Enum("format",  "default float exponential decimal hex string" , start=0)
    displayModeList = { formatEnum(0) : convDefault,
                        formatEnum(1) : convDefault,
                        formatEnum(2) : convExp,
                        formatEnum(3) : convDecimal,
                        formatEnum(4) : convHex,
                        formatEnum(5) : convDefault
                      }
    edmEntityFields = [
            edmField("controlPv", edmEdit.PV, defaultValue=None),
            edmField("format", edmEdit.Enum, defaultValue=0, enumList=formatEnum),
            edmField("precision", edmEdit.Int, defaultValue=2),
            edmField("showUnits", edmEdit.Bool, defaultValue=False),
            edmField("limitsFromDb", edmEdit.Bool, defaultValue=False)
            ] + edmWidget.edmFontFields
    V3propTable = {
        "2-12" : [ "controlPv", "font", "useDisplayBg", "fontAlign", "INDEX", "fgColor", "INDEX", "bgColor", "format", "bgAlarm", "editable", "autoHeight", "isWidget",
                "limitsFromDb", "precision", "ID", "changeCallbackFlag", "activateCallback", "deactivateCallbackFlag", "pvExprStr", "SvalColor", "nullAlarm", "fgPvExpStr", "smartRefresh", "useKp", 
                "changeValOnLoseFocus", "fastUpdate", "isDate", "isFile", "defDir", "pattern", "objType", "autoSelect", "updatePvOnDrop", "useHexPrefix", "fileComponent", "dateAsFileName",
                "showUnits", "useAlarmBorder" ]
                }

    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.setReadOnly(1)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrame(0)
        # removed a strange piece of code that seemed redundant. This may break older uses of "format"
        self.formatType = objectDesc.getProperty("format", "default")
        self.precision = objectDesc.getProperty("precision", 2)
        self.showUnits = objectDesc.getProperty("showUnits", 0)
        self.limitsFromDb = objectDesc.getProperty("limitsFromDb", 0)

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,))

    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,))

    def redisplay(self, **kw):
        
        if getattr(self, "controlPV", None) == None:  # Where does this come from?
            return
        self.checkVisible()
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        if self.controlPV.pvType == edmPVbase.typeEnum:
            self.setText(self.controlPV.char_value)
            return
        precision = self.precision
        try:
            if self.limitsFromDb and hasattr(self.controlPV, "precision"):
                precision = self.controlPV.precision
            txt = self.displayModeList[self.formatType] (self.controlPV.value, charValue=self.controlPV.char_value, precision=precision, units=self.controlPV.units, showUnits=self.showUnits)
            self.setText(txt)
            return
        except: print("activeXTextDspClass:noedit : conversion failure")
        self.setText(self.controlPV.char_value)

edmApp.edmClasses["activeXTextDspClass:noedit"] = activeXTextDspClass_noedit
