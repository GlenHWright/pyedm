# Copyright 2011-2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a widget that allows text entry.

from . import edmImport
from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmEditWidget import edmEdit
from .edmField import edmField

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

# relative execution of "from monitortext import TextupdateClass"
monitortext = edmImport("monitortext")
TextupdateClass = monitortext.TextupdateClass

class TextentryClass(TextupdateClass):
    menuGroup = [ "control", "Text Entry" ]

    edmEntityFields = [
            ] + TextupdateClass.edmEntityFields

    V3propTable = {
        "7-0" : [ "controlPv", "displayMode", "precision", "INDEX", "fgColor", "fgAlarm", "INDEX", "fillColor", "colorPv", "filled",
            "font", "alignment", "lineWidth", "lineAlarm" ]
            }
                
    def __init__(self, parent=None):
        super().__init__(parent)

    def findBgColor(self):
        edmWidget.findBgColor( self, palette=(QPalette.Base,))

    def findFgColor(self):
        edmWidget.findFgColor( self, palette=(QPalette.Text,))

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.setReadOnly(0) # override the  "display only" settings
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFrame(1)    # use the QFrame border ability
        self.edmParent.buttonInterest.append(self)

    # over-ride the focus events - simplification, because we really
    # want to allow updates unless keys have been pressed!

    def keyPressEvent(self, event):
        if event.text() == "\n" or event.text() == "\r":
            value = str(self.text())
            if self.controlPV.units != "" and value.endswith(self.controlPV.units):
                value = value[:-len(self.controlPV.units)]
            self.controlPV.put(value)
            self.haveFocus = False
            # self.controlPV.char_value = value
            event.accept()
            self.redisplay()
            return

        QLineEdit.keyPressEvent(self, event)
        self.haveFocus = True

    def focusOutEvent(self, event):
        QLineEdit.focusOutEvent(self, event)
        self.haveFocus = False
        self.redisplay()


TextentryClass.buildFieldListClass("edmEntityFields", "edmFontFields")

edmApp.edmClasses["TextentryClass"] = TextentryClass
