from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages the displaying of a rectangle.
# Where This Differs From EDM:
#  Because we're in a widget the same dimensions as the rectangle,
# anything outside the widget is clipped. This happens when a line drawn
# rectangle needs to draw outside the box - QT defines the rectangle
# width and height as the center of the box, and the line goes on the outside
# of this - mostly.

from past.utils import old_div
import pyedm.edmDisplay as edmDisplay
from pyedm.edmAbstractShape import abstractShape
from pyedm.edmEditWidget import edmEdit

from PyQt4.QtGui import QFrame, QPainter

class activeRectangleClass(abstractShape):
    V3propTable = {
        "2-0" : [ "lineColor", "lineAlarm", "fill", "fillColor", "fillAlarm",
                    "alarmPV", "visPV", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle", "invisible" ],
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm",
                    "alarmPV", "visPV", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle", "invisible" ]
                    }

    edmEditList = [
        edmEdit.LineThick(),
        edmEdit.Enum(label="Line Style", object="lineStyle", enumList= [ "Solid", "Dash" ] ),
        edmEdit.FgColor("Line Color", "lineColor"),
        edmEdit.CheckButton("Alarm Sensitive", "fgAlarm"),
        edmEdit.CheckButton("Fill", "fill"),
        edmEdit.BgColor("Fill Color", "fillColor"),
        edmEdit.CheckButton("Alarm Sensitive", "bgAlarm"),
        edmEdit.CheckButton("Invisible", "invisible"),
        edmEdit.StringPV("Color PV", "colorPv")
    ] + edmEdit.visibleList

    def __init__(self, parent=None):
        abstractShape.__init__(self,parent)

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
        if self.fillColorInfo != None:
            painter.setBrush( self.fillColorInfo.setColor() )
        else:
            x,y = x+int(old_div(self.linewidth,2)), y+int(old_div(self.linewidth,2))
            w,h = w-self.linewidth, h-self.linewidth
            
        painter.drawRect( x, y, w, h)
        
edmDisplay.edmClasses["activeRectangleClass"] = activeRectangleClass

