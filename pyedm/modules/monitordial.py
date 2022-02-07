from __future__ import division
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a meter of the value of a PV.
# Tries to build a display that matches the EDM meter.

from past.utils import old_div
import pyedm.edmDisplay as edmDisplay
import math
from pyedm.edmWidget import edmWidget

from PyQt4.QtGui import QAbstractSlider, QPainter, QFontMetrics, QPolygon
from PyQt4 import QtCore
from PyQt4.QtCore import QString, QPoint

class activeMeterClass(QAbstractSlider,edmWidget):
    V3propTable = {
        "2-1" : [ "INDEX", "meterColor", "meterAlarm", "INDEX", "scaleColor", "scaleAlarm", "INDEX", "labelColor", "INDEX", "fgColor", "fgAlarm",
            "INDEX", "bgColor", "INDEX", "tsColor", "INDEX", "bsColor", "controlPv", "readPv", "labelType", "showScale", "scaleFormat",
            "scalePrecision", "scaleLimitsFromDb", "useDisplayBg", "majorIntervals", "minorIntervals", "needleType", "shadowMode", "scaleMin", "scaleMax",
            "labelFont", "scaleFont" ]
            }
    def __init__(self, parent=None):
        QAbstractSlider.__init__(self, parent)
        edmWidget.__init__(self,parent)
        self.pvItem["readPv"] = [ "PVname", "pv", 1 ]
        self.readV = 0.0

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.scaleFont = self.object.getFontProperty("scaleFontTag", "helvetica-18")

    def getMin(self):
        return self.object.getDoubleProperty("scaleMin", 0.0)

    def getMax(self):
        return self.object.getDoubleProperty("scaleMax", 0.0)

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
        painter.setFont(self.scaleFont)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height())
        painter.setPen(QtCore.Qt.black )
        painter.drawRect( 0, 0, self.width()-1, self.height()-1)
        #
        mta = math.radians(self.object.getDoubleProperty("meterAngle", 180.0) )
        fm = painter.fontMetrics()
        caseWidth = 5   # number of pixels width of rectangular border around dial
        #faceX = self.x() + caseWidth
        #faceY = self.y() + caseWidth
        faceX = caseWidth
        faceY = caseWidth
        faceW = self.width() - 2*caseWidth
        faceH = self.height() - 2*caseWidth
        if "label" in self.object.tagValue:
            faceH = faceH + caseWidth - 4 - fm.ascent()
        scalePrecision = self.object.getIntProperty("scalePrecision", 0)
        if scalePrecision > 10 or scalePrecision < 0 :
            scalePrecision = 1
        
        scaleFormat = self.object.getStringProperty("scaleFormat", "Float")
        if scaleFormat == "GFloat":
            fmt = "g"
        elif scaleFormat == "Exponential":
            fmt = "e"
        else:
            fmt = "f"

        minval = self.getMin()
        maxval = self.getMax()
        scaleMinStr = QString("%1").arg( minval, 0, fmt, scalePrecision)
        scaleMaxStr = QString("%1").arg( maxval, 0, fmt, scalePrecision)
        # calculate the biggest scale width needed
        interval = self.object.getDoubleProperty("labelIntervals", 1.0)
        incr = max( old_div((maxval-minval),interval), 1.0)
        scaleWidth = self.checkWidth(fm, scaleMinStr, 0)
        scaleWidth = self.checkWidth(fm, scaleMaxStr, scaleWidth)
        scaleWidth = self.checkWidth(fm, QString("%1").arg(minval+incr, scalePrecision), scaleWidth)
        scaleWidth = self.checkWidth(fm, QString("%1").arg(maxval-incr, scalePrecision), scaleWidth)

        descent = old_div(( math.pi - mta),2)
        horizNeedlePlusScale = 0.5 * faceW -4 - scaleWidth;
        if descent > 0:
            horizNeedlePlusScale /= math.cos(descent)
            vf = 1.1 * (1 - 0.6*descent )
            vertNeedlePlusScale = old_div((faceH - fm.ascent() - 4 ), vf)
        else:
            vf = 1 - math.sin(descent)
            vertNeedlePlusScale = old_div((faceH - fm.ascent() - 12 ), vf)
        if vertNeedlePlusScale < horizNeedlePlusScale:
            needlePlusScale = vertNeedlePlusScale
        else:
            needlePlusScale = horizNeedlePlusScale
            ve = visibleFraction * needlePlusScale + fm.ascent() + 12
            if 1.1*ve < faceH:
                faceH = int(ve)
        center = QPoint(faceX+old_div(faceW,2), faceY+int(needlePlusScale + 4 +
            fm.ascent() ) )
        beginAngle = descent
        endAngle = beginAngle + mta

        # erase the dial area
        # draw a label
        label = self.object.getStringProperty("label")
        if label != None:
            painter.drawText( faceX+2, faceY + faceH + fm.ascent()-2, label)
        # painter.setPen(background color)
        # draw a needle
        labelTickSize = min(15.0, fm.ascent()*0.8)
        insideArc = needlePlusScale - labelTickSize
        line = self.getPoints(center, min( max(beginAngle + mta *(1.0
            -(old_div((self.readV-minval),(maxval-minval)))), beginAngle), endAngle),
            0.98*insideArc, 0.0)
        if self.object.getIntProperty("complexNeedle", 0) == 0:
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
        if self.object.getIntProperty("showScale",1) == 0:
            return

        # label the major tick marks,
        # draw the tick marks
        if interval > 0.0:
            lai = old_div(mta,interval) # label angle increment
            mjai = old_div(lai, max(0.1, self.object.getDoubleProperty("majorIntervals", 5.0) ))    # major angle increment
            miai = old_div(mjai, max(0.1, self.object.getDoubleProperty("minorIntervals", 2.0) ))   # minor angle increment
            labelVal = maxval
            la = beginAngle
            while la <= endAngle:
                # tick mark for label
                line = self.getPoints( center, la, insideArc, insideArc+labelTickSize)
                painter.drawLine( line[0], line[1])
                # label
                labelStr = QString("%1").arg( labelVal, 0, fmt, scalePrecision)
                labelVal -= incr
                position = self.getPoints(center, la, insideArc+labelTickSize+2)
                if la == beginAngle:
                    position[0] += QPoint(0, old_div(fm.ascent(),2) )
                elif la <= 1.5:
                    position[0] += QPoint(0,  0 )
                elif la <= 1.65:
                    position[0] += QPoint(old_div(-fm.width(labelStr),2), -fm.ascent() + 2)
                elif la < endAngle:
                    position[0] += QPoint(-fm.width(labelStr), 0 )
                else:
                    position[0] += QPoint(-fm.width(labelStr), old_div(fm.ascent(),2))
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

edmDisplay.edmClasses["activeMeterClass"] = activeMeterClass
