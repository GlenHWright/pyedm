# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# this widget gives a text display of a PV with over-ride of the display format.
# It may, at some point, have a pop-up window for calculator-style entry!
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt

from . import edmImport
from .edmApp import edmApp
from .edmField import edmField
from .edmEditWidget import edmEdit

monitoractiveXtext = edmImport("monitoractiveXtext")
activeXTextDspClass_noedit = monitoractiveXtext.activeXTextDspClass_noedit

class activeXTextDspClass(activeXTextDspClass_noedit):
    menuGroup = ["control", "Active Text Edit" ]

    edmEntityFields = [
            edmField("editable", edmEdit.Bool, defaultValue=False)
        ]
    edmFieldList = \
        activeXTextDspClass_noedit.edmBaseFields + activeXTextDspClass_noedit.edmColorFields  + \
                activeXTextDspClass_noedit.edmEntityFields + \
                edmEntityFields + activeXTextDspClass_noedit.edmFontFields + activeXTextDspClass_noedit.edmVisFields

    V3propTable = {
        "2-4" : [ "controlPv", "font", "useDisplayBg", "fontAlign", "fgColor", "bgColor", "formatType", "fgAlarm", "editable", "autoHeight",
            "isWidget", "limitsFromDb", "precision", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
            "svalPv", "bufSvalColor", "nullDetectMode", "fgPv", "smartRefresh", "useKp", "changeValOnLoseFocus", "fastUpdate", "isDate",
            "isFile", "defDir", "pattern" ],
        "2-5" : [ "controlPv", "font", "useDisplayBg", "fontAlign", "fgColor", "bgColor", "formatType", "fgAlarm", "editable", "autoHeight",
            "isWidget", "limitsFromDb", "precision", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
            "svalPv", "bufSvalColor", "nullDetectMode", "fgPv", "smartRefresh", "useKp", "changeValOnLoseFocus", "fastUpdate", "isDate",
            "isFile", "defDir", "pattern", "objType" ]
            }

    def __init__(self, parent):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject( objectDesc, **kw)
        if objectDesc.getProperty("editable") :
            self.setReadOnly(0)
            self.setFocusPolicy(Qt.StrongFocus)
            self.edmParent.buttonInterest.append(self)

    def findBgColor(self):
        self.bgColorInfo = self.findColor( "bgColor", palette=(QPalette.Base,),fillName="useDisplayBg", fillTest=1)


    def keyPressEvent(self, event):
        self.debug(mesg="keypress event")
        if event.text() == "\n" or event.text() == "\r":
            value = self.text()
            self.controlPV.put(value)
            self.haveFocus = 0
            # self.controlPV.char_value = value
            event.accept()
            self.redisplay()
            return

        QLineEdit.keyPressEvent(self, event)
        self.haveFocus = 1

edmApp.edmClasses["activeXTextDspClass"] = activeXTextDspClass

