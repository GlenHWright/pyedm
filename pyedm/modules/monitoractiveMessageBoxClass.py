# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a message box (continuous log of displayed values)
#
# support a scrollable area message box.
#

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtCore import Qt#, SIGNAL
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget,  QPushButton, QTextEdit, QVBoxLayout

class messageBoxClass(QWidget,edmWidget):
    V3propTable = {
        "2-2" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "2ndBgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "indicatorPv", "font", "bufferSize", "fileSize", "flushTimerValue", "logFileName", "ReadOnly" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = [ "PVname", "pv", 1, None, None ]

    def buildFromObject(self, object):
        self.object = object
        edmWidget.buildFromObject(self, object)
        self.clearButton = QPushButton("Clear", self)
        self.line = QTextEdit(self)
        #self.clearButton.connect(self.clearButton, SIGNAL("clicked()"), self.clear)
        self.clearButton.clicked.connect(self.clear)
        self.line.setReadOnly(1)
        self.line.setGeometry( 0, self.clearButton.y() + self.clearButton.height()
            +12, self.width()-4, self.height() - self.clearButton.height() -
            self.clearButton.y() - 4)

    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,),fillName="fill", fillTest=0)

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,) )

    # use the control PV for alarm, rather than color PV
    def getAlarmPv(self, colorName=None, alarmName=None):
        return self.pv

    def redisplay(self, **kw):
        self.checkVisible()
        self.line.append(self.pv.char_value)

    def clear(self):
        self.line.clear()

edmDisplay.edmClasses["activeMessageBoxClass"] = messageBoxClass
