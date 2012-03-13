# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages the display of text with regular expression manipulation

import pyedm.edmDisplay as edmDisplay

from PyQt4.QtGui import QTextEdit
from PyQt4 import QtCore
# from pyedm.displaytext import activeXTextClass
displaytext = __import__("displaytext", globals(), locals(), 1)
activeXTextClass = displaytext.activeXTextClass

class activeXRegTextClass(activeXTextClass):
    V3propTable = {
        "2-1" : [ "INDEX", "fgColor", "fgAlarm", "useDisplayBg", "INDEX", "bgColor", "bgAlarm", "alarmPv",
            "visPv", "visInvert", "visMin", "visMax", "value", "font", "fontAlign", "autoSize", "ID" , "regExpr" ]
            }
    def __init__(self, parent=None):
        activeXTextClass.__init__(self, parent)

    def onUpdate(self, **kw):
        self.setText(self.controlPV.char_value)

edmDisplay.edmClasses["activeXRegTextClass"] = activeXRegTextClass

