# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a text monitor class

from enum import Enum

from .edmApp import edmApp, redisplay
from .edmWidget import edmWidget, pvItemClass
from .edmTextFormat import convDefault, convDecimal, convHex, convEngineer, convExp
from .edmPVfactory import edmPVbase
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QPalette, QFontMetrics
from PyQt5.QtCore import Qt

class activeXTextDspClass_noedit(QLineEdit,edmWidget):
    menuGroup = [ "monitor", "Active Text" ]
    typeList = [ "unknown", "graphics", "monitors", "controls" ]
    nullCondEnum = Enum("nullCond", "nullEqCtl nullEq0 disabled", start=0)
    fileCompEnum = Enum("fileComp", "fullPath nameAndExt name", start=0)

    formatEnum = Enum("format",  "default float gfloat exponential decimal hex string" , start=0)
    displayModeList = { formatEnum(0) : convDefault,
                        formatEnum(1) : convDefault,
                        formatEnum(2) : convDefault,
                        formatEnum(3) : convExp,
                        formatEnum(4) : convDecimal,
                        formatEnum(5) : convHex,
                        formatEnum(6) : convDefault
                      }
    edmEntityFields = [
            edmField("controlPv", edmEdit.PV, defaultValue=None),
            edmField("nullPv", edmEdit.PV, defaultValue=None),
            edmField("nullCondition", edmEdit.Enum, defaultValue=None, enumList=nullCondEnum),
            edmField("nullColor", edmEdit.Color, defaultValue=None),
            edmField("format", edmEdit.Enum, defaultValue=0, enumList=formatEnum),
            edmField("hexPrefix", edmEdit.Bool, defaultValue=False),
            edmField("limitsFromDb", edmEdit.Bool, defaultValue=False),
            edmField("precision", edmEdit.Int, defaultValue=1),
            edmField("fieldLen", edmEdit.Int, defaultValue=2),
            edmField("noExecuteClipMask", edmEdit.Bool, defaultValue=False),
            edmField("clipToDspLimits", edmEdit.Bool, defaultValue=False),
            edmField("showUnits", edmEdit.Bool, defaultValue=False),
            edmField("autoHeight", edmEdit.Bool, defaultValue=False),
            edmField("smartRefresh", edmEdit.Bool, defaultValue=False),
            edmField("limitsFromDb", edmEdit.Bool, defaultValue=False),
            edmField("motifWidget", edmEdit.Bool, defaultValue=False),
            edmField("fastUpdate", edmEdit.Bool, defaultValue=False),
            ] + edmWidget.edmFontFields
    V3propTable = {
        "2-12" : [ "controlPv", "font", "useDisplayBg", "fontAlign", "INDEX", "fgColor",
                    "INDEX", "bgColor", "format", "bgAlarm", "editable", "autoHeight", "isWidget",
                    "limitsFromDb", "precision", "ID", "changeCallbackFlag", "activateCallback",
                    "deactivateCallbackFlag", "pvExprStr", "SvalColor", "nullAlarm", "fgPvExpStr",
                    "smartRefresh", "useKp", "changeValOnLoseFocus", "fastUpdate", "isDate", "isFile",
                    "defDir", "pattern", "objType", "autoSelect", "updatePvOnDrop", "useHexPrefix",
                    "fileComponent", "dateAsFileName", "showUnits", "useAlarmBorder" ]
                }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["nullPv"] = pvItemClass("nullPVname", "nullPV")
        self.nullCondition = None

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.setReadOnly(1)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrame(0)
        self.formatType = objectDesc.getProperty("format")
        self.precision = objectDesc.getProperty("precision")
        self.showUnits = objectDesc.getProperty("showUnits")
        self.precisionFromDb = objectDesc.getProperty("limitsFromDb")
        self.nullCondition = objectDesc.getProperty("nullCondition")
        self.autoHeight = objectDesc.getProperty("autoHeight") 
        if self.autoHeight or edmApp.autosize:
            fm = QFontMetrics(self.edmFont)
            h = fm.height()
            delta = h - self.height() + 2
            if delta > 0:
                geometry = self.geometry()
                yoff = delta//2
                geometry.setY(geometry.y() - yoff)
                geometry.setHeight(h+2)
                self.setGeometry(geometry)

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,))
        if getattr(self, "nullPV", None) == None:
            return
        self.fgColorInfo.addNullPV(nullPV=self.nullPV,
                                    nullColor=self.getProperty("nullColor"),
                                    nullTest=self.nullTest)

    def nullTest(self, value):
        '''nullTest() return True if value indicates a null condition'''
        if self.nullCondition == self.nullCondEnum.nullEqCtl:
            return self.controlPV.value == value
        elif self.nullCondition == self.nullCondEnum.nullEq0:
            return float(value) == 0
        return False

    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,))

    def redisplay(self, **kw):
        ''' determine how to format text for display'''
        if getattr(self, "controlPV", None) == None:  # Where does this come from?
            return
        self.checkVisible()
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        if self.controlPV.pvType == edmPVbase.typeEnum:
            txt = self.controlPV.char_value
        else:
            precision = self.precision
            try:
                if self.precisionFromDb and hasattr(self.controlPV, "precision"):
                    precision = self.controlPV.precision
                txt = self.displayModeList[self.formatType] (self.controlPV.value,
                                                        charValue=self.controlPV.char_value,
                                                        precision=precision,
                                                        units=self.controlPV.units,
                                                        showUnits=self.showUnits)
            except:
                print("activeXTextDspClass:noedit : conversion failure")
                txt = self.controlPV.char_value

        if edmApp.autosize:
            fm = QFontMetrics(self.edmFont)
            bounds = fm.boundingRect(txt)
            delta = bounds.width() - self.width() + 2
            if delta > 0:
                geometry = self.geometry()
                xoff = delta//2
                geometry.setX(geometry.x() - xoff)
                geometry.setWidth(bounds.width()+2)
                self.setGeometry(geometry)

        self.setText(txt)

edmApp.edmClasses["activeXTextDspClass:noedit"] = activeXTextDspClass_noedit
