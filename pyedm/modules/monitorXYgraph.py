# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#
# 
# Module to display an XY graph
#
# Different Plot types:
#  XPV source can be None, a scalar value, or an array value
#  YPV source can be None, a scalar value, or an array value
#  X-axis can be Linear or Time (with log10 variants)
#  Y-axis can be Linear or Time (with log10 variants)
#  update mode can be "X and Y', "X or Y", "X", "Y" "Trigger"
#  update timer can be 0 or > 0 (not sure if 0 is different than undefined!)
#
#  That gives roughly 360 variants! A number of them are nonsensical, such as
#  both X and Y PVs being None, or plotting an array against anything - you probably don't want a 2D plot
#  The most challenging situation is determining how to match length of input data.
#
#  Input values must be numbers. A number of things will break in messy ways
#  if any of the PVs are strings.
#  
# 

from dataclasses import dataclass
import sys
from enum import Enum
from typing import Any

from .edmPVfactory import buildPV, expandPVname
from .edmApp import redisplay, edmApp
from .edmWidget import edmWidget, pvItemClass
from .edmField import edmField, edmTag
from .edmFont import toHTML
from .edmEditWidget import edmEditField, edmEdit
from .edmProperty import converter

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPen, QPalette, QFontMetrics, QFontInfo, QPainter
import pyqtgraph as pgraph
# from Exceptions import AttributeError

import collections
import time

# custom screen for displaying an Axis: X, Y, or Y2
class edmEditAxisScreen(edmEdit.SubScreen):
    def __init__(self, *args, axis, **kw):
        super().__init__(*args, **kw)
        self.axis = axis

# custom screen for configuring plot lines
#
class edmEditCurveConfig(edmEdit.SubScreen):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.newtags = {}
        self.numCurves = self.widget.numCurves
        self.colvalue = {}
        for idx, fld in enumerate(self.edmfield.group):
            self.colvalue[idx] = self.widget.objectDesc.getProperty(fld.tag, arrayCount=self.widget.numCurves).copy()

    def buildLayout(self):
        layout = QtWidgets.QGridLayout()
        # add column headers, and create the array of values.
        for idx, fld in enumerate(self.edmfield.group):
            label = QtWidgets.QLabel(fld.tag)
            label.setFrameShape(QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken)
            layout.addWidget(label, 0, idx)
        
        for row in range(self.numCurves):
            for idx, fld in enumerate(self.edmfield.group):
                tagw = fld.editClass(fld.tag, fld, self.widget, **fld.editKeywords)
                w = tagw.showEditWidget(self.colvalue[idx][row]).nolabel()
                layout.addWidget(w, row+1, idx)
                self.editlist.append(tagw)
                tagw.newValue.connect(lambda tag, value, row=row,col=idx: self.onNewValue(tag,value,row,col))
            remove = QtWidgets.QPushButton("Remove")
            layout.addWidget(remove, row+1, len(self.edmfield.group))
            remove.clicked.connect(lambda clicked,curveNum=row: self.removeRow(curveNum))
        addrow = QtWidgets.QPushButton("Add Row")
        layout.addWidget(addrow, self.numCurves+1, 0)
        addrow.clicked.connect(self.addRow)

        return layout

    def removeRow(self, curveNum):
        ''' removeRow - copy the gridlayout to a new gridlayout,
            ignoring the row to be deleted.
        '''
        print(f"edmEditCurveConfig removeRow {curveNum}")
        for idx in range(len(self.colvalue)):
            self.colvalue[idx].pop(curveNum)
        self.numCurves -= 1
        layout = self.buildLayout()
        self.changeLayout(layout)
        self.newtags["numTraces"] = self.numCurves


    def addRow(self):
        print(f"edmEditCurveConfig {self} addRow")
        self.numCurves += 1
        for idx, fld in enumerate(self.edmfield.group):
            self.colvalue[idx].append(converter(edmTag(fld.tag, fld.defaultValue), fld, None))
            self.onNewValue(fld.tag, self.colvalue[idx][-1], self.numCurves-1, idx)
        layout = self.buildLayout()
        self.changeLayout(layout)
        self.newtags["numTraces"] = self.numCurves

    def onNewValue(self, tag, value, row, col):
        print(f"onNewValue {tag} {value} {row} {col}")
        if tag not in self.newtags.keys():
            self.newtags[tag] = self.colvalue[col]
        try:
            self.newtags[tag][row] = value
        except IndexError:
            self.newtags[tag].append(value)

    def onApply(self):
        print(f"onApply {self.newtags}")
        for tag,value in self.newtags.items():
            self.newValue.emit(tag,value)

    def onDone(self):
        print(f"onDone {self.newtags}")
        for tag,value in self.newtags.items():
            self.newValue.emit(tag,value)
        edmEdit.SubScreen.onDone(self)

class xAxisClass(pgraph.AxisItem):
    def setTickLabelMode(self, mode=0, base=0):
        '''
        sets the labelling mode for the x axis. This matches the edm
        modes of "linear", "log10", "time", "log10(time)"
        base of 0 (timestamp) or 1 (seconds before now)
        '''
        self.tickMode = mode
        self.tickBase = base

    def tickStrings(self, *args, **kw):
        if self.tickMode <  2:
            return pgraph.AxisItem.tickStrings(self, *args, **kw)
        
        try:
            values = args[0]
        except:
            print("Error: no values to convert to time", sys.exc_info()[0], *args, **kw)
            return pgraph.AxisItem.tickStrings(self,*args, **kw)
        
        if len(values) < 1:
            return pgraph.AxisItem.tickStrings(self,*args,  **kw)
        
        rng = max(values)-min(values)
        if self.tickBase:
            string = "-%H:%M:%S"
            label1 = "-%H"
            label2 = "0"
        elif rng < 3600*24:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= 3600*24 and rng < 3600*24*30:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= 3600*24*30 and rng < 3600*24*30*24:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >=3600*24*30*24:
            string = '%Y'
            label1 = ''
            label2 = ''

        strns = []
        for x in values:
            try:
                strns.append(time.strftime(string, time.localtime(x)))
            except ValueError:  ## Windows can't handle dates before 1970
                strns.append('')
        '''
        try:
            label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        '''
        return strns


@dataclass
class onePVvalue:
    ''' simple tracking for a single value returned from a PV
        this simplifies the coding of availability of new data.
    '''
    value : Any
    count : int


class xyGraphClass(pgraph.PlotWidget, edmWidget):
    menuGroup = [ "monitor", "XY Plot" ]
    plotModeEnum = Enum("plotMode", "plotNPtsAndStop plotLastNPts", start=0)
    styleEnum = Enum("axisStyle", "linear log10 time log10(time)" , start=0)
    srcEnum = Enum( "source", "AutoScale fromUser fromPv" , start=0)
    formatEnum = Enum( "format", "FFloat GFloat Exponential" , start=0)      # not used??
    updateModeEnum = Enum( "update", "xAndY xOrY x y trigger" , start=0)
    plotStyleEnum = Enum( "plotStyle", "line point needle single-point", start=0)
    plotSymbolEnum = Enum( "symbol", "none circle square diamond", start=0)
    lineStyleEnum = Enum("lineStyle", "solid dash", start=0)
    xAxisTimeEnum = Enum("xAxisTime", "seconds date dateTime", start=0)
    opModeEnum = Enum("opMode", "scope plot", start=0)

    edmEntityFields = [
            edmField("triggerPv", edmEdit.PV, defaultValue=None),
            edmField("resetPv", edmEdit.PV, defaultValue=None),
            edmField("gridColor", edmEdit.Color, defaultValue=0),
            edmField("numTraces", edmEdit.Int, defaultValue=0, readonly=True),                              # this may need to be invisible and auto generated!
            edmField("Curve Configure", edmEditCurveConfig, group=[
                edmField("xPv", edmEdit.PV, defaultValue=None, array=True),
                edmField("yPv", edmEdit.PV, defaultValue=None, array=True),                  # optional(?) list of Y-axis PV's
                edmField("plotStyle", edmEdit.Enum, defaultValue=0, enumList=plotStyleEnum, array=True),
                edmField("plotUpdateMode", edmEdit.Enum, defaultValue="y", array=True, enumList=updateModeEnum),    # xAndY, xOrY, x, y, trigger
                edmField("plotSymbolType", edmEdit.Enum, defaultValue=None, array=True, enumList=plotSymbolEnum ),
                edmField("opMode", edmEdit.Enum, defaultValue=0, array=True, enumList=opModeEnum),           # scope, plot
                edmField("useY2Axis", edmEdit.Bool, defaultValue=False, array=True),         #
                edmField("xSigned", edmEdit.Bool, defaultValue=False, array=True),           #
                edmField("ySigned", edmEdit.Bool, defaultValue=False, array=True),           #
                edmField("plotColor", edmEdit.Color, defaultValue="black", array=True),      # 'index' and number
                edmField("lineThickness", edmEdit.Int, defaultValue=1, array=True),          # integers
                edmField("lineStyle", edmEdit.Enum, defaultValue="solid", array=True, enumList=lineStyleEnum)     # solid, dash
                ] ),
            edmField("plotMode", edmEdit.Enum, enumList=plotModeEnum),
            edmField("graphTitle", edmEdit.String),
            edmField("nPts", edmEdit.Int, defaultValue=100),
            edmField("updateTimerMs", edmEdit.Int, defaultValue=0),
            edmField("unused", edmEdit.HList, group= [
                edmField("showXAxis", edmEdit.Bool, defaultValue=1),
                edmField("xAxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
            ] ),
            edmField("unused", edmEdit.HList, group= [
                edmField("xAxisSrc",  edmEdit.Enum, defaultValue=0, enumList=srcEnum),     # AutoScale, fromUser and fromPv
                edmField("xAxisFormat",  edmEdit.Enum, defaultValue=0, enumList=formatEnum)        # FFloat, GFloat, ???? - needs to be checked!
            ] ),
            edmField("X-Axis Settings", edmEditAxisScreen, editKeywords={"axis":'x'},
                group = [
                edmField("xAxisTimeFormat", edmEdit.Enum, defaultValue=0, enumList=xAxisTimeEnum),
                edmField("xAxisPrecision",  edmEdit.Int, defaultValue=0),
                edmField("xMin", edmEdit.Real, defaultValue=0),
                edmField("xMax", edmEdit.Real, defaultValue=0),
                edmField("xLabel", edmEdit.String, defaultValue=None),
                edmField("xLabelIntervals", edmEdit.Real, defaultValue=None),
                edmField("xMajorsPerLabel", edmEdit.Int, defaultValue=None),
                edmField("xMinorsPerMajor", edmEdit.Int, defaultValue=None),
                edmField("xShowLabelGrid", edmEdit.Bool, defaultValue=False),
                edmField("xShowMajorGrid", edmEdit.Bool, defaultValue=False),
                edmField("xShowMinorGrid", edmEdit.Bool, defaultValue=False)
                ] ),
            edmField("unused", edmEdit.HList, group= [
                edmField("showYAxis", edmEdit.Bool, defaultValue=1),
                edmField("yAxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
                ] ),
            edmField("unused", edmEdit.HList, group= [
                edmField("yAxisSrc",  edmEdit.Enum, defaultValue=0, enumList=srcEnum),     # AutoScale, fromUser and fromPv
                edmField("yAxisFormat",  edmEdit.Enum, defaultValue=0, enumList=formatEnum)        # FFloat, GFloat, ???? - needs to be checked!
            ] ),
            edmField("Y-Axis Settings", edmEditAxisScreen, editKeywords={"axis":'y'}, group = [
                edmField("yAxisPrecision",  edmEdit.Int, defaultValue=0),
                edmField("yMin", edmEdit.Real, defaultValue=0),
                edmField("yMax", edmEdit.Real, defaultValue=0),
                edmField("yLabel", edmEdit.String, defaultValue=None),
                edmField("yLabelIntervals", edmEdit.Real, defaultValue=None),
                edmField("yMajorsPerLabel", edmEdit.Int, defaultValue=None),
                edmField("yMinorsPerMajor", edmEdit.Int, defaultValue=None),
                edmField("yShowLabelGrid", edmEdit.Bool, defaultValue=False),
                edmField("yShowMajorGrid", edmEdit.Bool, defaultValue=False),
                edmField("yShowMinorGrid", edmEdit.Bool, defaultValue=False)
                ] ),
            edmField("unused", edmEdit.HList, group = [
                edmField("showY2Axis", edmEdit.Bool, 0),
                edmField("y2AxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
            ] ),
            edmField("unused", edmEdit.HList, group = [
                edmField("y2AxisSrc",  edmEdit.Enum, defaultValue=None, enumList=srcEnum),     # AutoScale, fromUser and fromPv
                edmField("y2AxisFormat",  edmEdit.Enum, defaultValue=None, enumList=formatEnum),        # FFloat, GFloat, ???? - needs to be checked!
            ] ),
            edmField("Y2-Axis Settings", edmEditAxisScreen, editKeywords={"axis":'y2'},
                group = [
                edmField("y2AxisPrecision",  edmEdit.Int, defaultValue=0),
                edmField("y2Min", edmEdit.Real, defaultValue=0),
                edmField("y2Max", edmEdit.Real, defaultValue=0),
                edmField("y2Label", edmEdit.String, defaultValue=None),
                edmField("y2LabelIntervals", edmEdit.Real, defaultValue=None),
                edmField("y2MajorsPerLabel", edmEdit.Int, defaultValue=None),
                edmField("y2MinorsPerMajor", edmEdit.Int, defaultValue=None),
                edmField("y2ShowLabelGrid", edmEdit.Bool, defaultValue=False),
                edmField("y2ShowMajorGrid", edmEdit.Bool, defaultValue=False),
                edmField("y2ShowMinorGrid", edmEdit.Bool, defaultValue=False)
                ] ),
        ] + edmWidget.edmFontFields

    def __init__(self, parent=None, *args):
        # set up arguments for configuring inherited class PlotWidget
        self.xaxisInstance =  xAxisClass(orientation="bottom") 
        axisArg = { "bottom": self.xaxisInstance }
        super().__init__(parent, *args, axisItems=axisArg)
        self.pvItem["triggerPv"] = pvItemClass( 'triggerName', 'triggerPV', dataCallback=self.triggerCallback)
        self.pvItem["resetPv"]   = pvItemClass( 'resetName', 'resetPV', dataCallback=self.resetCallback)
        # self.debug(setDebug = 1)

    # I think this bug is now fixed....
    def xx__getattr__(self, attr):    ## workaround for bug in PlotWidget __getattr__() which uses NameError instead of AttributeError
        if hasattr(self.plotItem, attr):
            m = getattr(self.plotItem, attr)
            if hasattr(m, '__call__'):
                return m
        raise AttributeError(attr)

    def edmCleanup(self):
        try:
            for curve in self.curves:
                if curve.xPv:
                    curve.xPv.del_callback(self)
                if curve.yPv:
                    curve.yPv.del_callback(self)
        except TypeError:
            pass    # self.curves may be None

        super().edmCleanup()

    @classmethod
    def setV3PropertyList(classRef, values, tags):
        for name in [ "graphTitle", "xLabel", "yLabel", "INDEX", "fgColor", "INDEX", "bgColor", "plotMode", "border", "count", "updateTimerValue",
                    "xAxis", "xAxisStyle", "xAxisSource", "xMin", "xMax", "xAxisTimeFormat",
                    "yAxis", "yAxisStyle", "yAxisSource", "yMin", "yMax",
                    "y2Axis", "y2AxisStyle", "y2AxisSource", "y2Min", "y2Max",
                "triggerPv", "resetPv", "resetMode", "font",
                    "xNumLabelIntervals", "xLabelGrid", "xMajorGrid", "xMinorGrid", "xAnnotationFormat", "xAnnotationPrecision",
                    "yNumLabelIntervals", "yLabelGrid", "yMajorGrid", "yMinorGrid", "yAnnotationFormat", "yAnnotationPrecision",
                    "y2NumLabelIntervals", "y2LabelGrid", "y2MajorGrid", "y2MinorGrid", "y2AnnotationFormat", "y2AnnotationPrecision",
                "INDEX", "gridColor", "numtraces" ] :
            tags[name] = values.pop(0)

        traceNames = [ "xPv" ,"yPv", "plotColor", "plotStyle", "plotUpdateMode", "plotSymbolType", "opMode", "y2Scale", "xSigned", "ySigned"] 
        for name in traceNames:
            tags[name] = []

        for idx in range(0, numTraces):
            for name in traceNames:
                tags[name].append( values.pop(0) )

        values.pop(0) # ignore!
        tags['y2Label'] = values.pop(0)
            
    def buildFromObject(self, objectDesc, **kw):
        '''buildFromObject - build the widget plus all the plot curves needed
        '''
        # before doing anything else, we'll clean up the curves!
        rebuild = kw.get('rebuild', False)
        if rebuild:
            for curve in self.curves:
                self.destroyCurve(curve)
            self.curves = None

        super().buildFromObject( objectDesc, **kw)

        # WARNING: edm uses npts as a vague suggestion, pyedm uses as a true limit.
        # This isn't compatible enough.
        self.npts = objectDesc.getProperty("nPts", 100)
        updateTimerMs = objectDesc.getProperty("updateTimerMs", 0)
        if not rebuild:
            # avoid a race condition where this isn't set and a callback occurs before the timer start
            self.updateTimerMs = updateTimerMs
        self.gridColorInfo = self.findColor( "gridColor", palette=(QPalette.Text,))
        self.gridColorInfo.setColor()

        plotMode = objectDesc.getProperty("plotMode")   # plotNPtsAndStop, plotLastNPts (0, 1)
        xAxisTimeFormat = objectDesc.getProperty("xAxisTimeFormat") # 'seconds', 'dateTime'
        plotTitle = objectDesc.getProperty("graphTitle", "")
        self.border = objectDesc.checkProperty("border")
        self.axisInfo("x", objectDesc)
        self.axisInfo("y", objectDesc)
        self.axisInfo("y2", objectDesc)

        self.numCurves = self.objectDesc.getProperty("numTraces", 0)

        self.xPv           = self.objectDesc.getProperty("xPv", arrayCount=self.numCurves)                # optional list of X-axis PV's
        self.yPv           = self.objectDesc.getProperty("yPv", arrayCount=self.numCurves)                # optional(?) list of Y-axis PV's
        self.plotStyle     = self.objectDesc.getProperty("plotStyle", arrayCount=self.numCurves)          # line, point needle, 'single point'
        self.plotUpdateMode= self.objectDesc.getProperty("plotUpdateMode", arrayCount=self.numCurves)     # xAndY, xOrY, x, y, trigger
        self.plotSymbolType= self.objectDesc.getProperty("plotSymbolType", arrayCount=self.numCurves)     # none, circle, square, diamond
        self.opMode        = self.objectDesc.getProperty("opMode", arrayCount=self.numCurves)             # scope, plot
        self.useY2Axis     = self.objectDesc.getProperty("useY2Axis", arrayCount=self.numCurves)          #
        self.xSigned       = self.objectDesc.getProperty("xSigned", arrayCount=self.numCurves)            #
        self.ySigned       = self.objectDesc.getProperty("ySigned", arrayCount=self.numCurves)            #
        self.plotColor     = self.objectDesc.getProperty("plotColor", arrayCount=self.numCurves)          # 'index' and number
        self.lineThickness = self.objectDesc.getProperty("lineThickness", arrayCount=self.numCurves, defValue=1)       # integers
        self.lineStyle     = self.objectDesc.getProperty("lineStyle", arrayCount=self.numCurves, defValue="solid")     # solid, dash

        # X-axis
        if self.showXAxis:
            self.showAxis("bottom")
            axis = self.getAxis("bottom")
            axis.setPen(self.fgColorInfo.setColor())
            axis.setTextPen(self.fgColorInfo.setColor())
            #axis.setTickPen(self.gridColorInfo.setColor())
            axis.setStyle( tickFont=self.edmFont, tickLength=10)

            if self.xLabel:
                self.setLabel( "bottom", toHTML(self.edmFont, self.xLabel ))

            if self.xAxisSrc == self.srcEnum.fromUser:
                # print 'xAxisSrc=', self.xMin, self.xMax
                self.setXRange(  self.xMin, self.xMax, padding=0.0 )

            if self.xShowLabelGrid:
                self.showGrid(x=True)
        else:
            self.hideAxis("bottom")

        # Y-axis
        if self.showYAxis:
            self.showAxis( "left")
            axis = self.getAxis("left")
            axis.setPen(self.fgColorInfo.setColor())
            axis.setTextPen(self.fgColorInfo.setColor())
            #axis.setTickPen( self.gridColorInfo.setColor())
            axis.setStyle( tickFont=self.edmFont, tickLength=10)

            if self.yLabel:
                self.setLabel( "left", toHTML(self.edmFont, self.yLabel ))

            if self.yAxisSrc == self.srcEnum.fromUser:
                self.setYRange( self.yMin, self.yMax, padding=0.0 )

            if self.yShowLabelGrid:
                self.showGrid(y=True)
        else:
            self.hideAxis("left")

        # Y2-axis
        if self.showY2Axis:
            if rebuild:
                y2 = self.y2
            else:
                y2 = pgraph.ViewBox()
                self.y2 = y2
                self.scene().addItem(y2)
            # code copied from https://stackoverflow.com/questions/23679159/two-y-scales-in-pyqtgraph-twinx-like
            self.showAxis("right")
            axis = self.getAxis("right")
            axis.linkToView(y2)
            axis.setPen(self.fgColorInfo.setColor())
            axis.setTextPen(self.fgColorInfo.setColor())
            axis.setStyle( tickFont=self.edmFont, tickLength=10)

            if self.y2Label:
                self.setLabel("right", toHTML(self.edmFont, self.y2Label))
            axis.setGrid(False)     # both y2 and y grid makes a messy display
            y2.setXLink(self.getViewBox())
            if self.y2AxisSrc == self.srcEnum.fromUser:
                y2.setYRange( self.y2Min, self.y2Max, padding=0.0 )
        else:
            self.hideAxis("right")

        # title
        self.setFont(self.edmFont)
        fm = QFontInfo(self.edmFont)
        args = { "color" : f"{self.fgColorInfo.setColor().name()}", "size" : f"{fm.pointSize()}", "bold" : fm.bold(), "italic" : fm.italic() }
        self.setTitle( toHTML(self.edmFont, plotTitle), **args)
        #
        # Build the curves that will be used
        self.curves = [None]*self.numCurves
        ypen, y2pen = False, False
        for idx in range(0, self.numCurves):
            self.buildCurve(idx, rebuild=False)     # rebuild not working yet...
            # check to see if axis text should use this plot color.
            #
            if self.showYAxis and self.useY2Axis[idx] == False and ypen == False:
                self.getAxis("left").setTextPen(self.plotColor[idx].getColor())
                ypen = True
            elif self.showY2Axis and self.useY2Axis[idx] == True and y2pen == False:
                self.getAxis("right").setTextPen(self.plotColor[idx].getColor())
                y2pen = True

        self.xaxisInstance.setTickLabelMode(mode=self.xAxisStyle.value)
        if self.xAxisStyle.value >= 2:      # If we're doing a "time" x-axis, then track seconds since we started.
            self.clockStart = time.time()   # seconds since epoch, count seconds for this display.

        if self.xAxisStyle.value == 1 or self.xAxisStyle.value == 3:    # log(x), log(time)
            self.getAxis("bottom").setLogMode(True)
        else:
            self.getAxis("bottom").setLogMode(False)

        if self.yAxisStyle.value == 1 or self.yAxisStyle.value == 3:
            self.getAxis("left").setLogMode(True)
        else:
            self.getAxis("left").setLogMode(False)

        if self.y2AxisStyle.value == 1 or self.y2AxisStyle.value == 3:
            self.getAxis("right").setLogMode(True)
        else:
            self.getAxis("right").setLogMode(False)

        '''
        # definition of updateTimerMs: forces data with time along
        # x axis to update every <specified> milliseconds (as opposed to waiting to redraw)
        # basically polling -- doesn't keep any extra data points that may have come in,
        if y hasn't changed then plots last point.
        '''

        if rebuild and self.updateTimerMs != 0 and self.timerID != None:
            self.killTimer(self.timerID)
            self.timerID = None

        self.updateTimerMs = updateTimerMs
        if self.updateTimerMs != 0:
            self.timerID = self.startTimer(self.updateTimerMs)

    def buildCurve(self, curveIdx,rebuild=False):
        '''
            build a single curve.
            How to preserve plot data when rebuilding? not easily done!

        '''
        if self.debug(1) : print("Generating curve", curveIdx)
        changed = True
        if rebuild:
            curve = self.curves[curveIdx]
            changed = False
            try:
                isY2 = curve in self.y2.allChildren()
            except AttributeError:
                isY2 = False
            if isY2 != self.useY2Axis[curveIdx]:
                changed = True
                if isY2:
                    self.y2.removeItem(curve)
                else:
                    self.removeItem(curve)
            elif self.pvChanged(self.xPv, curveIdx, curve.xPv) or self.pvChanged(self.yPv, curveIdx, curve.yPv):
                changed = True
            elif curve.updateMode != self.plotUpdateMode[curveIdx]:
                changed = True
            elif curve.nPts != self.npts:
                changed = True
        
        if changed:     # original build, or need to replace previous build
            curve =  pgraph.PlotDataItem(name=str(curveIdx)+self.yPv[curveIdx])
            self.curves[curveIdx] = curve
            curve.xPv = None
            curve.yPv = None

        xlog = self.xAxisStyle.value ==1 or self.xAxisStyle.value == 3
        if self.useY2Axis[curveIdx]:
            ylog = self.y2AxisStyle.value == 1 or self.y2AxisStyle.value == 3
        else:
            ylog = self.yAxisStyle.value == 1 or self.yAxisStyle.value == 3

        curve.setLogMode(xlog, ylog)

        curve.updateMode = self.plotUpdateMode[curveIdx]
        curve.lastX = None   # used for xAndY, maybe xOrY(?). If None, no input value
        curve.lastY = None   # ditto
        if self.lineStyle[curveIdx] == self.lineStyleEnum.solid:
            dash = Qt.SolidLine
        else:
            dash = Qt.DashLine
        pen = pgraph.mkPen(color=self.plotColor[curveIdx].getColor(), width=self.lineThickness[curveIdx], style=dash)
        curve.setPen( pen)
        if changed:
            curve.nPts = self.npts
            curve.edmXdata = collections.deque(maxlen=self.npts )
            curve.edmYdata = collections.deque( maxlen=self.npts )

        # if rebuilding, need to remove then add the curve.
        if changed:
            if self.useY2Axis[curveIdx]:
                self.y2.addItem(curve)
            else:
                self.addItem(curve)

        if changed:
            if curve.xPv:
                curve.xPv.del_callback(self)
            curve.xPv = self.pvConnect(self.xPv, curveIdx, self.xDataCallback, ( curve, 0, 0 ) )
        if curve.xPv is None:
            if curve.updateMode == self.updateModeEnum.xAndY:
                curve.updateMode = self.updateModeEnum.y
            elif curve.updateMode == self.updateModeEnum.xOrY:
                curve.updateMode = self.updateModeEnum.y

        if changed:
            if curve.yPv:
                curve.yPv.del_callback(self)
            curve.yPv = self.pvConnect(self.yPv, curveIdx, self.yDataCallback, ( curve, 0, 0 ) )
        if self.debug(): print('xyPlotData build curve', curve.xPv, curve.yPv, curve.updateMode)

    def destroyCurve(self, curve):
        ''' destroyCurve - undo curve connections
        '''
        if curve.yPv:
            curve.yPv.del_callback(self)
        if curve.xPv:
            curve.xPv.del_callback(self)
        try:
            isY2 = curve in self.y2.allChildren()
        except AttributeError:
            isY2 = False
        if isY2:
            self.y2.removeItem(curve)
        else:
            self.removeItem(curve)


    def pvChanged( self, nameList, idx, oldRef):
        if nameList is None or len(nameList) <= idx or nameList[idx] is None or nameList[idx] == "":
            if oldRef == None:
                return False
        prefix, newname = expandPVname(nameList[idx], macroTable=self.findMacroTable())
        return oldRef.getPVname() != '\\'.join([prefix,newname])

    def pvConnect( self, nameList, idx, callback=None, callbackArgs=None):
        if nameList is None or len(nameList) <= idx or nameList[idx] is None or nameList[idx] == "":
            return None
        if self.debug(): print('xyPlotData pvConnect', nameList[idx], callback)
        pv = buildPV( nameList[idx], macroTable=self.findMacroTable())
        pv.add_callback( callback, self, callbackArgs)
        return pv

    def findBgColor(self, *args, **kw):
        edmWidget.findBgColor(self, *args, **kw)
        self.setBackground(self.bgColorInfo.setColor() )

    def axisInfo(self, prefix, objectDesc):
        '''read axis configuration information'''
        try:
            show = { 'x':'showXAxis', 'y':'showYAxis', 'y2':'showY2Axis' }[prefix]
        except:
            print("axisInfo: Bad prefix", prefix)
            return
        setattr(self, show, objectDesc.getProperty(show, 0))
        setattr(self, prefix+"AxisStyle", objectDesc.getProperty(prefix+"AxisStyle", 0))  # "linear", "log10", "time", "log10(time)"
        setattr(self, prefix+"AxisSrc",  objectDesc.getProperty(prefix+"AxisSrc", 0))     # AutoScale, fromUser and fromPv
        setattr(self, prefix+"AxisFormat",  objectDesc.getProperty(prefix+"AxisFormat", 0))
        setattr(self, prefix+"AxisPrecision",  objectDesc.getProperty(prefix+"AxisPrecision", None))  # AutoScale, fromUser and fromPv
        setattr(self, prefix+"Min", objectDesc.getProperty(prefix+"Min", 0))
        setattr(self, prefix+"Max", objectDesc.getProperty(prefix+"Max", 0))
        setattr(self, prefix+"Label", objectDesc.getProperty(prefix+"Label", None))
        setattr(self, prefix+"LabelIntervals", objectDesc.getProperty(prefix+"LabelIntervals", None))
        setattr(self, prefix+"MajorsPerLabel", objectDesc.getProperty(prefix+"MajorsPerLabel", None))
        setattr(self, prefix+"MinorsPerMajor", objectDesc.getProperty(prefix+"MinorsPerMajor", None))
        setattr(self, prefix+"ShowLabelGrid", objectDesc.getProperty(prefix+"ShowLabelGrid", None))
        setattr(self, prefix+"ShowMajorGrid", objectDesc.getProperty(prefix+"ShowMajorGrid", None))
        setattr(self, prefix+"ShowMinorGrid", objectDesc.getProperty(prefix+"ShowMinorGrid", None))

    # NOTE: none of these callbacks, with the exception of 'redisplay' should
    # do anything that would cause the screen to redraw. Instead, the call
    # should be made to global function redisplay(widget) which will queue the
    # call to widget.redisplay to occur during a timer event within thread 0.
    #
    # called when a PV listed as a "y" source updates
    def yDataCallback(self, widget, userArgs=None, **args):
        if self.debug() : print('xyPlotdata yDataCallback', widget, userArgs, args)
        if userArgs is None:
            return
        curve = userArgs[0]

        if self.debug(): print ('... curve.updateMode', curve.updateMode)

        # check to see if trigger on Y
        num = args['count']
        if curve.updateMode == self.updateModeEnum.y:
            # if returning one data point, add it to the data list.
            # if returning an array of points, rewrite the data list
            if num <= 1:
                if curve.edmXdata.maxlen == len(curve.edmXdata):
                    curve.edmXdata.popleft()
                curve.edmYdata.append(args['value'])
            else:
                if curve.edmYdata.maxlen < num:
                    curve.edmYdata = collections.deque(maxlen=num)
                    curve.edmXdata = collections.deque(maxlen=num)
                curve.edmYdata.clear()
                curve.edmYdata.extend([ float(v) for v in args['value'] ])

            if curve.xPv is None:
                if self.xAxisStyle.value >= 2:  # time, log10(time)
                    # plot against time when the y PV updates
                    curve.edmXdata.append( time.time() )
                elif self.xAxisStyle.value < 2: # x, log(x)
                    # auto-generate some x data: regular x or log(x)
                    curve.edmXdata.clear()
                    curve.edmXdata.extend([ xn for xn in range(0, len(curve.edmYdata))] )
                try:
                    if self.updateTimerMs == 0:
                        curve.setData(list(curve.edmXdata),list(curve.edmYdata))
                        redisplay(self)
                except RuntimeError as exc:
                    print(f"monitorXYgraph yDataCallback runtime exception {exc}")
            else:
                # have x data - use X and Y directly
                self.setOneXY(curve)
            return
        # When running "x" or "trigger", just store the value and let the other update handle it.
        #
        curve.lastY = onePVvalue(args['value'], num)
        if curve.updateMode == self.updateModeEnum.trigger or curve.updateMode == self.updateModeEnum.x:
            return

        #when running "xAndY", if we've had two both X and Y PVs update, then plot
        if curve.updateMode == self.updateModeEnum.xAndY:
            if curve.lastX is not None:
                self.setOneXY(curve)
            return

        # when running "xOrY", update what we've got, and redisplay
        if curve.updateMode == self.updateModeEnum.xOrY:
            self.setOneXY(curve)
            return

        # To Do - raise a 'how the heck did I get here?' error

    # called when a PV listed as an "x" source updates
    def xDataCallback(self, widget, userArgs=None, **args):
        if (self.debug()) : print('xyPlotData xDataCallback', widget, userArgs, args)
        if userArgs is None:
            return
        curve = userArgs[0]
        # If returning one data point, add it to the data list.
        # if returning an array of points, rewrite the data list
        # check to see if trigger on X
        try:
            num = args['count']
        except KeyError:
            return

        if curve.updateMode == self.updateModeEnum.x:
            if num <= 1:
                if curve.edmYdata.maxlen == len(curve.edmYdata):
                    curve.edmYdata.popleft()
                curve.edmXdata.append(args['value'])
            else:
                curve.edmXdata.clear()
                curve.edmXdata.extend(args['value'])
            if curve.yPv is None:   # not sure where this case is valid?
                return
            self.setOneXY(curve)
            return

        curve.lastX = onePVvalue(args['value'], num)
        if curve.updateMode == self.updateModeEnum.y or curve.updateMode == self.updateModeEnum.trigger:
            return

        #when running "xAndY", if we've had two both X and Y PVs update, then plot
        if curve.updateMode == self.updateModeEnum.xAndY:
            if curve.lastY is not None:
                self.setOneXY(curve)
            return

        # when running "xOrY", update what we've got, and redisplay
        if curve.updateMode == self.updateModeEnum.xOrY:
            self.setOneXY(curve)
            return

        # To Do - raise a 'how the heck did I get here?' error


    def triggerCallback(self, widget, **args):
        if getattr(self, "curves", None) == None:
            return
        if self.debug() : print('xyPlotData triggerCallback', widget, args)
        for curve in self.curves:
            if curve.updateMode != self.updateModeEnum.trigger:
                continue
            if self.debug() : print(f'xyPlotData triggerCallback curve {curve}\nlastx {curve.lastX},\nlasty {curve.lastY},\nxdata= {curve.edmXdata}\nydata= {curve.edmYdata}')
            if curve.lastX is None:
                if curve.xPv is not None and len(curve.edmXdata) > 0:
                    curve.edmXdata.append(curve.edmXdata[-1])
            else:
                if curve.lastX.count > 1:
                    curve.edmXdata.clear()
                    curve.edmXdata.extend(curve.lastX.value)
                else:
                    curve.edmXdata.append(curve.lastX.value)
                curve.lastX = None

            if curve.lastY is None:
                if curve.yPv is not None and len(curve.edmYdata) > 0:
                    curve.edmYdata.append(curve.edmYdata[-1])
            else:
                if curve.lastY.count != 1:
                    curve.edmYdata.clear()
                    curve.edmYdata.extend([val for val in curve.lastY.value])
                else:
                    curve.edmYdata.append(curve.lastY.value)
                curve.lastY = None

            if len(curve.edmXdata) == 0:
                if len(curve.edmYdata) == 0:
                    continue
            if curve.xPv is None:
                curve.edmXdata.clear()
                curve.edmXdata.extend( list(range(1, len(curve.edmYdata)+1)))
            if curve.yPv is None:
                curve.edmYdata.clear()
                curve.edmYdata.extend(list(range(1, len(curve.edmXdata)+1)))

            try:
                if self.updateTimerMs == 0 and len(curve.edmYdata) > 0 and len(curve.edmXdata) > 0:
                    curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))
            except RuntimeError as exc:
                print(f"monitorXYgraph triggerCallback runtime exception {exc}")


    def setMatchedData(self, curve):
        ''' stretch the shorter of x or y lists out to make the lists equal length.
            If nothing has been defined, then ignore.
        '''
        if len(curve.edmYdata) == 0 or len(curve.edmXdata) == 0:
            return
        diff = len(curve.edmYdata) - len(curve.edmXdata)
        if diff < 0:
            curve.edmYdata.extend([curve.edmYdata[-1]]*-diff)
        elif diff > 0:
            curve.edmXdata.extend([curve.edmXdata[-1]]*diff)
        try:
            if self.updateTimerMs == 0:
                curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))
                redisplay(self)
        except RuntimeError as exc:
            print(f"monitorXYgraph setMatchedData runtime exception {exc}")

    def setOneXY(self, curve):
        '''
            If one or both of the axis is being delayed for update values,
            then add them to the list. 
        '''
        if curve.lastX is not None and curve.lastX.value is not None:
            if curve.lastX.count > 1:
                curve.edmXdata.clear()
                curve.edmXdata.extend(curve.lastX.value)
            else:
                curve.edmXdata.append(curve.lastX.value)
            curve.lastX.value = None

        if curve.lastY is not None:
            if curve.lastY.count > 1:
                curve.edmYdata.clear()
                curve.edmYdata.extend(curve.lastY.value)
            else:
                curve.edmYdata.append(curve.lastY.value)
            curve.lastY = None

        self.setMatchedData(curve)

    def resetCallback(self, widget, **args):
        '''
            edm 105F has ~300 lines of code to reset limits
            for the various curves. Need to determine how much
            of that is relevant to this widget.
        '''
        if getattr(self, "curves",None) == None:
            return
        for curve in self.curves:
            # TO DO: decide what 'reset' means for each type of plot
            pass
        self.clockStart = time.time()
        redisplay(self)

    # called from redisplay on the timer queue. It is safe to redraw here.
    #
    def redisplay(self, **kw):
        if self.debug() : print('xyPlotData redisplay', kw)
        self.checkVisible()
        if hasattr(self, "y2"):
            # not all plots use y2
            self.y2.setGeometry(self.getViewBox().sceneBoundingRect())
            self.y2.linkedViewChanged(self.getViewBox(), self.y2.XAxis)

        self.replot()

    def drawBorder(self):
        ''' unused function - unable to mix the replot with any other drawing.
        '''
        if self.border == False:
            return
        painter = QPainter(self)
        w,h = self.width(), self.height()
        x,y = 0,0
        pen = painter.pen()
        pen.setColor( self.fgColorInfo.setColor())
        painter.setPen(pen)
        painter.drawRect( x, y, w, h)

    def timerEvent(self, e):
        '''
            timerEvent - called if updateTimerMs is non-zero.
            Alternative to redisplaying as-it-happens
        '''
        if self.debug() : print('timerEvent')
        for curve in self.curves:
            if len(curve.edmXdata) > 0 and len(curve.edmYdata) > 0:
                try:
                    curve.setData(list(curve.edmXdata), list(curve.edmYdata))
                except RuntimeError as exc:
                    print(f"monitorXYgraph timerEvent runtime exception {exc}")
        redisplay(self)
        return

edmApp.edmClasses["xyGraphClass"] = xyGraphClass
