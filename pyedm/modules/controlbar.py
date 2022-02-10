# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages a widget to control a slide bar
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt

#class activeSliderClass(QwtSlider, edmWidget):
class activeSliderClass(QSlider, edmWidget):
    V3propTable = {
        "2-0" : [ "fgColor", "bgColor", "shadeColor", "controlColor", "readColor",
                "increment", "controlPv", "indicatorPv", "savedValuePvName", "controlLabelName", "controlLabelType", "readLabelName", "readLabelType", "font",
                "bgAlarm", "fgAlarm", "readAlarm", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
                "limitsFromDb", "precision", "scaleMin", "scaleMax", "accelMultiplier" ],
        "2-2" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "shadeColor", "INDEX", "controlColor", "INDEX", "readColor",
                "increment", "controlPv", "indicatorPv", "savedValuePvName", "controlLabelName", "readLabelName", "readLabelType", "font",
                "bgAlarm", "fgAlarm", "readAlarm", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
                "limitsFromDb", "precision", "scaleMin", "scaleMax", "accelMultiplier" ]
                }
    def __init__(self, parent):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = [ "indicatorName", "indicatorPV", 1]
        self.pvItem["controlPv"] = [ "controlName", "controlPV", 0]
        self.minField, self.maxField = "scaleMin", "scaleMax"

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object,attr=None)
        self.findReadonly()
        self.orientation = self.object.getStringProperty("orientation", "horizontal")
        self.displayLimits = self.object.getIntProperty("limitsFromDb", 0)
        self.objMin = self.object.getDoubleProperty(self.minField, None)
        self.objMax = self.object.getDoubleProperty(self.maxField, None)
        if self.orientation == "vertical":
            self.setOrientation(Qt.Vertical)
        else:
            self.setOrientation(Qt.Horizontal)
        '''
        if self.showScale():
            self.scale = QwtScaleDraw()
            self.setScaleDraw(self.scale)
            if self.orientation == "vertical":
                self.setScalePosition(QwtSlider.LeftScale)
            else:
                self.setScalePosition(QwtSlider.BottomScale)
                '''
        if hasattr(self, "indicatorPV") and self.displayLimits:
            self.indicatorPV.add_callback(self.setDisplayLimits, None)

        #self.connect(self, SIGNAL("valueChanged(double)"), self.gotNewValue)
        self.valueChanged.connect(self.gotNewValue)
        # if we have a controlPv, but no indicatorPv in the tags list, try and
        # make the indicatorPv (from activeBarClass) the same as the controlPv
        if hasattr(self, "controlPV") and "indicatorPv" not in self.object.tagValue:
            self.pvSet( self.controlName, "indicatorPv")
            self.indicatorPV.add_callback(self.setDisplayLimits, None)
        self.edmParent.buttonInterest.append(self)

    def showScale(self):    # this class always displays a scale
        return 1

    def findReadonly(self):
        pass
        # self.setReadOnly(0)

    def setDisplayLimits(self, *kw, **args):
        pv = args["pv"]
        # print "setDisplayLimits", pv
        limits = pv.getLimits()
        if limits[0] < limits[1]:
            self.setRange( int(limits[0]), int(limits[1]) )

    def gotNewValue(self, val):
        '''called when the slider on the screen is changed'''
        # although it should be a no-op, on startup the valueChanged callback tries
        # to put the display value out as the indicator value.
        if self.controlPV != None and self.controlPV.isValid :
            if val != int(self.indicatorPV.value):
                self.controlPV.put(val)

    def redisplay(self, *kw):
        self.checkVisible()
        if self.value() != (self.indicatorPV.value):
            self.setValue( (self.indicatorPV.value))

edmDisplay.edmClasses["activeSliderClass"] = activeSliderClass
