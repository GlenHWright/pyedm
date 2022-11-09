# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a line display class

from math import acos, sin, cos, pi as Pi
from enum import Enum
from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmAbstractShape import abstractShape
from .edmEditWidget import edmEditInt, edmEditString, edmEditEnum, edmEditBool
from .edmField import edmField

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPolygonF, QPolygon
from PyQt5.QtCore import QLineF, QLine, QPointF, QPoint, Qt

class activeLineClass(abstractShape):
    menuGroup = [ "display", "Line"]
    arrowEnum = Enum("arrow", "none from to both", start=0)
    edmEntityFields = [
            edmField( "numPoints", edmEditInt, 0),
            edmField( "xPoints", edmEditInt, array=True, defaultValue=0),
            edmField( "yPoints", edmEditInt, array=True, defaultValue=0),
            edmField( "closePolygon", edmEditBool, defaultValue=False),
            edmField( "arrows", edmEditEnum, defaultValue=0, enumList=arrowEnum)
            ]
    edmFieldList = abstractShape.edmBaseFields + abstractShape.edmShapeFields + edmEntityFields + abstractShape.edmVisFields

    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.linewidth = objectDesc.getProperty("lineWidth")

    def paintEvent(self, event=None):
        if self.npoints <= 1:
            return
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        pen = painter.pen()
        pen.setColor( self.lineColorInfo.setColor() )
        pen.setWidth(self.linewidth)
        if self.lineStyle == "dash":
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        if self.closePolygon:
            if self.fillColorInfo != None:
                brush = painter.brush()
                brush.setColor(self.fillColorInfo.setColor() )
                brush.setStyle( Qt.SolidPattern)
                painter.setBrush(brush)
            painter.drawPolygon( QPolygon(self.points) )
        else:
            painter.drawPolyline(QPolygon(self.points) )
        if self.arrows != "none" and self.lineStyle != "solid":
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
        if self.arrows == "from" or self.arrows == "both":
            self.drawArrow(painter, self.points[1], self.points[0])
        if self.arrows == "to" or self.arrows == "both":
            self.drawArrow(painter, self.points[self.npoints-2], self.points[self.npoints-1])
        painter.end()
        
    def drawArrow(self, painter, fromPt, toPt):
        line = QLineF(QPointF(fromPt), QPointF(toPt) )
        destp = line.p2()
        if line.length() <= 1:
            return
        angle = acos(line.dx()/ line.length() )
        if line.dy() >= 0:
            angle = Pi*2 - angle

        brush = painter.brush()
        brush.setColor(self.lineColorInfo.setColor() )
        brush.setStyle( Qt.SolidPattern)
        painter.setBrush(brush)
        p0 = destp + QPointF( sin(angle-self.arrowAngle) * self.arrowSize, cos(angle-self.arrowAngle) * self.arrowSize)
        p1 = destp + QPointF( sin(angle-Pi+self.arrowAngle) * self.arrowSize, cos(angle-Pi+self.arrowAngle) * self.arrowSize)
        painter.drawPolygon( QPolygonF( [destp, p0, p1]))


    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.myx = objectDesc.getProperty("x")
        self.myy = objectDesc.getProperty("y")
        self.npoints = self.objectDesc.getProperty("numPoints",0)
        self.closePolygon = self.objectDesc.getProperty("closePolygon",0)
        self.lineStyle = self.objectDesc.getProperty("lineStyle", "solid")
        self.xpoints = self.objectDesc.getProperty("xPoints", arrayCount=self.npoints,defValue=0)
        self.ypoints = self.objectDesc.getProperty("yPoints", arrayCount=self.npoints,defValue=0)
        self.arrows = self.objectDesc.getProperty("arrows", "none")
        self.arrowSize = 15
        self.arrowAngle = Pi/2.5
        # translate points to 'QT' space
        adj = self.arrowSize//2
        self.points = [QPoint(x-self.myx+adj,y-self.myy+adj) for x,y in zip(self.xpoints,self.ypoints)]
        geom = self.geometry()
        geom.translate(-adj, -adj)
        geom.setWidth( geom.width() + adj*2)
        geom.setHeight( geom.height() + adj*2)
        self.setGeometry(geom)

    @classmethod
    def setV3PropertyList(classRef, values, tags):
        for name in [ "x", "y", "w", "h", "numPoints" ]:
            tags[name] = values.pop(0)
        npoints = int( tags['numPoints'] )
        xpoints = []
        ypoints = []
        for idx in range(npoints):
            xyv = values.pop(0).split(' ')
            xpoints.append(xyv[0])
            ypoints.append(xyv[1])
        tags['xPoints'] = xpoints
        tags['yPoints'] = ypoints
        for name in [ "lineColor", "lineAlarm", "fillflag", "fillColor", "fillAlarm", "lineWidth", "lineStyle", "alarmPv", "visPv", "visInvert", 'visMin', 'visMax', "closePolygon", "arrows" ]:
            if values[0] == "index" and (name == "lineColor" or name  == "fillColor" ) : values.pop(0)
            tags[name] = values.pop(0)


edmApp.edmClasses["activeLineClass"] = activeLineClass

