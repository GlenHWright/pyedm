from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget for an up/down button. Left button presses cause the value
# to decrement, Right button presses cause the value to increment. This isn't a Qt Button,
# it just has a passing display relationship to one.

from . import edmPopupEntry
from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QWidget, QMenu
from PyQt5.QtGui import QPalette, QFontMetrics, QPainter
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QPoint

class updownButtonClass(QWidget, edmWidget):
    menuGroup = ["control", "up/down button"]
    edmEntityFields =  [
        edmField("controlPv", edmEdit.PV),
        edmField("savedValuePv", edmEdit.PV),
        edmField("invisible", edmEdit.Bool, defaultValue=False),
        edmField( "label", edmEdit.String),
        edmField("coarseValue", edmEdit.Real ),
        edmField("fineValue", edmEdit.Real ),
        edmField("rate", edmEdit.Real ),
        edmField("limitsFromDb", edmEdit.Bool, defaultValue=False),
        edmField("scaleMin", edmEdit.Real),
        edmField("scaleMax", edmEdit.Real)
        ]
    edmFieldList = \
     edmWidget.edmBaseFields + edmWidget.edmColorFields  + \
     edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields

    V3propTable = {
        "1-5" :  [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "controlPv", "fineValue", "coarseValue", "label", "3D", "invisible", "rate", "font", "savePv", "scaleMin", "scaleMax",
            "visPv", "visMin", "visMax", "colorPv" ]
    }
    menuLabels = [ "Save", "Restore", "Set Coarse", "Set Fine", "Set Rate", "Set Value" ]
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edmParent.buttonInterest.append(self)
        self.pvItem["savedValuePv"] = pvItemClass( "savedValueName", "savedValuePV")

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        rebuild = kw.get('rebuild', False)
        self.invisible = objectDesc.getProperty("invisible")
        self.label = self.macroExpand( objectDesc.getProperty("label"))
        self.coarseValue = objectDesc.getProperty("coarseValue")
        self.fineValue = objectDesc.getProperty("fineValue")
        self.rate = objectDesc.getProperty("rate")
        self.dbLimits = objectDesc.getProperty("limitsFromDb")
        self.scaleMin = objectDesc.getProperty("scaleMin")
        self.scaleMax = objectDesc.getProperty("scaleMax")
        self.waitRepeat = 0
        self.incr = 0.0
        if not rebuild:
            self.timerID = None
            self.timerActive = False
            self.menu = QMenu(self)
            self.actions = [ self.menu.addAction(menu, lambda arg=menu:self.onMenu(arg)) for menu in self.menuLabels ]
            self.popup = None

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.setFont(self.edmFont)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        if self.invisible:
            return
        fm = painter.fontMetrics()
        w = fm.width(self.label)
        painter.fillRect(0, 0, self.width(), self.height(), self.palette().brush(QPalette.Window) )
        painter.drawText( (self.width()-w)//2, (self.height()+fm.height())//2,self.label)
        if self.width() > 20 and self.height() > fm.height() + 10:
            painter.drawLine( 10, 15, self.width()-20, 15)

    def timerEvent(self, event):
        if self.waitRepeat == 1:
            self.killTimer(self.timerID)
            self.timerID = self.startTimer(int(1000*self.rate))
        self.setVal = self.setVal + self.incr
        self.controlPV.put(self.setVal)

    def mousePressEvent(self, event):
        pos = event.pos()
        if pos.y() < 15:    # Menu Region
            if self.timerActive == True:
                return
            self.menu.exec_(self.mapToGlobal(pos) )
            return
        if not hasattr(self,"controlPV") or self.controlPV.isValid == 0:
            if self.debug(): print("Ignoring - no", hasattr(self, "controlPV"))
            return
        if event.button() == QtCore.Qt.RightButton:
            # increase the value
            self.waitRepeat = 1
            self.setVal = self.controlPV.value + self.coarseValue
            self.incr = self.fineValue
        elif event.button() == QtCore.Qt.LeftButton:
            # decrease the value
            self.waitRepeat = 1
            self.setVal = self.controlPV.value - self.coarseValue
            self.incr = -self.fineValue
        else:
            return
        self.controlPV.put(self.setVal)
        if self.timerActive == False:
            self.timerActive = True
            self.timerID = self.startTimer(1000)

    def mouseReleaseEvent(self, event):
        if self.timerID == None:
            return
        self.killTimer(self.timerID)
        self.timerID = None
        self.timerActive = False

    def onMenu(self, arg):
        if self.debug(): print("onMenu", arg)
        activity = self.menuLabels.index(arg)
        if activity < 0:
            return
        if activity == 0:
            if hasattr(self,"savedValuePV") and self.savedValuePV.isValid:
                self.savedValuePV.put( self.controlPV.get() )
            return
        if activity == 1:
            if hasattr(self,"savedValuePV") and self.savedValuePV.isValid:
                self.controlPV.put( self.savedValuePV.get() )
            return
        self.activity = activity
        if self.popup == None:
            self.popup = edmPopupEntry.PopupNumeric( self.popupInput)
        self.popup.move( self.mapToGlobal(QPoint(0, self.height())))
        self.popup.show()
            
    def popupInput(self, text):
        val = float(text)
        if self.activity == 2:
            self.coarseValue = val
        elif self.activity == 3:
            self.fineValue = val
        elif self.activity == 4:
            self.rate = val
        elif self.activity == 5:
            if self.timerActive:
                self.setVal = val
            elif hasattr(self,"controlPV") and self.controlPV.isValid:
                self.controlPV.put(val)

edmApp.edmClasses["activeUpdownButtonClass"] = updownButtonClass
