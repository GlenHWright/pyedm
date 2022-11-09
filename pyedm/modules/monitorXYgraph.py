from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
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
from .edmField import edmField
from .edmEditWidget import edmEditField, edmEdit

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

    def buildLayout(self):
        layout = QtWidgets.QGridLayout()
        # add column headers, and create the array of values.
        self.colvalue = {}
        for idx, fld in enumerate(self.edmfield.group):
            label = QtWidgets.QLabel(fld.tag)
            label.setFrameShape(QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken)
            layout.addWidget(label, 0, idx)
            self.colvalue[idx] = self.widget.objectDesc.getProperty(fld.tag, arrayCount=self.widget.numCurves)
        
        for row in range(self.widget.numCurves):
            for idx, fld in enumerate(self.edmfield.group):
                tagw = fld.editClass(fld.tag, fld, self.widget, **fld.editKeywords)
                w = tagw.showEditWidget(self.colvalue[idx][row]).nolabel()
                layout.addWidget(w, row+1, idx)
                self.editlist.append(tagw)
                tagw.newValue.connect(lambda tag, value, row=row,col=idx: self.onNewValue(tag,value,row,col))

        return layout

    def onNewValue(self, tag, value, row, col):
        print(f"onNewValue {tag} {value} {row} {col}")
        if tag not in self.newtags.keys():
            self.newtags[tag] = self.colvalue[col].copy()
        self.newtags[tag][row] = value

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

    edmEntityFields = [
            edmField("triggerPv", edmEdit.PV, defaultValue=None),
            edmField("resetPv", edmEdit.PV, defaultValue=None),
            edmField("gridColor", edmEdit.Color, defaultValue=0),
            edmField("numTraces", edmEdit.Int, defaultValue=0),                              # this may need to be invisible and auto generated!
            edmField("Curve Configure", edmEditCurveConfig, group=[
                edmField("xPv", edmEdit.PV, defaultValue=None, array=True),
                edmField("yPv", edmEdit.PV, defaultValue=None, array=True),                  # optional(?) list of Y-axis PV's
                edmField("plotStyle", edmEdit.Enum, defaultValue=0, enumList=plotStyleEnum, array=True),
                edmField("plotUpdateMode", edmEdit.Enum, defaultValue="y", array=True, enumList=updateModeEnum),    # xAndY, xOrY, x, y, trigger
                edmField("plotSymbolType", edmEdit.Enum, defaultValue=None, array=True, enumList=plotSymbolEnum ),
                edmField("opMode", edmEdit.String, defaultValue=None, array=True),           # scope, plot
                edmField("useY2Axis", edmEdit.Bool, defaultValue=False, array=True),         #
                edmField("xSigned", edmEdit.Bool, defaultValue=False, array=True),           #
                edmField("ySigned", edmEdit.Bool, defaultValue=False, array=True),           #
                edmField("plotColor", edmEdit.Color, defaultValue="black", array=True),      # 'index' and number
                edmField("lineThickness", edmEdit.Int, defaultValue=0, array=True),          # integers
                edmField("lineStyle", edmEdit.Enum, defaultValue="solid", array=True, enumList=lineStyleEnum)     # solid, dash
                ] ),
            edmField("plotMode", edmEdit.Enum, enumList=plotModeEnum),
            edmField("graphTitle", edmEdit.String),
            edmField("nPts", edmEdit.Int, defaultValue=100),
            edmField("updateTimerMs", edmEdit.Int, defaultValue=0),
            edmField("showXAxis", edmEdit.Bool, defaultValue=1),
            edmField("unused", edmEdit.HList, group= [
                edmField("xAxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
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
                edmField("xShowMinorGrid", edmEdit.Bool, defaultValue=False),
                edmField("showYAxis", edmEdit.Bool, defaultValue=1)
                ] ),
            edmField("unused", edmEdit.HList, group= [
                edmField("yAxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
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
                edmField("yShowMinorGrid", edmEdit.Bool, defaultValue=False),
                edmField("showY2Axis", edmEdit.Bool, 0)
                ] ),
            edmField("unused", edmEdit.HList, group = [
                edmField("y2AxisStyle", edmEdit.Enum, defaultValue="linear", enumList=styleEnum),  # "linear", "log10", "time", "log10(time)"
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
        super().edmCleanup()
        for curve in self.curves:
            if curve.xPv:
                curve.xPv.del_callback(self)
            if curve.yPv:
                curve.yPv.del_callback(self)

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
        super().buildFromObject( objectDesc, **kw)
        rebuild = kw.get('rebuild', False)

        # WARNING: edm uses npts as a vague suggestion, pyedm uses as a true limit.
        # This isn't compatible enough.
        npts = objectDesc.getProperty("nPts", 100)
        updateTimerMs = objectDesc.getProperty("updateTimerMs", 0)
        if not rebuild:
            # avoid a race conditin where this isn't set and a callback occurs before the timer start
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

        xPv           = self.objectDesc.getProperty("xPv", arrayCount=self.numCurves)                # optional list of X-axis PV's
        yPv           = self.objectDesc.getProperty("yPv", arrayCount=self.numCurves)                # optional(?) list of Y-axis PV's
        plotStyle     = self.objectDesc.getProperty("plotStyle", arrayCount=self.numCurves)          # enumerated list - line, point needle, 'single point'
        plotUpdateMode= self.objectDesc.getProperty("plotUpdateMode", arrayCount=self.numCurves)     # xAndY, xOrY, x, y, trigger
        plotSymbolType= self.objectDesc.getProperty("plotSymbolType", arrayCount=self.numCurves)     # none, circle, square, diamond
        opMode        = self.objectDesc.getProperty("opMode", arrayCount=self.numCurves)             # scope, plot
        useY2Axis     = self.objectDesc.getProperty("useY2Axis", arrayCount=self.numCurves)          #
        xSigned       = self.objectDesc.getProperty("xSigned", arrayCount=self.numCurves)            #
        ySigned       = self.objectDesc.getProperty("ySigned", arrayCount=self.numCurves)            #
        plotColor     = self.objectDesc.getProperty("plotColor", arrayCount=self.numCurves)          # 'index' and number
        lineThickness = self.objectDesc.getProperty("lineThickness", arrayCount=self.numCurves, defValue=1)       # integers
        lineStyle     = self.objectDesc.getProperty("lineStyle", arrayCount=self.numCurves, defValue="solid")     # solid, dash

        # X-axis
        if self.showXAxis:
            self.showAxis("bottom")
            axis = self.getAxis("bottom")
            axis.setPen(self.fgColorInfo.setColor())
            axis.setTextPen(self.fgColorInfo.setColor())
            #axis.setTickPen(self.gridColorInfo.setColor())
            axis.setStyle( tickFont=self.edmFont, tickLength=10)

            if self.xLabel:
                self.setLabel( "bottom", self.xLabel )

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
                self.setLabel( "left", self.yLabel )

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
                self.setLabel("right", self.y2Label)
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
        self.setTitle( plotTitle, **args)
        #
        # Build the curves that will be used
        if not rebuild:
            self.curves = []
        for idx in range(0, self.numCurves):
            if self.debug(0) : print("Generating curve", idx)
            if rebuild and idx < len(self.curves):
                curve = self.curves[idx]
            else:
                curve =  pgraph.PlotCurveItem(name=str(idx)+yPv[idx])
                self.curves.append( curve)
                curve.xPv = None
                curve.yPv = None
            curve.updateMode = plotUpdateMode[idx]
            curve.lastX = None   # used for xAndY, maybe xOrY(?). If None, no input value
            curve.lastY = None   # ditto
            if lineStyle is None or lineStyle[idx].value == 0:
                dash = Qt.SolidLine
            else:
                dash = Qt.DashLine
            pen = pgraph.mkPen(color=plotColor[idx].getColor(), width=1 if lineThickness is None or lineThickness[idx] is None else lineThickness[idx], style=dash)
            curve.setPen( pen)
            if (not rebuild) or curve.nPts != npts:
                curve.nPts = npts
                curve.edmXdata = collections.deque(maxlen=npts )
                curve.edmYdata = collections.deque( maxlen=npts )

            if not rebuild:
                if useY2Axis and useY2Axis[idx]:
                    y2.addItem(curve)
                else:
                    self.addItem(curve)

            if (not rebuild) or self.pvChanged(xPv, idx, curve.xPv):
                if curve.xPv:
                    curve.xPv.del_callback(self)
                curve.xPv = self.pvConnect(xPv, idx, self.xDataCallback, ( curve, 0, 0 ) )
            if curve.xPv is None:
                if curve.updateMode == self.updateModeEnum.xAndY:
                    curve.updateMode = self.updateModeEnum.y
                elif curve.updateMode == self.updateModeEnum.xOrY:
                    curve.updateMode = self.updateModeEnum.y
            if (not rebuild) or self.pvChanged(yPv, idx, curve.yPv):
                if curve.yPv:
                    curve.yPv.del_callback(self)
                curve.yPv = self.pvConnect(yPv, idx, self.yDataCallback, ( curve, 0, 0 ) )
            if self.debug(): print('xyPlotData build curve', curve.xPv, curve.yPv, curve.updateMode)

        self.xaxisInstance.setTickLabelMode(mode=self.xAxisStyle.value)
        if self.xAxisStyle.value == 2:    # If we're doing a "time" x-axis, then track seconds since we started.
            self.clockStart = time.time()   # seconds since epoch, count seconds for this display.

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
                    curve.edmYdata = deque(maxlen=num)
                    curve.edmXdata = deque(maxlen=num)
                curve.edmYdata.clear()
                curve.edmYdata.extend([ float(v) for v in args['value'] ])

            if curve.xPv is None:
                if self.xAxisStyle == self.styleEnum.time:
                    # plot against time when the y PV updates
                    curve.edmXdata.append( time.time() )
                elif self.xAxisStyle.value < 2:
                    # auto-generate some x data: regular x or log(x)
                    curve.edmXdata.clear()
                    curve.edmXdata.extend([ xn for xn in range(0, len(curve.edmYdata))] )
                if self.updateTimerMs == 0:
                    curve.setData(list(curve.edmXdata),list(curve.edmYdata))
                    redisplay(self)
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
        if self.debug() : print('xyPlotData triggerCallback', widget, args)
        if hasattr(self, "curves") == 0:
            return
        for curve in self.curves:
            if curve.updateMode != self.updateModeEnum.trigger:
                continue
            if self.debug() : print(f'xyPlotData curve {curve.lastX}, {curve.lastY}, {curve.edmXdata} {curve.edmYdata}')
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

            if self.updateTimerMs == 0:
                curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))

        if self.updateTimerMs == 0:
            redisplay(self)

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
        if self.updateTimerMs == 0:
            curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))
            redisplay(self)

    def setOneXY(self, curve):
        '''
            If one or both of the axis is being delayed for update values,
            then add them to the list. 
        '''
        if curve.lastX is not None:
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
            for the various curves. 
        '''
        if hasattr(self, "curves") == 0:
            return
        for curve in self.curves:
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
                curve.setData(list(curve.edmXdata), list(curve.edmYdata))
        redisplay(self)
        return

edmApp.edmClasses["xyGraphClass"] = xyGraphClass
