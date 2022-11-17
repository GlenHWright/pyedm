# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a line display class
#
# MODULE LEVEL: high

from enum import Enum
from pyedm.edmWidget import edmWidget
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QFrame, QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

class abstractShape(QFrame, edmWidget):
    lineStyleEnum = Enum("linestyle", "solid dash", start=0)
    edmShapeFields = [
            edmField("lineColor", edmEdit.Color, defaultValue=0),
            edmField("lineAlarm", edmEdit.Bool, defaultValue=0),
            edmField("fill",        edmEdit.Bool, defaultValue=0),
            edmField("fillColor", edmEdit.Color, defaultValue=0),
            edmField("fillAlarm", edmEdit.Bool, defaultValue=0),
            edmField("lineWidth", edmEdit.Int, defaultValue=1),
            edmField("lineStyle", edmEdit.Enum, enumList=lineStyleEnum, defaultValue=0),
            edmField("invisible", edmEdit.Bool, defaultValue=0),
            edmField("alarmPv", edmEdit.String, defaultValue=None)
            ]
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.linewidth = 0

    def edmCleanup(self):
        try: self.lineColorInfo.edmCleanup()
        except: pass
        try: self.fillColorInfo.edmCleanup()
        except: pass
        edmWidget.edmCleanup(self)

    def findFgColor(self):
        self.lineColorInfo = self.findColor("lineColor", (), alarmName="lineAlarm")
        if self.objectDesc.getProperty("fill", 0) == 0:
            self.fillColorInfo = None
        else:
            self.fillColorInfo = self.findColor("fillColor", (), alarmName="fillAlarm")

    def findBgColor(self):
        pass

    def paintEvent(self, event=None):
        pass
        
    def redisplay(self):
        self.checkVisible()
        self.update()
