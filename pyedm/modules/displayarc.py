# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draws an arc.

from .edmApp import edmApp
from .edmAbstractShape import abstractShape
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter
from PyQt5 import QtCore

class activeArcClass(abstractShape):
    menuGroup = ["display", "Draw Arc"]
    edmEntityFields = [
            edmField("startAngle", edmEdit.Real, 0.0),
            edmField("totalAngle", edmEdit.Real, 180.0)
            ]
    edmFieldList = abstractShape.edmBaseFields + abstractShape.edmShapeFields + edmEntityFields + abstractShape.edmVisFields
    V3propTable = {
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "alarmPv",
                "visPv", "visMin", "visMax", "lineWidth", "lineStyle", "startAngle", "totalAngle", "fillMode" ]
                }
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc):
        super().buildFromObject(objectDesc)
        self.linewidth = objectDesc.getProperty("lineWidth", 1)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        painter.setPen(self.lineColorInfo.setColor() )
        painter.drawArc( 0, 0, self.width()-1, self.height()-1,
        self.objectDesc.getProperty("startAngle")*16,
        self.objectDesc.getProperty("totalAngle")*16 )

edmApp.edmClasses["activeArcClass"] = activeArcClass

