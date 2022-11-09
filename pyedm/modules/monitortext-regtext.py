# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget for monitoring the text value of a PV


from . import edmImport
from .edmApp import edmApp
from .edmField import edmField
from .edmEditWidget import edmEdit

monitortext = edmImport("monitortext")
TextupdateClass = monitortext.TextupdateClass


class RegTextupdateClass(TextupdateClass):
    menuGroup = [ "monitor", "Reg Text" ]
    edmEntityFields = [
            edmField("regExpr", edmEdit.String)
            ]
    edmFieldList = TextupdateClass.edmBaseFields + TextupdateClass.edmColorFields + \
            edmEntityFields + TextupdateClass.edmEntityFields +  \
            TextupdateClass.edmFontFields + TextupdateClass.edmVisFields

    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)

    def redisplay(self, **kw):
        self.checkVisible()
        self.setText(self.controlPV.char_value)

# "inherit" and expand the V3 property table 
RegTextupdateClass.V3propTable = {}
for idx in TextupdateClass.V3propTable:
    RegTextupdateClass.V3propTable[idx] = TextupdateClass.V3propTable[idx] + [ "regExpr" ]

edmApp.edmClasses["RegTextupdateClass"] = RegTextupdateClass

