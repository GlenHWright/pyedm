# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a line display class

from pyedm.edmWidget import edmWidget

from PyQt4.QtGui import QFrame, QPainter

class abstractShape(QFrame, edmWidget):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        edmWidget.__init__(self,parent)

    def cleanup(self):
        edmWidget.cleanup(self)
        try: self.lineColorInfo.cleanup()
        except: pass
        try: self.fillColorInfo.cleanup()
        except: pass

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)
        self.linewidth = object.getIntProperty("lineWidth", 1)

    def findFgColor(self):
        self.lineColorInfo = self.findColor("lineColor", (), "alarmPV", "lineAlarm")
        self.fill = self.object.getIntProperty("fill", 0)
        if self.fill == 0:
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
