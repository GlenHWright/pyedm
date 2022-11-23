# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module draw an ellipse

from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmAbstractShape import abstractShape

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

class activeCircleClass(abstractShape):
    menuGroup = ["display", "Draw Circle"]
    edmFieldList = abstractShape.edmBaseFields + abstractShape.edmShapeFields + abstractShape.edmVisFields

    V3propTable = {
        "2-0" : [ "lineColor", "lineAlarm", "fill", "fillColor", "fillAlarm", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle" ],
        "2-1" : [ "INDEX", "lineColor", "lineAlarm", "fill", "INDEX", "fillColor", "fillAlarm", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "lineWidth", "lineStyle" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject( objectDesc, **kw)
        self.linewidth = objectDesc.getProperty("lineWidth")
        w2 = self.linewidth
        w = int(self.linewidth//2)

        self.setGeometry(self.x(), self.y(),
            self.width()+w2, self.height()+w2)

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
        lw2 = self.linewidth
        lw = int(lw2//2)
        painter.drawEllipse( lw, lw, self.width()-lw2, self.height()-lw2 )
        
edmApp.edmClasses["activeCircleClass"] = activeCircleClass

