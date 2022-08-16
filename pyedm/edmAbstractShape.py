# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a line display class

from pyedm.edmWidget import edmWidget

from PyQt5.QtWidgets import QFrame, QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

class abstractShape(QFrame, edmWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

    def cleanup(self):
        edmWidget.cleanup(self)
        try: self.lineColorInfo.cleanup()
        except: pass
        try: self.fillColorInfo.cleanup()
        except: pass

    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self, objectDesc)
        self.linewidth = objectDesc.getIntProperty("lineWidth", 1)

    def findFgColor(self):
        self.lineColorInfo = self.findColor("lineColor", (), "alarmPV", "lineAlarm")
        if self.objectDesc.getIntProperty("fill", 0) == 0:
            self.fillColorInfo = None
        else:
            self.fillColorInfo = self.findColor("fillColor", (), "fillAlarm", "fillAlarm")

    def findBgColor(self):
        pass

    def paintEvent(self, event=None):
        pass
        
    # ignore palette settings - this class draw colors directly
    def setupPalette( self, color, palette):
        pass

    def redisplay(self):
        self.checkVisible()
        self.update()
