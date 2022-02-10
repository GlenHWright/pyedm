# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a group display class
#

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWindowWidget import edmWindowWidget
from pyedm.edmWidget import edmWidget

from PyQt5 import QtCore, QtGui

class activeGroupClass(edmWindowWidget, edmWidget):
    '''group display widget
        because the data input is handled by the edmScreen module, there isn't much to
        do at this level, and there is no need of alternate file input handling here'''
    def __init__(self, parent=None, **kw):
        super().__init__(parent, **kw)

    def cleanup(self):
        self.buttonInterest = []
        edmWidget.cleanup(self)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)
        self.parentx = object.getIntProperty("x")
        self.parenty = object.getIntProperty("y")
        self.macroTable = getattr(self.edmParent, "macroTable", None)
        edmDisplay.generateWidget(self.object, self)
        # Unknown level of nesting, so the assumption is made that
        # this widget could contain something that would like
        # a mouse message
        self.edmParent.buttonInterest.append(self)

    def redisplay(self):
        self.checkVisible()

    def findFgColor(self):
        return None

    def findBgColor(self):
        return None

edmDisplay.edmClasses["activeGroupClass"] = activeGroupClass


