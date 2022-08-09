from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages simple text updates

from pyedm.edmPVfactory import edmPVbase
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmTextFormat import convDefault, convDecimal, convHex, convEngineer, convExp

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt


class TextupdateClass(QLineEdit,edmWidget):
    displayModeList = { "default" : convDefault, "decimal":convDecimal, "hex":convHex, "engineer":convEngineer, "exp":convExp }
    V3propTable = {
        "7-0" : [ "controlPv", "displayMode", "precision", "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "colorPv", "fill", "font", "fontAlign", "lineWidth", "lineAlarm" ]
        }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.haveFocus = 0

    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self, objectDesc)
        self.setReadOnly(1)
        self.setFrame(0)
        self.setFocusPolicy(Qt.NoFocus)
        self.precision = self.objectDesc.getEfIntProperty("precision", 0)
        if self.objectDesc.getIntProperty("major") == 7:    # V3 data
            dm = self.objectDesc.getIntProperty("displayMode", 0)
            self.displayMode = [ "default", "decimal", "hex", "engineer", "exp"] [dm]
        else:
            self.displayMode = self.objectDesc.getStringProperty("displayMode", "default")

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

edmDisplay.edmClasses["TextupdateClass"] = TextupdateClass
