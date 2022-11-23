# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Module for generating a widget for a static text display class

# This SHOULD simply be a QT label. However, there is no control over
# the 'leading' value for the font metrics, and this displays differently
# in X11 and Windows! So, because this works on fixed-format displays
# rather than auto-adjustable displays, the work needs to be done here.
import os
from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField, edmTag
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFontMetrics, QPalette
from PyQt5.QtCore import QPoint, QPointF

class activeXTextClass(QWidget,edmWidget):
    menuGroup = [ "monitor", "Text Box" ]

    edmEntityFields = [
        edmField("value", edmEdit.TextBox, array=True),
        edmField("autoSize", edmEdit.Bool, False),
        edmField("border", edmEdit.Bool, False),
        edmField("lineWidth", edmEdit.Int, 1),
        edmField("ID", edmEdit.String, None),
        edmField("alarmPv", edmEdit.PV, None)
            ] + edmWidget.edmFontFields
    V3propTable = {
        "2-0" : [ "fgColor", "colorMode", "useDisplayBg", "bgColor", "bgColorMode", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "value",
                    "font", "fontAlign", "autoSize", "ID" ] ,
        "2-1" : [ "INDEX", "fgColor", "colorMode", "useDisplayBg", "INDEX", "bgColor", "bgColorMode", "alarmPv", "visPv", "visInvert", "visMin", "visMax", "value", "font", "fontAlign", "autoSize", "ID" ]
        }
    def __init__(self, parent=None, **kw):
        super().__init__(parent, **kw)
        self.layout = None
        self.pvItem["alarmPv"] = pvItemClass( "alarmName", "alarmPV" )

    def findBgColor(self):
        edmWidget.findBgColor(self, palette=(QPalette.Base,) )

    @classmethod
    def setV3PropertyList(classRef, propValue, obj):
        if edmApp.debug() : print(f"setV3PropertyList({classReff}, {propValue}, {obj}")
        propName = classRef.getV3PropertyList(obj.tags['major'].value, obj.tags['minor'].value, obj.tags['release'].value)
        if len(propValue) != len(propName):
            print("warning: mismatched property list", "class", obj.tags['Class'], obj.tags['major'].value, obj.tags['minor'].value, len(propName), len(propValue))
            print(propName)
            print(propValue)

        for n,v in zip(propName, propValue):
            obj.tags[n] = edmTag(n,v)

        if 'value' in obj.tags:
            obj.tags['value'].value = obj.tags['value'].value.split("\\n")

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)

        if self.objectDesc.checkProperty("value") == False:
            value = [ "" ]
        else:
            # EDM V4 has multiple strings, 1 per line.
            value = [ self.macroExpand(val) for val in self.objectDesc.getProperty("value",arrayCount=-1)]

        fm = QFontMetrics(self.edmFont)
        border = self.objectDesc.getProperty("border")
        autoSize = self.objectDesc.getProperty("autoSize") 
        lineWidth = self.objectDesc.getProperty("lineWidth") 
        # Find new box size.
        if autoSize:
            maxwidth = -1
            for word in value:
                maxwidth = max(maxwidth, fm.width(word))

            h = (fm.height())*len(value)
            if border:
                maxwidth = maxwidth + lineWidth*2
                h = h + lineWidth*2

            geom = self.geometry()
            geom.setWidth(maxwidth+2)
            geom.setHeight(h+2*len(value))
            self.setGeometry(geom)

        if self.layout == None:
            self.layout = QVBoxLayout()
            self.layout.setContentsMargins(0,0,0,0)
            self.layout.setSpacing(4)
        else:
            while self.layout.takeAt(0) != None:
                pass

        for line in value:
            label = QLabel(line)
            self.layout.addWidget(label)
            self.layout.setAlignment(label, self.findAlignment())
        self.setLayout(self.layout)
        self.update()

edmApp.edmClasses["activeXTextClass"] = activeXTextClass

