# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draws an arc.

import pyedm.edmDisplay as edmDisplay
from pyedm.edmAbstractShape import abstractShape

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter
from PyQt5 import QtCore

class activeArcClass(abstractShape):
    V3propTable = {
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "alarmPv",
                "visPv", "visMin", "visMax", "lineWidth", "lineStyle", "startAngle", "totalAngle", "fillMode" ]
                }
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        painter.setPen(self.lineColorInfo.setColor() )
        painter.drawArc( 0, 0, self.width()-1, self.height()-1,
        self.object.getDoubleProperty("startAngle", 0.0)*16,
        self.object.getDoubleProperty("totalAngle", 180.0)*16 )

edmDisplay.edmClasses["activeArcClass"] = activeArcClass

