# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module generates a widget for monitoring the text value of a PV

# from  pyedm.monitortext import TextupdateClass
monitortext = __import__("monitortext", globals(), locals(), 1)
TextupdateClass = monitortext.TextupdateClass

import pyedm.edmDisplay as edmDisplay
import copy

class RegTextupdateClass(TextupdateClass):
    def __init__(self, parent=None):
        TextupdateClass.__init__(self, parent)

    def buildFromObject(self, object):
        TextupdateClass.buildFromObject(self, object)

    def redisplay(self, **kw):
        self.checkVisible()
        self.setText(self.controlPV.char_value)

# "inherit" and expand the V3 property table 
RegTextupdateClass.V3propTable = {}
for idx in TextupdateClass.V3propTable:
    RegTextupdateClass.V3propTable[idx] = TextupdateClass.V3propTable[idx] + [ "regExpr" ]

edmDisplay.edmClasses["RegTextupdateClass"] = RegTextupdateClass

