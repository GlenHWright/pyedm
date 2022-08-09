from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module to display an XY graph

import sys
from builtins import str
from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmPVfactory import buildPV
from pyedm.edmApp import redisplay
from pyedm.edmWidget import edmWidget

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QPalette, QFontMetrics
import pyqtgraph as pgraph
# from Exceptions import AttributeError

import collections
import time

class xAxisClass(pgraph.AxisItem):
    def setTickLabelMode(self, mode="linear", base=0):
        '''
        sets the labelling mode for the x axis. This matches the edm
        modes of "linear", "log10", "time", "log10(time)"
        base of 0 (timestamp) or 1 (seconds before now)
        '''
        self.tickMode = { "linear":0, "log":1, "time":2, "log10(time)":3 }[mode]
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

class xyGraphClass(pgraph.PlotWidget, edmWidget):
    def __init__(self, parent=None, *args):
        self.xaxisInstance =  xAxisClass(orientation="bottom") 
        axisArg = { "bottom": self.xaxisInstance }
        super().__init__(parent, *args, axisItems=axisArg)
        self.pvItem["triggerPv"] = [ 'triggerName', 'triggerPV', 0, self.triggerCallback, None ]
        self.pvItem["resetPv"]   = [ 'resetName', 'resetPV', 0, self.resetCallback, None ]
        # self.DebugFlag = 1

    def __getattr__(self, attr):    ## workaround for bug in PlotWidget __getattr__() which uses NameError instead of AttributeError
        if hasattr(self.plotItem, attr):
            m = getattr(self.plotItem, attr)
            if hasattr(m, '__call__'):
                return m
        raise AttributeError(attr)

    def cleanup(self):
        edmWidget.cleanup(self)
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
            
    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self, objectDesc)

        npts = objectDesc.getIntProperty("nPts", 100)
        self.updateTimerMs = objectDesc.getIntProperty("updateTimerMs", 0)
        self.gridColorInfo = self.findColor( "gridColor", palette=(QPalette.Text,))
        self.gridColorInfo.setColor()

        plotMode = objectDesc.getStringProperty("plotMode", "plotNPtsAndStop")   # plotNPtsAndStop, plotLastNPts (0, 1)
        xAxisTimeFormat = objectDesc.getStringProperty("xAxisTimeFormat", None) # 'seconds', 'dateTime'
        plotTitle = objectDesc.getStringProperty("graphTitle", "")
        self.axisInfo("x", objectDesc)
        self.axisInfo("y", objectDesc)
        self.axisInfo("y2", objectDesc)
        
        # Grid - change this to be based on file settings
        # grid = qwt.plot.QwtPlotGrid()
        # grid.attach(self)
        # grid.setPen(Qt.QPen(Qt.black, 0, Qt.DotLine))

        # X-axis
        self.showAxis("bottom")
        if self.xLabel:
            self.setLabel( "bottom", self.xLabel )

        if self.xAxisSrc == "fromUser":
            # print 'xAxisSrc=', self.xMin, self.xMax
            self.setXRange(  self.xMin, self.xMax )

        # Y-axis
        self.showAxis( "left")
        if self.yLabel:
            self.setLabel( "left", self.yLabel )

        if self.yAxisSrc == "fromUser":
            self.setYRange( self.yMin, self.yMax )

        # title
        self.setTitle( plotTitle )

        self.numCurves = self.objectDesc.getIntProperty("numTraces", 0)

        xPv      = self.objectDesc.decode("xPv", self.numCurves)                    # optional list of X-axis PV's
        yPv      = self.objectDesc.decode("yPv", self.numCurves)                    # optional(?) list of Y-axis PV's
        plotStyle= self.objectDesc.decode("plotStyle", self.numCurves)              # enumerated list - line, point needle, 'single point'
        plotUpdateMode= self.objectDesc.decode("plotUpdateMode", self.numCurves)    # xAndY, xOrY, x, y, trigger
        plotSymbolType= self.objectDesc.decode("plotSymbolType", self.numCurves)    # none, circle, square, diamond
        opMode   = self.objectDesc.decode("opMode", self.numCurves)                 # scope, plot
        useY2Axis= self.objectDesc.decode("useY2Axis", self.numCurves)              #
        xSigned  = self.objectDesc.decode("xSigned", self.numCurves)                #
        ySigned  = self.objectDesc.decode("ySigned", self.numCurves)                #
        plotColor= self.objectDesc.decode("plotColor", self.numCurves)              # 'index' and number
        lineThickness = self.objectDesc.decode("lineThickness", self.numCurves, 0)  # integers
        lineStyle= self.objectDesc.decode("lineStyle", self.numCurves, "solid")     # solid, dash
        #
        # Build the curves that will be used
        self.curves = []
        for idx in range(0, self.numCurves):
            if self.DebugFlag > 0 : print("Generating curve", idx)
            curve =  self.plot(name=str(idx)+yPv[idx])
            self.curves.append( curve)
            # curve.attach(self)
            curve.yPvName = yPv[idx]
            curve.xPv = self.pvConnect(xPv, idx, self.xDataCallback, ( curve, 0, 0 ) )
            curve.yPv = self.pvConnect(yPv, idx, self.yDataCallback, ( curve, 0, 0 ) )
            curve.updateMode = plotUpdateMode[idx] if plotUpdateMode != None else "y" if curve.xPv == None else "xAndY"
            if lineStyle is None or lineStyle[idx] == "solid":
                dash = Qt.SolidLine
            else:
                dash = Qt.DashLine
            pen = pgraph.mkPen(color=plotColor[idx].getColor(), width=1 if lineThickness is None or lineThickness[idx] is None else lineThickness[idx], style=dash)
            curve.setPen( pen)
            curve.nPts = npts
            curve.edmXdata = collections.deque(maxlen=npts )
            curve.edmYdata = collections.deque( maxlen=npts )
            if self.DebugFlag > 0: print('xyPlotData build curve', curve.xPv, curve.yPv, curve.updateMode)

        self.xaxisInstance.setTickLabelMode(mode=self.xAxisStyle)
        if self.xAxisStyle == "time":    #
            if self.updateTimerMs == 0:
                self.clockStart = time.time()   # seconds since epoch
                # self.setAxisScaleDraw(qwt.plot.QwtPlot.xBottom, AbsTimeScaleDraw(self))
            else:
                pass
                # self.axisScaleEngine( qwt.plot.QwtPlot.xBottom ).setAttribute( Qwt.QwtScaleEngine.Inverted )
                # self.setAxisScaleDraw(qwt.plot.QwtPlot.xBottom, TimeScaleDraw(time.time()))

        print(self.xLabelIntervals)

        '''
        THIS IS UNUSED CODE
        if self.xLabelIntervals != None:
            medium = self.xMajorsPerLabel
            minor = self.xMinorsPerMajor
            print self.xLabelIntervals, medium, minor
            self.setAxisMaxMajor( qwt.plot.QwtPlot.xBottom, self.xLabelIntervals+1)
            if minor != None:
                self.setAxisMaxMinor( qwt.plot.QwtPlot.xBottom, minor)
        # Change of definition of updateTime: now being used to force data with time along
        # x axis to update every <specified> milliseconds (as opposed to waiting to redraw)
        # basically polling (doesn't keep any extra data points that may have come in)
        END OF UNUSED CODE SECTION
        '''

        if self.updateTimerMs != 0:
            self.startTimer(self.updateTimerMs)

    def pvConnect( self, nameList, idx, callback=None, callbackArgs=None):
        if nameList == None or len(nameList) <= idx or nameList[idx] == None:
            return None
        if self.DebugFlag > 0: print('xyPlotData pvConnect', nameList[idx], callback)
        pv = buildPV( nameList[idx], macroTable=self.findMacroTable())
        pv.add_callback( callback, self, callbackArgs)
        return pv

#    def findFgColor(self):
#        edmWidget.findFgColor(self, fgcolor="gridColor", palette=(QPalette.Text,))
#
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
        setattr(self, show, objectDesc.getIntProperty(show, 0))
        setattr(self, prefix+"AxisStyle", objectDesc.getStringProperty(prefix+"AxisStyle", "linear"))  # "linear", "log10", "time", "log10(time)"
        setattr(self, prefix+"AxisSrc",  objectDesc.getStringProperty(prefix+"AxisSrc", None))     # AutoScale, fromUser and fromPv
        setattr(self, prefix+"AxisFormat",  objectDesc.getStringProperty(prefix+"AxisFormat", None))        # AutoScale, fromUser and fromPv
        setattr(self, prefix+"AxisPrecision",  objectDesc.getStringProperty(prefix+"AxisPrecision", None))  # AutoScale, fromUser and fromPv
        setattr(self, prefix+"Min", objectDesc.getDoubleProperty(prefix+"Min", 0))
        setattr(self, prefix+"Max", objectDesc.getDoubleProperty(prefix+"Max", 0))
        setattr(self, prefix+"Label", objectDesc.getStringProperty(prefix+"Label", None))
        setattr(self, prefix+"LabelIntervals", objectDesc.getIntProperty(prefix+"LabelIntervals", None))
        setattr(self, prefix+"MajorsPerLabel", objectDesc.getIntProperty(prefix+"MajorsPerLabel", None))
        setattr(self, prefix+"MinorsPerMajor", objectDesc.getIntProperty(prefix+"MinorsPerMajor", None))
        setattr(self, prefix+"ShowLabelGrid", objectDesc.getIntProperty(prefix+"ShowLabelGrid", None))
        setattr(self, prefix+"ShowMajorGrid", objectDesc.getIntProperty(prefix+"ShowMajorGrid", None))
        setattr(self, prefix+"ShowMinorGrid", objectDesc.getIntProperty(prefix+"ShowMinorGrid", None))

    # NOTE: none of these callbacks, with the exception of 'redisplay' should
    # do anything that would cause the screen to redraw. Instead, the call
    # should be made to global function redisplay(widget) which will queue the
    # call to widget.redisplay to occur during a timer event within thread 0.
    #
    # called when a PV listed as a "y" source updates
    def yDataCallback(self, widget, userArgs=None, **args):
        if self.DebugFlag > 0 : print('xyPlotdata yDataCallback', widget, userArgs, args)
        if userArgs == None:
            return
        curve = userArgs[0]
        if self.DebugFlag > 0: print ('... curve.updateMode', curve.updateMode)
        # To Do : if returning one data point, add it to the data list.
        # if returning an array of points, rewrite the data list
        # check to see if trigger on Y
        num = args['count']
        if num <= 1:
            curve.edmYdata.append(args['value'])
        else:
            curve.edmYdata = [ float(v) for v in args['value'] ]
        if curve.updateMode in [ "y", "xOrY" ]:
            if curve.xPv == None:
                if self.xAxisStyle == "time" and self.updateTimerMs == 0:
                    # plot against time, but only when the y PV updates
                    curve.edmXdata.append( time.time() )
                    curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata) )
                    redisplay(self)
                elif self.xAxisStyle != "time":
                    # auto-generate some x data
                    curve.edmXdata = [ xn for xn in range(0, len(curve.edmYdata)) ]
                    curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata) )
                    redisplay(self)
            else:
                # have x data - use X and Y directly
                curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata) )
                redisplay(self)

    # called when a PV listed as an "x" source updates
    def xDataCallback(self, widget, userArgs=None, **args):
        if self.DebugFlag > 0 : print('xyPlotData xDataCallback', widget, userArgs, args)
        if userArgs == None:
            return
        curve = userArgs[0]
        # To Do : if returning one data point, add it to the data list.
        # if returning an array of points, rewrite the data list
        # check to see if trigger on Y
        num = args['count']
        if num <= 1:
            curve.edmXdata.append(args['value'])
        else:
            curve.edmXdata = [ float(v) for v in args['value'] ]
        if curve.updateMode in [ "x", "xOrY" ] and self.updateTimerMs is None:
            if curve.yPv == None:
                return
            curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))
            redisplay(self)

    def triggerCallback(self, widget, **args):
        if self.DebugFlag > 0 : print('xyPlotData triggerCallback', widget, args)
        if hasattr(self, "curves") == 0:
            return
        for curve in self.curves:
            if curve.updateMode != 'trigger':
                continue
            if curve.edmXdata == [] :
                if curve.edmYdata == [] :
                    continue
                curve.edmXdata = list(range(1, len(curve.edmYdata)+1))
            else:
                if curve.edmYdata == [] :
                    curve.edmYdata = list(range(1, len(curve.edmXdata)+1))
            #curve.setData(curve.edmXdata, curve.edmYdata )
        
            curve.setData(x=list(curve.edmXdata), y=list(curve.edmYdata))
        redisplay(self)

    def resetCallback(self, widget, **args):
        if hasattr(self, "curves") == 0:
            return
        for curve in self.curves:
            curve.setData(x=[], y=[])
        redisplay(self)

    # called from redisplay on the timer queue. It is safe to redraw here.
    #
    def redisplay(self, **kw):
        if self.DebugFlag > 0 : print('xyPlotData redisplay', kw)
        self.checkVisible()
        self.replot()

    def timerEvent(self, e):
        if self.DebugFlag > 0 : print('timerEvent')
        for curve in self.curves:
            if len(curve.edmYdata) == 0:
                return

            newYpts = len(curve.edmYdata) - len(curve.edmXdata)
            if newYpts == 0:  # No y point came in during the interval, copy last one, which is on the front
                curve.edmYdata.append(curve.edmYdata[len(curve.edmYdata) - 1])
            elif newYpts > 1: #ditch all the data points except the last one, since don't have time stamps for them
                #well we could do now but tough, just use the timer to poll
                recentYval = curve.edmYdata.pop()
                newYpts -= 1
                while newYpts > 0:
                    curve.edmYdata.pop()
                    newYpts -= 1
                curve.edmYdata.append(recentYval)

            # reverse the Y data, so can move back in time, with 0 being "now"
            # TODO: when move to python 2.7, can do this in place
            reversedYdata = []
            for yPt in reversed( curve.edmYdata ):
                reversedYdata.append(yPt)

            curve.edmXdata = [ xn * self.updateTimerMs / 1000    for xn in range(0, len(curve.edmYdata)) ]

            curve.setData(list(curve.edmXdata), list(reversedYdata))
            self.replot()

edmDisplay.edmClasses["xyGraphClass"] = xyGraphClass
