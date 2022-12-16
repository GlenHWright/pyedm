# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a message box (continuous log of displayed values)
#
# support a scrollable area message box.
#

from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget,  QPushButton, QTextEdit, QVBoxLayout

class messageBoxClass(QWidget,edmWidget):
    menuGroup = ["monitor", "Message Box"]
    edmEntityFields = [
            edmField("fill", edmEdit.Bool, defaultValue=False),
            edmField("indicatorPv", edmEdit.PV)
            ]
    edmFieldList = \
     edmWidget.edmBaseFields + edmWidget.edmColorFields  + \
        edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields
    V3propTable = {
        "2-2" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "2ndBgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "indicatorPv", "font", "bufferSize", "fileSize", "flushTimerValue", "logFileName", "ReadOnly" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = pvItemClass( "PVname", "pv", redisplay=True)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject( objectDesc, **kw)
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
        return getattr(self, "pv", None)

    def redisplay(self, **kw):
        self.checkVisible()
        try:
            self.line.append(self.pv.char_value)
        except AttributeError as exc:
            self.line.append(f"EDM Error {exc}")

    def clear(self):
        self.line.clear()

edmApp.edmClasses["activeMessageBoxClass"] = messageBoxClass
