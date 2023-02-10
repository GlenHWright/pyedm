from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a meter of the value of a PV.
# Tries to build a display that matches the EDM meter.

import math
from enum import Enum

from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QAbstractSlider
from PyQt5.QtGui import QPainter, QFontMetrics, QPolygon
from PyQt5 import QtCore, Qt
from PyQt5.QtCore import QPoint

class activeMeterClass(QAbstractSlider,edmWidget):
    menuGroup = [ "monitor", "Meter" ]
    labelTypeEnum = Enum("labelType", [ "pvName", "pvLabel", "literal" ], start=0)
    scaleFormatEnum = Enum("scaleFormat", "FFloat GFloat Exponential", start=0)
    edmEntityFields = [
            edmField("readPv", edmEdit.PV),
            edmField("labelType", edmEdit.Enum, enumList=labelTypeEnum, defaultValue=0),
            edmField("label", edmEdit.String),
            edmField("labelColor", edmEdit.Color),
            edmField("meterAngle", edmEdit.Real, defaultValue=180.0),
            edmField("trackDelta", edmEdit.Bool, defaultValue=False),
            edmField("showScale", edmEdit.Bool, defaultValue=False),
            edmField("scaleFormat", edmEdit.Enum, enumList=scaleFormatEnum, defaultValue="FFloat"),
            edmField("scalePrecision", edmEdit.Int, defaultValue=0),
            edmField("scaleLimitsFromDb", edmEdit.Bool, defaultValue=False),
            edmField("scaleMin", edmEdit.Real, defaultValue=0.0),
            edmField("scaleMax", edmEdit.Real, defaultValue=0.0),
            edmField("scaleColor", edmEdit.Color),
            edmField("scaleAlarm", edmEdit.Bool),
            edmField("labelIntervals", edmEdit.Real, defaultValue=1.0),
            edmField("majorIntervals", edmEdit.Real, defaultValue=5.0),   # major angle increment
            edmField("minorIntervals", edmEdit.Real, defaultValue=2.0),   # minor angle increment
            edmField("complexNeedle", edmEdit.Bool, defaultValue=False),
            edmField("needleColor", edmEdit.Color),
            edmField("caseColor", edmEdit.Color),
            edmField("scaleFontTag", edmEdit.FontInfo),
            edmField("labelFontTag", edmEdit.FontInfo)

            ]
    V3propTable = {
        "2-1" : [ "INDEX", "meterColor", "meterAlarm", "INDEX", "scaleColor", "scaleAlarm", "INDEX", "labelColor", "INDEX", "fgColor", "fgAlarm",
            "INDEX", "bgColor", "INDEX", "tsColor", "INDEX", "bsColor", "controlPv", "readPv", "labelType", "showScale", "scaleFormat",
            "scalePrecision", "scaleLimitsFromDb", "useDisplayBg", "majorIntervals", "minorIntervals", "needleType", "shadowMode", "scaleMin", "scaleMax",
            "labelFont", "scaleFont" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["readPv"] = pvItemClass( "PVname", "pv", redisplay=True)
        self.readV = 0.0

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.scaleFont = self.objectDesc.getProperty("scaleFontTag", "helvetica-18")
        self.useDbLimits = self.objectDesc.checkProperty("scaleLimitsFromDb")
        self.showScale  = self.objectDesc.checkProperty("showScale")

    def getMinMax(self):
        # if useDbLimits is True, then get Db scale limits and return that.
        if self.useDbLimits:
            try:
                mymin, mymax = self.pv.getLimits()
                return mymin, mymax
            except: pass

        mymin = self.objectDesc.getProperty("scaleMin", 0.0)
        mymax = self.objectDesc.getProperty("scaleMax", 0.0)
        if mymin == mymax:
            return ( 0.0, 1.0)
        return (mymin, mymax)

    def getPoints(self, center, angle, *radius):
        c = math.cos(angle)
        s = math.sin(angle)
        rval = []
        for r in radius:
            rval.append( QPoint(r*c+center.x(), -r*s+center.y()) )
        return rval

    def checkWidth(self, fm, str, lastWidth):
        return max(lastWidth, fm.width(str) )

    # Attempt to merge EDM dial code and QT dial code
    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.setBackground(self.getProperty("bgColor").getColor())
        painter.setBackgroundMode( QtCore.Qt.BGMode.OpaqueMode)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height())
        painter.setPen(self.getProperty("caseColor").getColor())
        painter.drawRect( 0, 0, self.width()-1, self.height()-1)
        #
        mta = math.radians(self.objectDesc.getProperty("meterAngle") )
        fm = painter.fontMetrics()
        caseWidth = 5   # number of pixels width of rectangular border around dial
        faceX = caseWidth
        faceY = caseWidth
        faceW = self.width() - 2*caseWidth
        faceH = self.height() - 2*caseWidth
        if self.objectDesc.checkProperty("label"):
            faceH = faceH + caseWidth - 4 - fm.ascent()
            label = self.objectDesc.getProperty("label")
            painter.setPen( self.objectDesc.getProperty("labelColor").getColor())
            painter.setFont( self.objectDesc.getProperty("labelFontTag"))
            painter.drawText( faceX+2, faceY + faceH + fm.ascent()-2, label)

        painter.setFont(self.scaleFont)
        scalePrecision = self.objectDesc.getProperty("scalePrecision")
        if scalePrecision > 10 or scalePrecision < 0 :
            scalePrecision = 1
        
        scaleFormat = self.objectDesc.getProperty("scaleFormat")
        if scaleFormat == "GFloat":
            fmt = "g"
        elif scaleFormat == "Exponential":
            fmt = "e"
        else:
            fmt = "f"

        minval, maxval = self.getMinMax()

        # moved from an obfuscated QString call to an obfuscated Python string function
        scaleMinStr = ("%%.%d%s"% (scalePrecision, fmt))%minval
        scaleMaxStr = ("%%.%d%s"% (scalePrecision, fmt))%maxval

        # calculate the biggest scale width needed
        interval = self.objectDesc.getProperty("labelIntervals")
        incr = max( (maxval-minval)/interval, 1.0)
        scaleWidth = self.checkWidth(fm, scaleMinStr, 0)
        scaleWidth = self.checkWidth(fm, scaleMaxStr, scaleWidth)
        scaleWidth = self.checkWidth(fm, ("%%.%dg"%scalePrecision)%(minval+incr), scaleWidth)
        scaleWidth = self.checkWidth(fm, ("%%.%dg"%scalePrecision)%(maxval+incr), scaleWidth)

        descent = ( math.pi - mta)/2
        horizNeedlePlusScale = 0.5 * faceW -4 - scaleWidth;
        if descent > 0:
            horizNeedlePlusScale /= math.cos(descent)
            vf = 1.1 * (1 - 0.6*descent )
            vertNeedlePlusScale = (faceH - fm.ascent() - 4 )/ vf
        else:
            vf = 1 - math.sin(descent)
            vertNeedlePlusScale = (faceH - fm.ascent() - 12 )/ vf
        if vertNeedlePlusScale < horizNeedlePlusScale:
            needlePlusScale = vertNeedlePlusScale
        else:
            needlePlusScale = horizNeedlePlusScale
            visibleFraction = 1 # find out what this really should be
            ve = visibleFraction * needlePlusScale + fm.ascent() + 12
            if 1.1*ve < faceH:
                faceH = int(ve)
        center = QPoint(faceX+faceW//2, faceY+int(needlePlusScale + 4 +
            fm.ascent() ) )
        beginAngle = descent
        endAngle = beginAngle + mta

        # draw a needle
        painter.setPen(self.getProperty("needleColor").getColor())
        labelTickSize = min(15.0, fm.ascent()*0.8)
        insideArc = needlePlusScale - labelTickSize
        line = self.getPoints(center, min( max(beginAngle + mta *(1.0
            -((self.readV-minval)/(maxval-minval))), beginAngle), endAngle),
            0.98*insideArc, 0.0)
        if self.objectDesc.getProperty("complexNeedle", 0) == 0:
            painter.drawLine(line[0], line[1] )
        else:
            poly = QPolygon()
            poly.append(line[1] + QPoint(-1, 0))
            poly.append(line[0])
            poly.append(line[1] + QPoint( 1, 0))
            poly.append(line[1] + QPoint( 0, -1))
            poly.append(line[0])
            poly.append(line[1] + QPoint( 0, 1))
            painter.drawPolygon(poly)

        # if showScale not set, don't draw any more
        if self.objectDesc.getProperty("showScale") == False:
            return

        # label the major tick marks,
        # draw the tick marks
        if interval > 0.0:
            lai = mta/interval # label angle increment
            mjai = lai/ max(0.1, self.objectDesc.getProperty("majorIntervals", 5.0) )    # major angle increment
            miai = mjai/ max(0.1, self.objectDesc.getProperty("minorIntervals", 2.0) )   # minor angle increment
            labelVal = maxval
            la = beginAngle
            painter.setPen(self.getProperty("scaleColor").getColor())
            while la <= endAngle:
                # tick mark for label
                line = self.getPoints( center, la, insideArc, insideArc+labelTickSize)
                painter.drawLine( line[0], line[1])
                # label
                #labelStr = QString("%1").arg( labelVal, 0, fmt, scalePrecision)
                #labelStr = qstring_wrapper(labelVal, 0, fmt, scalePrecision)
                labelStr = ("%%.%d%s"% (scalePrecision, fmt))%labelVal

                labelVal -= incr
                position = self.getPoints(center, la, insideArc+labelTickSize+2)
                if la == beginAngle:
                    position[0] += QPoint(0, fm.ascent()//2 )
                elif la <= 1.5:
                    position[0] += QPoint(0,  0 )
                elif la <= 1.65:
                    position[0] += QPoint(-fm.width(labelStr)//2, -fm.ascent() + 2)
                elif la < endAngle:
                    position[0] += QPoint(-fm.width(labelStr), 0 )
                else:
                    position[0] += QPoint(-fm.width(labelStr), fm.ascent()//2)
                painter.drawText(position[0], labelStr)

                # major tick marks
                m = la
                while m < la + lai and m < endAngle:
                    if m != la:
                        tick = self.getPoints( center, m, insideArc, insideArc+ 0.7*labelTickSize)
                        painter.drawLine( tick[0], tick[1])
                    # minor tick marks
                    mi = m + miai   # minor: major + minor angle increment
                    while mi < m + mjai:
                        tick = self.getPoints( center, mi, insideArc, insideArc+ 0.4*labelTickSize)
                        painter.drawLine( tick[0], tick[1])
                        mi += miai
                    m += mjai

                # next loop
                la += lai

    def redisplay(self):
        self.checkVisible()
        self.readV = self.pv.get()
        self.update()

edmApp.edmClasses["activeMeterClass"] = activeMeterClass
