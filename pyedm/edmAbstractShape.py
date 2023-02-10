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

#  a weirdness in shapes is that they have an alarmPv, but it is used as
# a colorPv. recommend over-writing tags somehow someway.
class abstractShape(QFrame, edmWidget):
    lineStyleEnum = Enum("linestyle", "solid dash", start=0)
    edmShapeFields = [
            edmField("lineColor", edmEdit.Color, defaultValue=0),
            edmField("lineAlarm", edmEdit.Bool, defaultValue=False),
            edmField("fill",        edmEdit.Bool, defaultValue=False),
            edmField("fillColor", edmEdit.Color, defaultValue=0),
            edmField("fillAlarm", edmEdit.Bool, defaultValue=False),
            edmField("lineWidth", edmEdit.Int, defaultValue=1),
            edmField("lineStyle", edmEdit.Enum, enumList=lineStyleEnum, defaultValue=0),
            edmField("invisible", edmEdit.Bool, defaultValue=False),
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
        self.lineColorInfo = None
        self.fillColorInfo = None
        super().edmCleanup()

    def findFgColor(self):
        self.lineColorInfo = self.findColor("lineColor", (), alarmName="lineAlarm")
        if self.objectDesc.getProperty("fill"):
            self.fillColorInfo = self.findColor("fillColor", (), alarmName="fillAlarm")
        else:
            self.fillColorInfo = None

    def findBgColor(self):
        pass

    def paintEvent(self, event=None):
        pass
        
    def redisplay(self):
        self.checkVisible()
        self.update()
