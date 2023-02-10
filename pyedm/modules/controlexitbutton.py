# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a static text display class

from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPalette
from PyQt5 import QtCore

class exitButtonClass(QPushButton, edmWidget):
    menuGroup = ["control", "Exit Button"]
    edmEntityFields = [
            edmField("invisible", edmEdit.Bool, defaultValue=False),
            edmField("label", edmEdit.String, defaultValue="EXIT"),
            edmField("iconify", edmEdit.Bool, defaultValue=False),
            edmField("exitProgram", edmEdit.Bool, defaultValue=False),
            edmField("controlParent", edmEdit.Bool, defaultValue=False)
            ] + edmWidget.edmFontFields
    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.invisible = objectDesc.getProperty("invisible")
        self.label = objectDesc.getProperty("label")
        self.iconifyFlag = objectDesc.getProperty("iconify")
        self.exitProgram = objectDesc.getProperty("exitProgram")
        self.controlParent = objectDesc.getProperty("controlParent")
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
        # To Do - exit screen if exitProgram False, else exit the program
        pass

    def redisplay(self):
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()

edmApp.edmClasses["activeExitButtonClass"] = exitButtonClass
