from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a bar indicating a PV value

import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

import PyQt5.QtCore as QtCore
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QProgressBar

# Display class for bars: can be inherited by controllable widgets
#
class activeBarClass(QProgressBar,edmWidget):
    V3propTable = {
        "2-1" : [ "indicatorColor", "indicatorAlarm", "fgColor", "fgAlarm", "bgColor", "indicatorPv", "readPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ],
        "2-2" : [ "INDEX", "indicatorColor", "indicatorAlarm", "INDEX", "fgColor", "fgAlarm", "INDEX", "bgColor", "indicatorPv", "readPv", "label", "labelType", "showScale",
            "origin","font", "labelTicks", "majorTicks", "minorTicks", "border", "limitsFromDb", "precision", "min", "max", "scaleFormat", "nullPv", "orientation" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = [ "indicatorName", "indicatorPV", 1]
        self.minField, self.maxField = "min", "max"
        self.setTextVisible(0)

    def showScale(self):    # this method should be over-ridden.
        return self.objectDesc.getIntProperty("showScale", 0)

    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self,objectDesc)
        self.orientation = self.objectDesc.getStringProperty("orientation", "horizontal")
        self.displayLimits = self.objectDesc.getIntProperty("limitsFromDb", 0)
        self.objMin = self.objectDesc.getDoubleProperty(self.minField, None)
        self.objMax = self.objectDesc.getDoubleProperty(self.maxField, None)
        if self.orientation == "vertical" or self.orientation == "0":
            self.setOrientation(QtCore.Qt.Vertical)
            self.pixelCount = self.objectDesc.getIntProperty("h")
        else:
            self.pixelCount = self.objectDesc.getIntProperty("w")

        if self.showScale():
            pass
        self.fixRange(0.0, 100.0)
        if self.objMin != None and self.objMax != None:
            self.fixRange(self.objMin, self.objMax)
        if hasattr(self, "indicatorPV") and self.displayLimits:
            self.indicatorPV.add_callback(self.setDisplayLimits, None)

    def findFgColor(self):
        edmWidget.findFgColor( self, fgcolor="indicatorColor", palette=(QPalette.Highlight,))

    def findBgColor(self):
        edmWidget.findBgColor( self, bgcolor="bgColor", palette=(QPalette.Base,) )

    def setDisplayLimits(self, *kw, **args):
        pv = args["pv"]
        limits = pv.getLimits()
        if limits[0] < limits[1]:
            self.fixRange( limits[0], limits[1] )

    def fixRange(self, minval, maxval):
        self.rmin = minval
        self.rmax = maxval
        self.rscale = self.pixelCount/(maxval-minval)
        self.setRange(minval*self.rscale, maxval*self.rscale)
        print(f"fixRange rmin:{self.rmin} rmax:{self.rmax} rscale:{self.rscale}")

    def redisplay(self, *kw):
        self.checkVisible()
        newval = int( (self.indicatorPV.value) * self.rscale)
        if True or self.DebugFlag > 0:  print("activeBarClass  newval:", newval, "min:", self.rmin, "max:", self.rmax, "scale:", self.rscale)
        self.setValue( newval)

edmDisplay.edmClasses["activeBarClass"] = activeBarClass
