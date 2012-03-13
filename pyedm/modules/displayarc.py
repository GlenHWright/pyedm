# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draws an arc.

import pyedm.edmDisplay as edmDisplay
from pyedm.edmAbstractShape import abstractShape
from edmEditWidget import edmEdit

from PyQt4.QtGui import QFrame, QPainter
from PyQt4 import QtCore

class activeArcClass(abstractShape):
    V3propTable = {
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "alarmPv",
                "visPv", "visMin", "visMax", "lineWidth", "lineStyle", "startAngle", "totalAngle", "fillMode" ]
                }

    edmEditList = [
        edmEdit.Int("Start Angle", "startAngle", None),
        edmEdit.Int("Total Angle", "totalAngle", None),
        edmEdit.LineThick(),
        edmEdit.Enum(label="Line Style", object="lineStyle", enumList=[  "Solid", "Dash"] ),
        edmEdit.FgColor("Line Color", "fgColorInfo.getName"),
        edmEdit.CheckButton("Alarm Sensitive", "fgColorInfo.alarmSensitive"),
        edmEdit.CheckButton("Fill", "fill"),
        edmEdit.Enum(label="Fill Mode", object="mode", enumList=[ "Chord", "Pie" ] ),
        edmEdit.BgColor("Fill Color", "bgColorInfo.getName"),
        edmEdit.CheckButton("Alarm Sensitive", "bgColorInfo.alarmSensitive"),
        edmEdit.StringPV("Color PV", "colorPV.getPVname")
    ] + edmEdit.visibleList

    def __init__(self, parent=None):
        abstractShape.__init__(self,parent)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        painter.setPen(self.lineColorInfo.setColor() )
        painter.drawArc( 0, 0, self.width()-1, self.height()-1,
        self.object.getDoubleProperty("startAngle", 0.0)*16,
        self.object.getDoubleProperty("totalAngle", 180.0)*16 )

edmDisplay.edmClasses["activeArcClass"] = activeArcClass

