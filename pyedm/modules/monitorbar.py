from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a bar indicating a PV value

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmAbstractShape import abstractShape

import PyQt5.QtCore as QtCore
from PyQt5.QtGui import QPalette, QPainter, QFontMetrics
from PyQt5.QtWidgets import QFrame

# Display class for bars: can be inherited by controllable widgets
# unfortunate that the edm bar differs from what Qt offers. Make the activeBarClass
# an abstractShape
#
class activeBarClass(abstractShape,edmWidget):
    V3propTable = {
        "2-1" : [ "indicatorColor", "indicatorAlarm", "fgColor", "fgAlarm", "bgColor", "indicatorPv", "readPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ],
        "2-2" : [ "INDEX", "indicatorColor", "indicatorAlarm", "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "indicatorPv", "readPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = [ "indicatorName", "indicatorPV", 1]
        self.minField, self.maxField = "min", "max"

    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self,objectDesc)
        self.orientation = self.objectDesc.getStringProperty("orientation", "horizontal")
        self.displayLimits = self.objectDesc.getIntProperty("limitsFromDb", 0)
        self.objMin = self.objectDesc.getDoubleProperty(self.minField, None)
        self.objMax = self.objectDesc.getDoubleProperty(self.maxField, None)
        self.label = self.objectDesc.getStringProperty("label", None)
        self.labelType = self.objectDesc.getEnumProperty("labelType", [ "pvName", "literal" ], "pvName")
        self.showScale = self.objectDesc.getIntProperty("showScale", 0)
        self.scaleFormat = self.objectDesc.getStringProperty("scaleFormat", "FFloat")
        self.precision = self.objectDesc.getIntProperty("precision", 0)
        self.labelTicks = self.objectDesc.getIntProperty("labelTicks", 10)
        self.majorTicks = self.objectDesc.getIntProperty("majorTicks", 2)
        self.minorTicks = self.objectDesc.getIntProperty("minorTicks", 2)
        self.border = self.objectDesc.getIntProperty("border")

        # set orientation to TRUE if vertical, FALSE if horizontal
        self.orientation = ( self.orientation == "vertical" or self.orientation == "0")

        self.fixRange(0.0, 100.0)
        if self.objMin != None and self.objMax != None:
            self.fixRange(self.objMin, self.objMax)
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
        self.indicatorColorInfo = self.findColor( "indicatorColor", (), "indicatorPV", "indicatorAlarm")

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

        if self.border:
            # draw a border around the widget. adjust the
            # geometry of the bar drawing area accordingly
            pen = painter.pen()
            pen.setColor( self.fgColorInfo.setColor() )
            bw = 2 # border width
            pen.setWidth(bw )
            painter.setPen(pen)
            painter.drawRect(x,y,w,h)
            x += bw+1
            y += bw+1
            w -= (bw+1)*2
            h -= (bw+1)*2

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
            tickpix = 10    # pixels per tick
            box0 = fm.boundingRect(drawmin)
            box1 = fm.boundingRect(drawmax)
            scalewidth = max(box0.width(), box1.width())
            scaleheight = max(box0.height(), box1.height())

            if self.orientation == True: # vertical
                sx = x
                x += scalewidth + tickpix
                w -= scalewidth + tickpix
                sy = y
                y += scaleheight/2
                h -= scaleheight
                linex = x-4
                painter.drawLine(linex, y, linex, y+h)
                la_incr = h / self.labelTicks
                sc_incr = (self.rmax-self.rmin)/self.labelTicks
                ma_incr = la_incr / self.majorTicks
                mi_incr = ma_incr / self.minorTicks
                mi_pix = tickpix/2
                liney = y
                scale = self.rmax
                while liney <= y+h:
                    painter.drawLine(linex-tickpix, liney, linex, liney)
                    painter.drawText(sx, liney+scaleheight/4, self.fmt % (scale,))
                    scale -= sc_incr
                    for major in range(0, self.majorTicks):
                        if major > 0:
                            ly = liney + major*ma_incr
                            painter.drawLine(linex-tickpix, ly, linex, ly)
                        for minor in range(1, self.minorTicks):
                            ly = liney + major*ma_incr + minor*mi_incr
                            painter.drawLine(linex-mi_pix, ly, linex, ly)
                    liney += la_incr

                #painter.drawLine(linex-tickpix, y+h, linex, y+h)

                # this 'divide-by-4' is a total hack! I don't know what
                # I'm missing in tracking the calculations, but it makes
                # no sense to me. - GW 2022-08-17
                #painter.drawText(sx, y+scaleheight/4, drawmax)
                #painter.drawText(sx, y+h+scaleheight/4, drawmin)

        # get a value for the length/height of the bar
        try:
            value = self.indicatorPV.value
        except AttributeError:
            value = self.rmax

        if value == None:
                return
        if self.orientation == True:   # vertical
            height = h * (value-self.rmin)/(self.rmax-self.rmin)
            y = y + h - height
            h = height
        else:
            w = w * (value-self.rmin)/(self.rmax-self.rmin)

        if self.DebugFlag > 0 : print("paintBar ({x}, {y}, {w}, {h}) value:{value} min/max {self.rmin}{self.rmax}")
        painter.setBrush( self.indicatorColorInfo.setColor() )
        painter.drawRect( x, y, w, h)

edmDisplay.edmClasses["activeBarClass"] = activeBarClass
