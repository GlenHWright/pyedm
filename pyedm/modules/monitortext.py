# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages simple text updates

from enum import Enum
from .edmPVfactory import edmPVbase
from .edmApp  import edmApp
from .edmWidget import edmWidget
from .edmTextFormat import convDefault, convDecimal, convHex, convEngineer, convExp
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt


class TextupdateClass(QLineEdit,edmWidget):
    menuGroup = [ "monitor", "Text Update" ]
    displayModeEnum = Enum("displayMode", "default decimal hex engineer exp", start=0)
    displayModeList = {
                                displayModeEnum(0) : convDefault,
                                displayModeEnum(1) : convDecimal,
                                displayModeEnum(2) : convHex,
                                displayModeEnum(3) : convEngineer,
                                displayModeEnum(4) : convExp
                            }

    V3propTable = {
        "7-0" : [ "controlPv", "displayMode", "precision", "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "colorPv", "fill", "font", "fontAlign", "lineWidth", "lineAlarm" ]
        }

    edmEntityFields = [
        edmField("controlPv", edmEdit.PV, defaultValue=None),
        edmField("precision", edmEdit.Int, defaultValue=0),
        edmField("displayMode", edmEdit.Enum, defaultValue="default", enumList=displayModeEnum),
        edmField("fill", edmEdit.Bool, defaultValue=False)
        ]

    edmFieldList = edmWidget.edmBaseFields + edmWidget.edmColorFields  + edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields

    def __init__(self, parent=None):
        super().__init__(parent)
        self.haveFocus = 0

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject( objectDesc, **kw)
        self.setReadOnly(1)
        self.setFrame(0)
        self.setFocusPolicy(Qt.NoFocus)
        self.precision = self.objectDesc.getProperty("precision", 0)
        # note that V3 and V4 switch int and string values. Use of Enum sorts this out at a lower level
        self.displayMode = self.objectDesc.getProperty("displayMode", "default")

    # unfortunately, TextupdateClass has its own configuration for
    # determining background color (use parent the default, unless
    # 'fill' is set). This differs from the 'useDisplayBg' in use
    # for other widgets
    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,),fillName="fill", fillTest=0)

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,))

    def redisplay(self, **kw):
        if not hasattr(self, "controlPV") or self.controlPV == None:
            return
        self.checkVisible()
        if self.haveFocus:
            return
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        try:
            if self.precision == 0:
                self.precision = self.controlPV.precision
        except: pass
        try:
            if self.controlPV.pvType == edmPVbase.typeEnum:  # the hard decisions have already been made.
                self.setText(self.controlPV.char_value)
                return
            txt = self.displayModeList[self.displayMode](self.controlPV.value, charValue=self.controlPV.char_value, precision=self.precision, units=self.controlPV.units,showUnits=(self.displayMode == "default") )
            self.setText(txt)
            return
        except:
            print("Textupdate: conversion failure")
        self.setText(self.controlPV.char_value)

edmApp.edmClasses["TextupdateClass"] = TextupdateClass
