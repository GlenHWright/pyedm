# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# this module displays a simple slider
from . import edmImport
from .edmApp import edmApp

controlbar = edmImport("controlbar")
activeSliderClass = controlbar.activeSliderClass

class activeMotifSliderClass(activeSliderClass):
    menuGroup = ["control", "Motif Slider"]
    def __init__(self, parent):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
    def showScale(self):
        return 0    # this class never displays a scale
    def findReadonly(self):
        pass
        #self.setReadOnly(0)

edmApp.edmClasses["activeMotifSliderClass"] = activeMotifSliderClass

