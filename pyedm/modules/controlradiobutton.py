# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This widget displays a radio button for each valid value of a PV.
from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmWindowWidget import mousePressEvent, mouseReleaseEvent, mouseMoveEvent
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QButtonGroup, QRadioButton
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot

class activeRadioButtonClass(QWidget,edmWidget):
    menuGroup = [ "control", "Radio Button" ]
    edmEntityFields = [
            edmField("controlPv", edmEdit.PV),
            edmField("selectColor", edmEdit.Color)
            ]
    edmFieldList =  \
     edmWidget.edmBaseFields + edmWidget.edmColorFields  + edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields
    V3propTable = {
        "1-2" : [ "INDEX", "fgColor", "fgAlarm", "bgColor", "bgAlarm", "INDEX", "buttonColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
        "controlPv", "font", "selectColor"
        ]
        }
    def __init__(self,parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.group = QButtonGroup(self)
        self.pvItem["controlPv"] = pvItemClass( "controlName", "controlPV", redisplay=True, conCallback=self.onConnect )

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.group.buttonClicked.connect(self.gotNewValue)

        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    @pyqtSlot()
    def gotNewValue(self):
        if self.controlPV == None:
            return
        self.controlPV.put( self.group.checkedId() )

    def redisplay(self):
        # called when the control PV changes
        self.checkVisible()
        # find the button that corresponds to the index, and mark it
        bt = self.group.button(int(self.controlPV.value) )
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

    def onConnect(self, pv, arg, **kw):
        ''' called when displayPV connects or reconnects
        '''
        self.menu = pv.getEnumStrings()
        if self.menu != None:
            self.rebuildList()

    def mousePressEvent(self, event):
        mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        mouseMoveEvent(self, event)

edmApp.edmClasses["activeRadioButtonClass"] = activeRadioButtonClass
