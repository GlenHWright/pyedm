# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draws an arc.

from .edmApp import edmApp
from .edmAbstractShape import abstractShape
from .edmField import edmField
from .edmEditWidget import edmEdit

from enum import Enum
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

class activeArcClass(abstractShape):
    menuGroup = ["display", "Draw Arc"]
    fillModeEnum = Enum("fillMode", "none chord arc", start=0)
    edmEntityFields = [
            edmField("startAngle", edmEdit.Real, defaultValue=0.0),
            edmField("totalAngle", edmEdit.Real, defaultValue=180.0),
            edmField("fillMode", edmEdit.Enum, enumList=fillModeEnum, defaultValue="none")
            ]
    edmFieldList = abstractShape.edmBaseFields + abstractShape.edmShapeFields + edmEntityFields + abstractShape.edmVisFields
    V3propTable = {
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "alarmPv",
                "visPv", "visMin", "visMax", "lineWidth", "lineStyle", "startAngle", "totalAngle", "fillMode" ]
                }
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc)
        self.linewidth = objectDesc.getProperty("lineWidth")
        self.fillMode = objectDesc.getProperty("fillMode")
        edmApp.redisplay(self)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        pen = painter.pen()
        pen.setWidth(self.linewidth)
        pen.setColor( self.lineColorInfo.setColor())
        painter.setPen(pen)
        brush = painter.brush()
        if self.fillMode == self.fillModeEnum.none:
            brush.setStyle(Qt.NoBrush)
        else:
            brush.setStyle(Qt.SolidPattern)
        try:
            brush.setColor( self.fillColorInfo.setColor())
        except AttributeError:
            pass
        painter.setBrush(brush)
        offset = max(self.linewidth, 1)
        w = self.width() - offset
        h = self.height() - offset
        offset = int(offset/2)
        startAngle = self.objectDesc.getProperty("startAngle")*16
        totalAngle = self.objectDesc.getProperty("totalAngle")*16 
        if self.fillMode == self.fillModeEnum.none:
            painter.drawArc( offset, offset, w, h, startAngle, totalAngle)
        elif self.fillMode == self.fillModeEnum.chord:
            painter.drawChord( offset, offset, w, h, startAngle, totalAngle)
        elif self.fillMode == self.fillModeEnum.arc:
            painter.drawPie( offset, offset, w, h, startAngle, totalAngle)
        else:
            print(f"Unknown fill mode {self.fillMode}")

edmApp.edmClasses["activeArcClass"] = activeArcClass

