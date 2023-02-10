# Copyright 2011-2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages the display of text with regular expression manipulation

from . import edmImport
from .edmApp import edmApp
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QTextEdit
from PyQt5 import QtCore

displaytext = edmImport("displaytext")
activeXTextClass = displaytext.activeXTextClass

class activeXRegTextClass(activeXTextClass):
    menuGroup = [ "display", "active Text regex" ]
    edmEntityFields = [
        edmField("regExpr", edmEdit.String)
            ]
    edmFieldList = \
     activeXTextClass.edmBaseFields + activeXTextClass.edmColorFields  + \
     activeXTextClass.edmEntityFields + \
     edmEntityFields + activeXTextClass.edmFontFields + activeXTextClass.edmVisFields
    V3propTable = {
        "2-1" : [ "INDEX", "fgColor", "fgAlarm", "useDisplayBg", "INDEX", "bgColor", "bgAlarm", "alarmPv",
            "visPv", "visInvert", "visMin", "visMax", "value", "font", "fontAlign", "autoSize", "ID" , "regExpr" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)

    def onUpdate(self, **kw):
        self.setText(self.controlPV.char_value)

edmApp.edmClasses["activeXRegTextClass"] = activeXRegTextClass

