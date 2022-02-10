from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a set of boxes for the bit values of a PV

from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget


# Display class for bars: can be inherited by controllable widgets
#
class byteClass(QWidget,edmWidget):

    V3propTable = {
         "1-1" : [ "INDEX", "lineColor", "INDEX", "onColor", "INDEX", "offColor", 
         "controlPv", "lineWidth", "lineStyle", "direction", "numBits", "shifting" ]
         }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["controlPv"] = [ "PVname", "pv", 1 ]

    def cleanup(self):
        edmWidget.cleanup(self)
        self.lineColorInfo.cleanup()
        self.onColorInfo.cleanup()
        self.offColorInfo.cleanup()

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.noBits = object.getIntProperty("numBits", 16)
        self.shiftBits = object.getIntProperty("shifting", 0)
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
        width = self.width() // self.noBits
        height = self.height()
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height())
        li = self.lineColorInfo
        painter.setPen(li.colorRule.getColor(li.colorValue))
        for idx in range(0, self.noBits):
            painter.setBrush( self.chooseColor(idx) )
            painter.drawRect( xoffset, 0, width-1, height-1)
            xoffset = xoffset + width-1

    def redisplay(self, *kw):
        self.setVisible(self.visible)
        self.value = self.pv.value >> self.shiftBits
        self.update()

edmDisplay.edmClasses["ByteClass"] = byteClass

