# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module manages a widget to control a slide bar

from enum import Enum

from .edmApp import edmApp
from .edmWidget import edmWidget, pvItemClass, setupPalette
from .edmField import edmField
from .edmEditWidget import edmEdit
from .edmTextFormat import convDefault

import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QSlider, QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PyQt5.QtGui import QPainter, QPalette, QFontMetrics, QDoubleValidator
from PyQt5.QtCore import Qt


class activeSliderClass(QFrame, edmWidget):
    menuGroup = ["control", "Slider" ]
    labelTypeEnum = Enum("labelType", ["Literal", "pvLabel", "pvName"] , start=0)
    orientationEnum = Enum("orientation", "horizontal vertical", start=0)   # This isn't supported in EDM, do we want to start?
    edmEntityFields = [
            edmField("2ndBgColor", edmEdit.Color, 0),
            edmField("controlColor", edmEdit.Color, 0),
            edmField("indicatorColor", edmEdit.Color, 0),
            edmField("controlPv", edmEdit.PV, None),
            edmField("indicatorPv", edmEdit.PV, None),
            edmField("savedValuePvName", edmEdit.PV, None),
            edmField("controlLabelName", edmEdit.String, None),
            edmField("controlLabelType", edmEdit.Enum, defaultValue=0, enumList=labelTypeEnum),
            edmField("readLabelName", edmEdit.String, None),
            edmField("readLabelType", edmEdit.Enum, defaultValue=0, enumList=labelTypeEnum),
            edmField("precision", edmEdit.Int, 0),
            edmField("scaleMin", edmEdit.Int, 0),
            edmField("scaleMax", edmEdit.Int, 1),
            edmField("increment", edmEdit.Real, 1.0),
            edmField("orientation", edmEdit.Enum, enumList=orientationEnum, defaultValue=0),
            edmField("limitsFromDb", edmEdit.Bool, False),
            ]
    edmFieldList = edmWidget.edmBaseFields + edmWidget.edmColorFields  + edmEntityFields + edmWidget.edmFontFields + edmWidget.edmVisFields
    V3propTable = {
        "2-0" : [ "fgColor", "bgColor", "2ndBgColor", "controlColor", "readColor",
                "increment", "controlPv", "indicatorPv", "savedValuePvName", "controlLabelName", "controlLabelType", "readLabelName", "readLabelType", "font",
                "bgAlarm", "fgAlarm", "readAlarm", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
                "limitsFromDb", "precision", "scaleMin", "scaleMax", "accelMultiplier" ],
        "2-2" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "2ndBgColor", "INDEX", "controlColor", "INDEX", "readColor",
                "increment", "controlPv", "indicatorPv", "savedValuePvName", "controlLabelName", "readLabelName", "readLabelType", "font",
                "bgAlarm", "fgAlarm", "readAlarm", "ID", "changeCallbackFlag", "activateCallbackFlag", "deactivateCallbackFlag",
                "limitsFromDb", "precision", "scaleMin", "scaleMax", "accelMultiplier" ]
                }
    def __init__(self, parent):
        super().__init__(parent)
        self.pvItem["indicatorPv"] = pvItemClass( "indicatorName", "indicatorPV", dataCallback=self.indicatorCallback)
        self.pvItem["controlPv"] = pvItemClass( "controlName", "controlPV", dataCallback=self.controlCallback)      #override the default 'controlPv' entry
        self.pvItem["savedValuePvName"] = pvItemClass( "savedValuePvName", "savePV")
        self.minField, self.maxField = "scaleMin", "scaleMax"
        self.stepMul = 1.0

    def buildFromObject(self, objectDesc, **kw):
        kw['attr'] = None 
        self.setFrameShape(QFrame.Box)
        self.setAutoFillBackground(True)
        self.orientation = objectDesc.getProperty("orientation")
        self.haveIndicator = objectDesc.checkProperty("indicatorPv")
        self.precision = objectDesc.getProperty("precision")
        self.setCounter = 0
        if self.orientation == self.orientationEnum(0):
            self.buildHLayout()
            self.slider.setOrientation(Qt.Horizontal)
        else:
            return

        super().buildFromObject(objectDesc, **kw)
        
        self.controlColorInfo = self.objectDesc.getProperty("controlColor")
        self.offsetColorInfo = self.objectDesc.getProperty("2ndBgColor")
        setupPalette( self.labelWidget, self.controlColorInfo.getColor(), [QPalette.ColorRole.WindowText])
        setupPalette( self.valueWidget, self.controlColorInfo.getColor(),  [QPalette.ColorRole.WindowText])
        setupPalette( self.incrementWidget, self.controlColorInfo.getColor(),  [QPalette.ColorRole.Text])
        setupPalette( self.incrementWidget, self.offsetColorInfo.getColor(), [QPalette.ColorRole.Base])
        setupPalette( self.saveButton, self.offsetColorInfo.getColor(), [QPalette.ColorRole.Button])
        setupPalette( self.restoreButton, self.offsetColorInfo.getColor(), [QPalette.ColorRole.Button])
        if self.haveIndicator:
            self.readColorInfo = self.objectDesc.getProperty("indicatorColor")
            setupPalette( self.rbLabelWidget, self.readColorInfo.getColor(),  [QPalette.ColorRole.WindowText])
            setupPalette( self.rbValueWidget, self.readColorInfo.getColor(),  [QPalette.ColorRole.WindowText])
        self.displayLimits = self.objectDesc.getProperty("limitsFromDb")
        self.objMin = self.objectDesc.getProperty(self.minField)
        self.objMax = self.objectDesc.getProperty(self.maxField)

        self.labelWidget.setFont(self.edmFont)
        self.incrementWidget.setFont(self.edmFont)
        self.valueWidget.setFont(self.edmFont)
        self.saveButton.setFont(self.edmFont)
        self.restoreButton.setFont(self.edmFont)

        if self.haveIndicator:
            self.rbLabelWidget.setFont(self.edmFont)
            self.rbValueWidget.setFont(self.edmFont)

        clt = self.objectDesc.getProperty("controlLabelType")
        if clt == self.labelTypeEnum(0): # literal
            self.labelWidget.setText(self.objectDesc.getProperty("controlLabelName"))
        elif clt == self.labelTypeEnum(2):  # pvname
            self.labelWidget.setText(self.controlPV.name)
        else: # pv desc
            self.labelWidget.setText("Desc...")

        if self.haveIndicator:
            rlt = self.objectDesc.getProperty("readLabelType")
            if rlt == self.labelTypeEnum(0): # literal
                self.rbLabelWidget.setText(self.objectDesc.getProperty("readLabelName"))
            elif clt == self.labelTypeEnum(2):  # pvname
                self.rbLabelWidget.setText(self.indicatorPV.name)
            else: # pv desc
                self.rbLabelWidget.setText("Desc...")

        if self.displayLimits:
            if hasattr(self, "indicatorPV"):
                self.indicatorPV.add_callback(self.setDisplayLimits, None)
            else:
                self.controlPV.add_callback(self.setDisplayLimits, None)
        else:
            self.setControlRange(self.objMin, self.objMax)
            self.lowLimit.setText(str(self.objMin))
            self.highLimit.setText(str(self.objMax))

        self.setIncrementValue( self.objectDesc.getProperty("increment"))

        self.edmParent.buttonInterest.append(self)
        self.slider.valueChanged.connect(self.gotNewValue)
        self.saveButton.clicked.connect(self.savePosition)
        self.restoreButton.clicked.connect(self.restorePosition)
        self.validator = QDoubleValidator()
        self.validator.setDecimals(self.precision)
        self.incrementWidget.setValidator(self.validator)
        self.incrementWidget.editingFinished.connect(self.incrementCallback)

    # build a horizontal layout.
    def buildHLayout(self):
        ''' build (or rebuild) a horizontal control bar, edm-style
        '''
        mainlayout = self.layout()
        if mainlayout:
            count = mainlayout.count()
            controllayout = mainlayout.takeAt(0).layout()
            if count == 4:
                readbacklayout = mainlayout.takeAt(0).layout()
            else:
                readbacklayout = None
            slider = mainlayout.takeAt(0).widget()
            rangelayout = mainlayout.takeAt(0).layout()
            print(f"buildHLayout {count} {mainlayout.count()} {controllayout} {readbacklayout} {slider} {rangelayout}")
        else:
            mainlayout = QVBoxLayout()
            mainlayout.setContentsMargins(0,0,0,0)
            mainlayout.setSpacing(0)
            readbacklayout = None
            slider = None
            rangelayout = None

            controllayout = QHBoxLayout()
            controllayout.setContentsMargins(0,0,0,0)
            controllayout.setSpacing(0)
            self.labelWidget = QtWidgets.QLabel("---")
            self.incrementWidget = QtWidgets.QLineEdit("1.0")
            self.valueWidget = QtWidgets.QLabel("---")
            controllayout.addWidget(self.labelWidget, alignment=Qt.AlignmentFlag.AlignLeft)
            controllayout.addWidget(self.incrementWidget, alignment=Qt.AlignmentFlag.AlignHCenter)
            controllayout.addWidget(self.valueWidget, alignment=Qt.AlignmentFlag.AlignRight)

        if self.haveIndicator and readbacklayout is None:
            readbacklayout = QHBoxLayout()
            readbacklayout.setContentsMargins(0,0,0,0)
            readbacklayout.setSpacing(0)
            self.rbLabelWidget = QtWidgets.QLabel()
            self.rbValueWidget = QtWidgets.QLabel()
            readbacklayout.addWidget(self.rbLabelWidget, alignment=Qt.AlignmentFlag.AlignLeft)
            readbacklayout.addWidget(self.rbValueWidget, alignment=Qt.AlignmentFlag.AlignRight)
        elif readbacklayout and not self.haveIndicator:
            self.rbLabelWidget = None
            self.rbValueWidget = None
            readbacklayout.takeAt(0)
            readbacklayout.takeAt(0)
        
        if rangelayout == None:
            rangelayout = QHBoxLayout()
            rangelayout.setContentsMargins(0,0,0,0)
            rangelayout.setSpacing(0)
            self.lowLimit = QtWidgets.QLabel()
            self.highLimit = QtWidgets.QLabel()
            self.saveButton = QtWidgets.QPushButton("save")
            self.restoreButton = QtWidgets.QPushButton("restore")
            rangelayout.addWidget(self.lowLimit, alignment=Qt.AlignmentFlag.AlignLeft)
            rangelayout.addWidget(self.saveButton, alignment=Qt.AlignmentFlag.AlignRight)
            rangelayout.addWidget(self.restoreButton, alignment=Qt.AlignmentFlag.AlignLeft)
            rangelayout.addWidget(self.highLimit, alignment=Qt.AlignmentFlag.AlignRight)
        
        if slider == None:
            self.slider = QSlider(parent=self)

        mainlayout.addItem(controllayout)
        if self.haveIndicator:
            mainlayout.addItem(readbacklayout)
        mainlayout.addWidget(self.slider)
        mainlayout.addItem(rangelayout)
        self.setLayout(mainlayout)


    def setControlRange(self, lower, higher):
        '''
        try and do some intelligent reworking of the display range.
        '''
        if higher < lower:
            lower, higher = higher, lower
        full = higher - lower
        if full > 20 or self.precision == 0:
            self.stepMul = 1.0
        else:
            self.stepMul = full/100.0
            lower = lower/self.stepMul
            higher = higher/self.stepMul
        if self.precision > 0:
            exp = 10**self.precision
            self.stepMul = self.stepMul/exp
            lower = lower*exp
            higher = higher*exp
        self.slider.setRange(int(lower), int(higher))
        if self.controlPV.isValid:
            value = self.controlPV.value
            if int(value/self.stepMul) != self.slider.sliderPosition():
                self.slider.setSliderPosition(int(value/self.stepMul))

    def setDisplayLimits(self, *kw, **args):
        ''' data callback for a on-time setting of display limits.
            This does not check to see if limis changed at
            a later time.
        '''
        pv = args["pv"]
        newRange = [0, 100]
        try:
            limits = pv.getLimits()
            if limits[0] < limits[1]:
                self.setControlRange( int(limits[0]), int(limits[1]))
                newRange = limits
            else:
                self.setControlRange(0,100)
        except ValueError:
            self.setControlRange(0, 100)

        if self.haveIndicator:
            self.indicatorPV.del_callback(callback=self.setDisplayLimits)
        else:
            self.controlPV.del_callback(callback=self.setDisplayLimits)
        self.lowLimit.setText(convDefault(newRange[0], precision=self.precision))
        self.highLimit.setText(convDefault(newRange[1], precision=self.precision))

    def wheelEvent(self, event):
        '''
            wheelEvent - catch wheel events in the widget and pass to the slider.
        '''
        # print(f"wheelEvent {event}")
        self.slider.wheelEvent(event)

    def gotNewValue(self, val):
        '''called when the slider on the screen has changed'''
        if self.controlPV is None or not self.controlPV.isValid :
            return
        val = val *self.stepMul
        if val == self.controlPV.value:
            return

        if not self.slider.isSliderDown():
            if self.setCounter > 0:
                self.setCounter -= 1
                #print(f"gotNewValue ignoring {val} setting {self.setCounter}")
                return
        self.controlPV.put(val)

    def controlCallback(self, widget, *args, value=None, **kw):
        '''
            controlCallback - update the slider display if it has changed
        '''
        if value == None or self.valueWidget == None:
            return
        self.valueWidget.setText(convDefault(value, precision=self.precision))
        newPos = int(value/self.stepMul)
        if newPos != self.slider.sliderPosition() and not self.slider.isSliderDown():
            self.setCounter += 1
            self.slider.setSliderPosition(int(value/self.stepMul))

    def indicatorCallback(self, widget, *args, value=None, **kw):
        if value != None:
            self.rbValueWidget.setText(convDefault(value, precision=self.precision))

    def incrementCallback(self):
        val = float(self.incrementWidget.text())
        self.setIncrementValue(val)

    def setIncrementValue(self, increment):
        if self.precision == 0:
            disp = convDefault(increment, precision=1)
        else:
            disp = convDefault(increment, precision=self.precision)
        fm = QFontMetrics(self.edmFont)
        self.incrementWidget.setFixedWidth(fm.width(f" {disp} "))
        self.incrementWidget.setText(disp)
        print(f"setIncrementValue incr:{disp}({increment}) mul:{self.stepMul} min:{self.slider.minimum()} max:{self.slider.maximum()}")
        self.slider.setSingleStep(int(increment/self.stepMul))
        self.slider.setPageStep(int(increment/self.stepMul))

        
    def savePosition(self, *ignore):
        self.saveValue = self.slider.value()
        if hasattr(self, "savePV"):
            self.savePV.put(self.saveValue*self.stepMul)

    def restorePosition(self, *ignore):
        if hasattr(self, "savePV"):
            self.saveValue = self.savePV.value
        self.slider.setValue(self.saveValue)
        if self.controlPV != None and self.controlPV.isValid :
            val = self.saveValue* self.stepMul
            if val != self.controlPV.value:
                self.controlPV.put(val)

    def redisplay(self, *kw):
        self.checkVisible()

edmApp.edmClasses["activeSliderClass"] = activeSliderClass
