# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This widget displays a radio button for each valid value of a PV.
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmWindowWidget import mousePressEvent, mouseReleaseEvent

from PyQt4.QtGui import QWidget, QVBoxLayout, QButtonGroup, QRadioButton
from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

class activeRadioButtonClass(QWidget,edmWidget):
    V3propTable = {
        "1-2" : [ "INDEX", "fgColor", "fgAlarm", "bgColor", "bgAlarm", "INDEX", "buttonColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "font", "selectColor"
        ]
        }
    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        edmWidget.__init__(self,parent)
        self.layout = QVBoxLayout()
        self.group = QButtonGroup(self)
        self.pvItem["controlPv"] = [ "controlName", "controlPV", 1, None, None, onConnect, (self, "controlPv") ]

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.group.connect( self.group, SIGNAL("buttonClicked(int)"),
        self.gotNewValue)
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def gotNewValue(self, value):
        if self.controlPV == None:
            return
        self.controlPV.put( value)

    def redisplay(self):
        # called when the control PV changes
        self.checkVisible()
        # find the button that corresponds to the index, and mark it
        bt = self.group.button(self.controlPV.value)
        if bt != None:
            bt.setChecked(True)

    def rebuildList(self):
        idx = 0
        for rbName in self.menu:
            rb = self.group.button(idx)
            if rb == None:
                rb = QRadioButton("<?>", self)
                self.layout.addWidget(rb)
                self.group.addButton(rb, idx)
                self.buttonInterest.append(rb)
            idx = idx + 1
            rb.setText(rbName)
        self.setLayout(self.layout)
        self.update()

    def mousePressEvent(self, event):
        mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event)

def onConnect(pv, arg):
    who, tag = arg[0], arg[1]
    who.menu = pv.getEnumStrings()
    if who.menu != None:
        who.rebuildList()

edmDisplay.edmClasses["activeRadioButtonClass"] = activeRadioButtonClass
