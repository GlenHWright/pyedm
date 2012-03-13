# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a static text display class

# This SHOULD simply be a QT label. However, there is no control over
# the 'leading' value for the font metrics, and this displays differently
# in X11 and Windows! So, because this works on fixed-format displays
# rather than auto-adjustable displays, the work needs to be done here.
import os
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget
from pyedm.edmEditWidget import edmEdit

from PyQt4.QtGui import QWidget, QTextLayout, QTextOption, QPalette, QFontMetrics, QPainter
from PyQt4.QtCore import QPoint, QPointF

class activeXTextClass(QWidget,edmWidget):
    V3propTable = {
        "2-0" : [ "fgColor", "colorMode", "useDisplayBg", "bgColor", "bgColorMode", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "value",
                    "font", "fontAlign", "autoSize", "ID" ] ,
        "2-1" : [ "INDEX", "fgColor", "colorMode", "useDisplayBg", "INDEX", "bgColor", "bgColorMode", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "value", "font", "fontAlign", "autoSize", "ID" ]

        }
    edmEditList = [
        edmEdit.TextBox     ("Text String",     "value"),
        edmEdit.CheckButton ("Auto Size",       "autoSize"),
        edmEdit.CheckButton ("Border",          "border"),
        edmEdit.LineThick   (),
        edmEdit.FgColor     (),
        edmEdit.CheckButton ("Alarm Sensitive", "fgColorInfo.alarmSensitive"),
        edmEdit.CheckButton ("Use Display Bg", "useDisplayBg"),
        edmEdit.BgColor     (),
        edmEdit.CheckButton ("Alarm Sensitive", "bgColorInfo.alarmSensitive"),
        edmEdit.Font        ("Font"),
        edmEdit.StringPV    ("Color PV",        "colorPV.getTrueName")
        ] + edmEdit.visibleList


    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        edmWidget.__init__(self, parent)
        self.offset = 0

    def findBgColor(self):
        edmWidget.findBgColor(self, palette=(QPalette.Base,) )

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)

        if self.object.checkProperty("value") == False:
            self.value = [ "" ]
        elif self.object.getIntProperty("major", 0) < 4:
            # EDM V3 format has a single string with embedded newlines encoded as '\n'
            self.value = [ self.macroExpand(val) for val in self.object.getStringProperty("value").split('\\n') ]
        else:
            # EDM V4 has multiple strings, 1 per line.
            self.value = [ self.macroExpand(val) for val in self.object.decode("value",isString=True)]

        self.qtlayout = QTextLayout( '\n'.join(self.value), self.object.getFontProperty("font") )
        self.fm = QFontMetrics(self.qtlayout.font())
        self.border = self.object.getIntProperty("border", 0)
        self.autoSize = self.object.getIntProperty("autoSize", 0) 
        self.lineWidth = self.object.getIntProperty("lineWidth", 0) 
        self.align = self.object.getStringProperty("fontAlign", "None")
        # Find new box size.
        if self.autoSize:
            max = -1
            for word in self.value:
                check_width = self.fm.width(word)
                if check_width > max:
                    max = check_width
            h = (self.fm.height())*len(self.value)

            if self.border:
                max = max + self.lineWidth*2
                h = h + self.lineWidth*2
            geom = self.geometry()
            geom.setWidth(max+2)
            geom.setHeight(h)
            self.setGeometry(geom)
        # print "- - -", self.fontInfo().family()
        # print "Metrics: leading:", fm.leading(), "ascent", fm.ascent(), "descent", fm.descent(), "border", self.border, "autoSize", self.autoSize , "align", align
        # print "Widget: ", self.x(), self.y(), self.width(), self.height()
        option = self.qtlayout.textOption()
        option.setAlignment( self.findAlignment("fontAlign"))
        #option.setWrapMode(QTextOption.NoWrap)
        self.qtlayout.setTextOption(option)
        self.qtlayout.beginLayout()
        leading = self.fm.leading()
        height = 0
        if os.name == "posix" and self.autoSize:
            self.offset = -5 # essentially an adjustment to "leading"
            height = self.height()/len(self.value) - self.fm.height()
        if self.fm.height() > self.height():
            height = (self.height() - self.fm.height())/2
        if self.border:
            height = height+self.lineWidth+1
        # starting height sets the baseline to the midpoint of the allocated space.
        while 1:
            line = self.qtlayout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(self.width())
            height += leading
            line.setPosition( QPointF(0, height))
            height += self.fm.height() + self.offset
        self.qtlayout.endLayout()
        self.update()

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.fillRect(0, self.offset, self.width()-1, self.height()-1,
        self.palette().brush(QPalette.Base))
        self.qtlayout.draw( painter, QPointF(0,self.offset))
        # print "activeXTextClass: lines:", self.layout.lineCount(), self.layout.text()

edmDisplay.edmClasses["activeXTextClass"] = activeXTextClass

