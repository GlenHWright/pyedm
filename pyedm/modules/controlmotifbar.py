# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# this module displays a simple slider
import pyedm.edmDisplay as edmDisplay

# from pyedm.controlbar import activeSliderClass
controlbar = __import__("controlbar", globals(), locals(), 1)
activeSliderClass = controlbar.activeSliderClass


class activeMotifSliderClass(activeSliderClass):
    def __init__(self, parent):
        super().__init__(parent)

    def buildFromObject(self, objectDesc):
        activeSliderClass.buildFromObject(self, objectDesc)
    def showScale(self):
        return 0    # this class never displays a scale
    def findReadonly(self):
        pass
        #self.setReadOnly(0)

edmDisplay.edmClasses["activeMotifSliderClass"] = activeMotifSliderClass

