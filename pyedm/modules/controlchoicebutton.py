from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget containing one button per state for a PV
from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmApp import redisplay
from pyedm.edmWindowWidget import mousePressEvent, mouseReleaseEvent

from PyQt5.QtWidgets import QWidget, QLayout, QVBoxLayout, QHBoxLayout, QButtonGroup, QPushButton
from PyQt5.QtGui import QPalette
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot

class activeChoiceButtonClass(QWidget,edmWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.ready = 0
        self.pvItem["controlPv"] = [ "controlName", "controlPV", 1, None, None , onConnect, (self, ) ]

    def cleanup(self):
        edmWidget.cleanup(self)
        self.selectColorInfo.cleanup()

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.orientation = object.getStringProperty("orientation", "vertical")
        self.layout = QVBoxLayout() if self.orientation == "vertical" else QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setSpacing(0)
        #self.layout.setMargin(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.group = QButtonGroup(self)
        self.lastSelect = -2
        self.group.buttonClicked.connect(self.gotNewValue)

        self.selectColorInfo = self.findColor("selectColor",(QPalette.Button,) )
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)
        # Race conditions: if using a preemptive callback environment, the test and set of 'ready' can have
        # the onConnect callback occur in the middle, meaning the menu never gets set. Need to reevaluate
        # the use of 'ready' and the potential for fully correct implementation.
        if self.ready < 0:
            self.rebuildList()
        self.ready = 1

    # override the palette and the display request.
    def findFgColor(self):
        self.fgColorInfo = self.findColor( "fgColor", (QPalette.ButtonText,), "FGalarm", "fgAlarm")

    # override the palette and the display request.
    def findBgColor(self):
        self.bgColorInfo = self.findColor( "bgColor", (QPalette.Button,), "FGalarm", "fgAlarm")

    @pyqtSlot()
    def gotNewValue(self):
        button = self.group.checkedId()
        if self.controlPV == None or getattr(self, 'menu', None) == None:
            return
        self.controlPV.put( button )
        self.redisplay()

    def redisplay(self):
        # called when the control PV changes
        # find the button that corresponds to the index, and mark it
        self.checkVisible()
        if self.ready < 0:
            self.rebuildList()
        bid = int(self.controlPV.value)
        bt = self.group.button(bid)
        if bt != None:
            bt.setChecked(True)
        self.setButtonColors( bid)
        self.update()

    def setButtonColors(self, checkVal):
        if hasattr(self, 'menu') == False or self.menu == None:
            return
        checkVal = int(checkVal)
        if checkVal == self.lastSelect:
            return
        self.lastSelect = checkVal

        for idx in range(0,len( self.menu)):
            rb = self.group.button(idx)
            colorInfo = self.selectColorInfo if checkVal == idx else self.bgColorInfo
            if colorInfo.colorRule != None:
                col = colorInfo.colorRule.getColor(colorInfo.colorValue)
                pal = rb.palette()
                for role in colorInfo.colorPalette:
                    pal.setColor( QPalette.Active, role, col)
                    pal.setColor( QPalette.Inactive, role, col)
                    pal.setColor( QPalette.Disabled, role, col)
                fgcol = self.fgColorInfo.colorRule.getColor(self.fgColorInfo.colorValue)
                for role in self.fgColorInfo.colorPalette:
                    pal.setColor( QPalette.Active, role, fgcol)
                    pal.setColor( QPalette.Inactive, role, fgcol)
                    pal.setColor( QPalette.Disabled, role, fgcol)
                rb.setPalette(pal)

    def rebuildList(self):
        idx = 0
        width = self.width()
        height = self.height()
        num = len(self.menu)
        if self.orientation == "horizontal":
            width = width// num
            xIncr = width
            yIncr = 0
        else:
            height = height// num
            xIncr = 0
            yIncr = height

        x = 0
        y = 0
        for rbName in self.menu:
            rb = self.group.button(idx)
            if rb == None:
                rb = QPushButton("<?>", self)
                rb.setFixedSize(width, height)
                rb.setCheckable(True)
                rb.setAutoExclusive(True)
                self.layout.addWidget(rb)
                self.group.addButton(rb, idx)
                self.buttonInterest.append(rb)
            idx = idx + 1
            rb.setText(rbName)
        self.setButtonColors(-1)
        self.update()

    def mousePressEvent(self, event):
        mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event)

def onConnect(pv, arg, **kw):
    who = arg[0]
    who.menu = pv.getEnumStrings()
    if who.menu != None and len(who.menu) > 0:
        who.ready = -1
        redisplay(who)

edmDisplay.edmClasses["activeChoiceButtonClass"] = activeChoiceButtonClass
