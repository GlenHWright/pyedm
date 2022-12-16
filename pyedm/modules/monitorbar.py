from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a bar indicating a PV value

from enum import Enum

from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmAbstractShape import abstractShape
from .edmEditWidget import edmEdit
from .edmField import edmField

import PyQt5.QtCore as QtCore
from PyQt5.QtGui import QPalette, QPainter, QFontMetrics
from PyQt5.QtWidgets import QFrame

# Display class for bars: can be inherited by controllable widgets
# unfortunate that the edm bar differs from what Qt offers. Make the activeBarClass
# an abstractShape
#
class activeBarClass(abstractShape,edmWidget):
    menuGroup = [ "monitor", "Bar" ]
    labelTypeEnum = Enum("labelType", "pvName literal", start=0)
    scaleFormatEnum = Enum("scaleFormat", "FFloat GFloat Exponential", start=0)
    orientationEnum = Enum("orientation", "vertical horizontal", start=0)
    edmEntityFields = [
        edmField("indicatorPv", edmEdit.PV, None),
        edmField("indicatorAlarm", edmEdit.Bool, False),
        edmField("indicatorColor", edmEdit.Color, 0),
        edmField("limitsFromDb", edmEdit.Bool, False),
        edmField("orientation", edmEdit.Enum, defaultValue="horizontal", enumList=orientationEnum),
        edmField("min", edmEdit.Real, None),
        edmField("max", edmEdit.Real, None),
        edmField("origin", edmEdit.Real, None),
        edmField("label", edmEdit.String, None),
        edmField("labelType", edmEdit.Enum, enumList=labelTypeEnum, defaultValue="literal"),
        edmField("showScale", edmEdit.Bool, False),
        edmField("scaleFormat", edmEdit.Enum, enumList=scaleFormatEnum, defaultValue="FFloat"),
        edmField("precision", edmEdit.Int, 0),
        edmField("labelTicks", edmEdit.Int, 10),
        edmField("majorTicks", edmEdit.Int, 2),
        edmField("minorTicks", edmEdit.Int, 2),
        edmField("border", edmEdit.Bool, False)
        ]
    edmFieldList = abstractShape.edmBaseFields + abstractShape.edmColorFields + \
            edmEntityFields + \
            abstractShape.edmShapeFields + abstractShape.edmFontFields

    V3propTable = {
        "2-1" : [ "indicatorColor", "indicatorAlarm", "fgColor", "fgAlarm", "bgColor", "readPv", "indicatorPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ],
        "2-2" : [ "INDEX", "indicatorColor", "indicatorAlarm", "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "readPv", "indicatorPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = pvItemClass( "indicatorName", "indicatorPV", redisplay=True)
        self.minField, self.maxField = "min", "max"

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.orientation = self.objectDesc.getProperty("orientation")
        self.displayLimits = self.objectDesc.getProperty("limitsFromDb", 0)
        self.objMin = self.objectDesc.getProperty(self.minField, None)
        self.objMax = self.objectDesc.getProperty(self.maxField, None)
        self.origin = self.objectDesc.getProperty("origin")
        self.label = self.objectDesc.getProperty("label", None)
        self.labelType = self.objectDesc.getProperty("labelType")
        self.showScale = self.objectDesc.getProperty("showScale", 0)
        self.scaleFormat = self.objectDesc.getProperty("scaleFormat", "FFloat")
        self.precision = self.objectDesc.getProperty("precision", 0)
        self.labelTicks = self.objectDesc.getProperty("labelTicks", 10)
        self.majorTicks = self.objectDesc.getProperty("majorTicks", 2)
        self.minorTicks = self.objectDesc.getProperty("minorTicks", 2)
        self.border = self.objectDesc.getProperty("border")
        if self.border:
            self.setFrameShape(QFrame.Box)
            self.setAutoFillBackground(True)

        if self.objMin != None and self.objMax != None:
            self.fixRange(self.objMin, self.objMax)
        else:
            self.fixRange(0.0, 100.0)

        if hasattr(self, "indicatorPV") and self.displayLimits:
            self.indicatorPV.add_callback(self.setDisplayLimits, None)

        if self.showScale:
            if self.scaleFormat == "GFloat":
                self.fmt = f"%.{self.precision}g"
            elif self.scaleFormat == "Exponential":
                self.fmt = f"%.{self.precision}e"
            else:
                self.fmt = f"%.{self.precision}f"

    def findFgColor(self):
        edmWidget.findFgColor( self)
        self.indicatorColorInfo = self.findColor( "indicatorColor", (), alarmPV="indicatorPV", alarmName="indicatorAlarm")

    def findBgColor(self):
        edmWidget.findBgColor( self, bgcolor="bgColor", palette=(QPalette.Base,) )

    def setDisplayLimits(self, *kw, **args):
        pv = args["pv"]
        limits = pv.getLimits()
        if limits[0] < limits[1]:
            self.fixRange( limits[0], limits[1] )

    def fixRange(self, minval, maxval):
        self.rmin = minval
        self.rmax = maxval

    def redisplay(self, *kw):
        self.checkVisible()
        self.update()

    def paintEvent(self, event=None):
        painter = QPainter(self)
        w,h = self.width(), self.height()
        x,y = 0,0
        if event == None:
            painter.eraseRect(0, 0, w, h)

        painter.setBrush(self.bgColorInfo.setColor() )
        pen = painter.pen()
        # draw a border around the widget.
        if self.border:
            pen.setColor( self.fgColorInfo.setColor() )
        else:
            pen.setColor( self.bgColorInfo.setColor() )
        bw = 2 # border width
        pen.setWidth(bw )
        painter.setPen(pen)
        painter.drawRect(x,y,w,h)
        x += bw+1
        y += bw+1
        w -= (bw+1)*2
        h -= (bw+1)*2

        if self.labelType == self.labelTypeEnum.pvName:
            label = self.indicatorPV.name
        else:
            label = self.label

        if label != None and label != "":
            fm = QFontMetrics(self.edmFont)
            box = fm.boundingRect(label)
            # always at the top, always reduce height
            y += box.height()
            h -= box.height()
            pen = painter.pen()
            pen.setColor( self.fgColorInfo.setColor() )
            painter.setPen(pen)
            painter.setFont(self.edmFont)
            painter.drawText(x,y-fm.descent(), label)

        if self.showScale:
            # what should be done:
            #   determine high/low values as strings,
            #   determine string width for font,
            #   reduce bar thickness by this value.
            #   draw a line and some tick marks and values.
            pen = painter.pen()
            pen.setColor( self.fgColorInfo.setColor() )
            painter.setPen(pen)
            painter.setFont(self.edmFont)
            fm = QFontMetrics(self.edmFont)

            drawmin = self.fmt % (self.rmin,)
            drawmax = self.fmt % (self.rmax,)
            tickpix = 16    # pixels per tick
            box0 = fm.boundingRect(drawmin)
            box1 = fm.boundingRect(drawmax)
            scalewidth = max(box0.width(), box1.width())
            scaleheight = max(box0.height(), box1.height())

            if self.orientation == self.orientationEnum.vertical:
                sx = x
                x += scalewidth + tickpix
                w -= scalewidth + tickpix
                y += int(scaleheight/2)
                h -= scaleheight
                linex = x-4
                painter.drawLine(linex, y, linex, y+h)
                la_incr = h / self.labelTicks
                sc_incr = (self.rmax-self.rmin)/self.labelTicks
                ma_incr = la_incr / self.majorTicks
                mi_incr = ma_incr / self.minorTicks
                mi_pix = int(tickpix/2)
                liney = y
                scale = self.rmax
                texty = int(scaleheight/2-fm.descent())
                while True:
                    painter.drawLine(int(linex-tickpix), int(liney), int(linex), int(liney) )
                    painter.drawText(int(sx), int(liney+texty), self.fmt % (scale,))
                    if scale <= self.rmin:
                        break
                    scale -= sc_incr
                    for major in range(0, self.majorTicks):
                        if major > 0:
                            ly = liney + major*ma_incr
                            painter.drawLine(int(linex-tickpix), int(ly), int(linex), int(ly))
                        for minor in range(1, self.minorTicks):
                            ly = liney + major*ma_incr + minor*mi_incr
                            painter.drawLine(int(linex-mi_pix), int(ly), int(linex), int(ly) )
                    liney += la_incr
            else:   # Horizontal
                sx = x
                sy = y
                x += scalewidth/2
                w -= scalewidth
                h -= scaleheight + tickpix
                liney = y + h + 4
                painter.drawLine(int(x), liney, int(x+w), liney)
                majorTicks = self.majorTicks
                minorTicks = self.minorTicks
                labelTicks = self.labelTicks

                la_incr = w / labelTicks
                if la_incr <= scalewidth:
                    ticks = int(w/(scalewidth*1.2))  # estimate number of ticks
                    if ticks < 2:
                        ticks = 2
                    la_incr = w / ticks
                    majorTicks = majorTicks * int(labelTicks/ticks)
                    labelTicks = ticks

                ma_incr = la_incr / majorTicks
                mi_incr = ma_incr / minorTicks
                sc_incr = (self.rmax-self.rmin)/labelTicks
                    
                mi_pix = int(tickpix/2)
                linex = x
                texty = liney + tickpix + scaleheight - fm.descent()
                scale = self.rmin
                while True:
                    painter.drawLine(int(linex), liney, int(linex), liney+tickpix)
                    value = self.fmt % (scale,)
                    box = fm.boundingRect(value)
                    painter.drawText(int(linex-box.width()/2), int(texty), value)
                    if scale >= self.rmax:
                        break
                    scale += sc_incr
                    for major in range(0, majorTicks):
                        if major > 0:
                            lx = int(linex + major*ma_incr)
                            painter.drawLine(lx, liney, lx, liney+tickpix-3)
                        for minor in range(1, minorTicks):
                            lx = int(linex + major*ma_incr + minor*mi_incr)
                            painter.drawLine(lx, liney, lx, liney+mi_pix)
                    linex += la_incr


        # get a value for the length/height of the bar
        try:
            value = self.indicatorPV.value
        except AttributeError:
            value = self.rmax

        if value == None:
                return

        if self.origin == None:
            self.origin = self.rmin
        value = min(self.rmax, max(self.rmin, value))

        if self.orientation == self.orientationEnum.vertical:
            if value >= self.origin:
                height = h * (value-self.origin)/(self.rmax-self.rmin)
                y = y + h * (self.rmax - self.origin)/(self.rmax-self.rmin) - height
            else:
                height = h * (self.origin-value)/(self.rmax-self.rmin)
                y = y + h * (self.rmax - self.origin)/(self.rmax-self.rmin)

            h = max(height,1)
        else:
            if value >= self.origin:
                width = w * ( value - self.origin )/(self.rmax - self.rmin)
                x = x + w * ( self.origin - self.rmin)/(self.rmax-self.rmin)
            else:
                width = w * ( self.origin - value )/(self.rmax - self.rmin)
                x = x + w * ( self.origin - self.rmin)/(self.rmax - self.rmin) - width
            w = max(width,1)

        if self.debug() : print("paintBar ({x}, {y}, {w}, {h}) value:{value} min/max {self.rmin}{self.rmax}")
        painter.setBrush( self.indicatorColorInfo.setColor() )
        painter.drawRect( int(x), int(y), int(w), int(h) )

edmApp.edmClasses["activeBarClass"] = activeBarClass
