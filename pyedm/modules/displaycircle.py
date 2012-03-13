# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draw an ellipse

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmAbstractShape import abstractShape
from pyedm.edmEditWidget import edmEdit

from PyQt4.QtGui import QFrame, QPainter

class activeCircleClass(abstractShape):
    V3propTable = {
        "2-0" : [ "lineColor", "lineAlarm", "fill", "fillColor", "fillAlarm", "controlPv", "visPv", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle" ],
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "controlPv", "visPv", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle" ]
            }

    edmEditList = [
        edmEdit.LineThick(),
        edmEdit.Enum(label="Line Style", object="lineStyle", enumList=[ "Solid", "Dash" ] ),
        edmEdit.FgColor("Line Color", "lineColorInfo.getName"),
        edmEdit.CheckButton("Alarm Sensitive", "lineColorInfo.alarmSensitive"),
        edmEdit.CheckButton("Fill", "fill"),
        edmEdit.BgColor("Fill Color", "fillColorInfo.getName"),
        edmEdit.CheckButton("Alarm Sensitive", "fillColorInfo.alarmSensitive"),
        edmEdit.StringPV( "Color PV", "alarmPV.getPVname", None),
    ] + edmEdit.visibleList

    def __init__(self, parent=None):
        abstractShape.__init__(self,parent)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        pen = painter.pen()
        pen.setWidth(self.linewidth)
        pen.setColor( self.lineColorInfo.setColor() )
        painter.setPen(pen)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        if self.fillColorInfo != None:
            painter.setBrush( self.fillColorInfo.setColor() )
        painter.drawEllipse( 0, 0, self.width()-2, self.height()-2 )
        
edmDisplay.edmClasses["activeCircleClass"] = activeCircleClass

