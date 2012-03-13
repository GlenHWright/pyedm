# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# this widget gives a text display of a PV with over-ride of the display format.
# It may, at some point, have a pop-up window for calculator-style entry!
import pyedm.edmDisplay as edmDisplay
from PyQt4.QtGui import QPalette, QLineEdit
from PyQt4.QtCore import Qt

# from pyedm.monitoractiveXtext import activeXTextDspClass_noedit
monitoractiveXtext = __import__("monitoractiveXtext", globals(), locals(), 1)
activeXTextDspClass_noedit = monitoractiveXtext.activeXTextDspClass_noedit

class activeXTextDspClass(activeXTextDspClass_noedit):
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
        activeXTextDspClass_noedit.__init__(self, parent)

    def buildFromObject(self, object):
        activeXTextDspClass_noedit.buildFromObject(self, object)
        if object.getIntProperty("editable", 0) :
            self.setReadOnly(0)
            self.setFocusPolicy(Qt.StrongFocus)
            self.edmParent.buttonInterest.append(self)

    def findBgColor(self):
        self.bgColorInfo = self.findColor( "bgColor", palette=(QPalette.Base,),fillName="useDisplayBg", fillTest=1)


    def keyPressEvent(self, event):
        if self.DebugFlag > 0 : print "keypress event"
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

edmDisplay.edmClasses["activeXTextDspClass"] = activeXTextDspClass

