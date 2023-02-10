# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a set of boxes for the bit values of a PV

from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget

# Display class for bars: can be inherited by controllable widgets
#
class byteClass(QWidget,edmWidget):
    menuGroup = [ "monitor", "Byte" ]

    edmEntityFields = [
        edmField("controlPv", edmEdit.PV),
        edmField("numBits", edmEdit.Int, defaultValue=16),
        edmField("shifting", edmEdit.Int, defaultValue=0),
        edmField("lineColor", edmEdit.Color),
        edmField("onColor", edmEdit.Color),
        edmField("offColor", edmEdit.Color)
            ]
    edmEditFields = \
     edmWidget.edmBaseFields + edmWidget.edmColorFields  + \
     edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields
    V3propTable = {
         "1-1" : [ "INDEX", "lineColor", "INDEX", "onColor", "INDEX", "offColor", 
         "controlPv", "lineWidth", "lineStyle", "direction", "numBits", "shifting" ]
         }
    def __init__(self, parent=None):
        super().__init__(parent)

    def edmCleanup(self):
        super().edmCleanup()
        self.lineColorInfo.edmCleanup()
        self.onColorInfo.edmCleanup()
        self.offColorInfo.edmCleanup()

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.noBits = objectDesc.getProperty("numBits")
        self.shiftBits = objectDesc.getProperty("shifting")
        self.lineColorInfo = self.findColor("lineColor", ())
        self.value = 0

    def findFgColor(self):
        self.onColorInfo = self.findColor( "onColor", palette=() )

    def findBgColor(self):
        self.offColorInfo = self.findColor( "offColor", palette=() )

    def chooseColor(self, bitno):
        if self.value & ( 1 << (self.noBits-bitno-1)):
            ci = self.onColorInfo
        else:
            ci = self.offColorInfo
        return ci.colorRule.getColor(ci.colorValue)

    def paintEvent(self, event=None):
        if self.noBits <= 0:
            return
        xoffset = 0
        yoffset = 0
        if self.width() > self.height():
            width = self.width() / self.noBits
            height = self.height()
            yincr = 0
            xincr = width
        else:
            width = self.width()
            height = self.height() / self.noBits
            yincr = height
            xincr = 0
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height())
        li = self.lineColorInfo
        painter.setPen(li.colorRule.getColor(li.colorValue))
        for idx in range(0, self.noBits):
            painter.setBrush( self.chooseColor(idx) )
            w = int(xoffset+width) - int(xoffset)
            h = int(yoffset+height) - int(yoffset)
            painter.drawRect( xoffset, yoffset, w-1, h-1)
            xoffset += xincr
            yoffset += yincr

    def redisplay(self, *kw):
        self.setVisible(self.visible)
        self.value = int(self.controlPV.value) >> self.shiftBits
        self.update()

edmApp.edmClasses["ByteClass"] = byteClass

