from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages the displaying of a rectangle.
# Where This Differs From EDM:
#  Because we're in a widget the same dimensions as the rectangle,
# anything outside the widget is clipped. This happens when a line drawn
# rectangle needs to draw outside the box - QT defines the rectangle
# width and height as the center of the box, and the line goes on the outside
# of this - mostly.

import pyedm.edmDisplay as edmDisplay
from pyedm.edmAbstractShape import abstractShape

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

class activeRectangleClass(abstractShape):
    V3propTable = {
        "2-0" : [ "lineColor", "lineAlarm", "fill", "fillColor", "fillAlarm",
                    "alarmPV", "visPV", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle", "invisible" ],
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm",
                    "alarmPV", "visPV", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle", "invisible" ]
                    }
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc):
        abstractShape.buildFromObject(self, objectDesc)
        if self.fillColorInfo == None:
            w2 = self.linewidth
            w = int(self.linewidth//2)
            self.setGeometry(self.x()-w, self.y()-w,
                self.width()+w2, self.height()+w2)
            
    def paintEvent(self, event=None):
        painter = QPainter(self)
        w,h = self.width(), self.height()
        x,y = 0,0
        if event == None:
            painter.eraseRect(0, 0, w, h)
        pen = painter.pen()
        pen.setColor( self.lineColorInfo.setColor())
        pen.setWidth(self.linewidth)
        painter.setPen(pen)
        if self.DebugFlag > 0 : print("paintRect ", x, y, w, h, self.linewidth, self.fillColorInfo != None)
        if self.fillColorInfo != None:
            painter.setBrush( self.fillColorInfo.setColor() )
            painter.drawRect( x, y, w, h)
        else:
            #w,h = w-self.linewidth, h-self.linewidth
            lw = self.linewidth
            hlw = int(lw//2)
            painter.drawRect( x+hlw, y+hlw, w-lw, h-lw)
        
edmDisplay.edmClasses["activeRectangleClass"] = activeRectangleClass

