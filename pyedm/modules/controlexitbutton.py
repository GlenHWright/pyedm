# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a static text display class

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPalette
from PyQt5 import QtCore
#from PyQt5.QtCore import SIGNAL

class exitButtonClass(QPushButton, edmWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.invisible = object.getIntProperty("invisible", 0)
        self.label = object.getStringProperty("label", "EXIT")
        self.iconifyFlag = object.getIntProperty("iconify", 0)
        self.exitProgram = object.getIntProperty("exitProgram", 0)
        self.controlParent = object.getIntProperty("controlParent", 0)
        #self.connect(self, SIGNAL("clicked(bool)"), self.onClicked)
        self.clicked.connect(self.onClicked)
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        self.setText(self.label)

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText, QPalette.Text))

    def findBgColor(self):
        self.bgColorInfo = self.findColor("bgColor", (QPalette.Button,))


    # push putton
    def onClicked(self, checked):
        pass

    def redisplay(self):
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()

edmDisplay.edmClasses["activeExitButtonClass"] = exitButtonClass
