from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module to display an XY graph

from builtins import str
from builtins import range
import pyedm.edmDisplay as edmDisplay
from pyedm.edmPVfactory import buildPV
from pyedm.edmApp import redisplay
from pyedm.edmWidget import edmWidget

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPen, QPalette, QFontMetrics
import PyQt4.Qwt5 as Qwt

import collections
import time

# Copied this from some other code. I don't know why it is needed.
class xyGraphAxis(Qwt.QwtPlotItem):
    def __init__(self, masterAxis, slaveAxis):
        Qwt.QwtPlotItem.__init__(self)

    def draw(self):
        pass

class TimeScaleDraw(Qwt.QwtScaleDraw):
    def __init__(self, baseTime, *args):
        Qwt.QwtScaleDraw.__init__(self, *args)
        self.baseTime = baseTime

    def label(self, value):
        #timeMarker = self.baseTime + value
        timeParts = time.gmtime(value)
        hours = timeParts[3]; mins = timeParts[4]; secs = timeParts[5]
        if hours == 0:
            if mins == 0 and secs == 0:
                timeString = ("00:00")
            else:
                timeString = time.strftime("-%M:%S",timeParts)
        else:
            timeString = time.strftime("-%H:%M:%S", timeParts)
        return Qwt.QwtText(timeString)

class AbsTimeScaleDraw(Qwt.QwtScaleDraw):
    def __init__(self, plot=None, *args):
        Qwt.QwtScaleDraw.__init__(self, *args)
        self.plot = plot
        self.baseTime = time.time()

    def label(self, value):
        text = Qwt.QwtText( time.strftime("%H:%M:%S", time.localtime(value)))
        return text
        
class xyGraphClass(Qwt.QwtPlot,edmWidget):
    def __init__(self, parent=None, *args):
        Qwt.QwtPlot.__init__(self,  parent, *args)
        edmWidget.__init__(self, parent)
        self.pvItem["triggerPv"] = [ 'triggerName', 'triggerPV', 0, self.triggerCallback, None ]
        self.pvItem["resetPv"]   = [ 'resetName', 'resetPV', 0, self.resetCallback, None ]
        # self.DebugFlag = 1

    def cleanup(self):
        edmWidget.cleanup(self)
        for curve in self.curves:
            curve.pv.del_callback(self)

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
            
    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)

        npts = object.getIntProperty("nPts", 100)
        self.updateTimerMs = object.getIntProperty("updateTimerMs", None)
        self.gridColorInfo = self.findColor( "gridColor", palette=(QPalette.Text,))
        self.gridColorInfo.setColor()

        plotMode = object.getStringProperty("plotMode", "linear")
        xAxisTimeFormat = object.getStringProperty("xAxisTimeFormat", None) # 'seconds', 'dateTime'
        plotTitle = object.getStringProperty("graphTitle", "")
        self.axisInfo("x", object)
        self.axisInfo("y", object)
        self.axisInfo("y2", object)
        
        # Grid - change this to be based on file settings
        # grid = Qwt.QwtPlotGrid()
        # grid.attach(self)
        # grid.setPen(Qt.QPen(Qt.black, 0, Qt.DotLine))

        # X-axis
        self.enableAxis( Qwt.QwtPlot.xBottom, True )
        if self.xLabel:
            self.setAxisTitle( Qwt.QwtPlot.xBottom, self.xLabel )

        if self.xAxisSrc == "fromUser":
            print('xAxisSrc=', self.xMin, self.xMax)
            self.setAxisScale( Qwt.QwtPlot.xBottom, self.xMin, self.xMax )

        # Y-axis
        self.enableAxis( Qwt.QwtPlot.yLeft, True)
        if self.yLabel:
            self.setAxisTitle( Qwt.QwtPlot.yLeft, self.yLabel )

        if self.yAxisSrc == "fromUser":
            self.setAxisScale( Qwt.QwtPlot.yLeft, self.yMin, self.yMax )

        # title
        self.setTitle( plotTitle )

        self.numCurves = self.object.getIntProperty("numTraces", 0)

        xPv      = self.object.decode("xPv", self.numCurves)                    # optional list of X-axis PV's
        yPv      = self.object.decode("yPv", self.numCurves)                    # optional(?) list of Y-axis PV's
        plotStyle= self.object.decode("plotStyle", self.numCurves)              # enumerated list - line, point needle, 'single point'
        plotUpdateMode= self.object.decode("plotUpdateMode", self.numCurves)    # xAndY, xOrY, x, y, trigger
        plotSymbolType= self.object.decode("plotSymbolType", self.numCurves)    # none, circle, square, diamond
        opMode   = self.object.decode("opMode", self.numCurves)                 # scope, plot
        useY2Axis= self.object.decode("useY2Axis", self.numCurves)              #
        xSigned  = self.object.decode("xSigned", self.numCurves)                #
        ySigned  = self.object.decode("ySigned", self.numCurves)                #
        plotColor= self.object.decode("plotColor", self.numCurves)              # 'index' and number
        lineThickness = self.object.decode("lineThickness", self.numCurves, 1)  # integers
        lineStyle= self.object.decode("lineStyle", self.numCurves, "solid")     # solid, dash
        #
        # Build the curves that will be used
        self.curves = []
        for idx in range(0, self.numCurves):
            curve =  Qwt.QwtPlotCurve(str(idx)+yPv[idx])
            self.curves.append( curve)
            curve.attach(self)
            curve.yPvName = yPv[idx]
            curve.xPv = self.pvConnect(xPv, idx, self.xDataCallback, ( curve, 0, 0 ) )
            curve.yPv = self.pvConnect(yPv, idx, self.yDataCallback, ( curve, 0, 0 ) )
            curve.updateMode = plotUpdateMode[idx] if plotUpdateMode != None else "y" if curve.xPv == None else "xAndY"
            curve.setPen(QPen(plotColor[idx].getColor(), 1 if lineThickness is None or lineThickness[idx] is None else lineThickness[idx],
                Qt.SolidLine if lineStyle is None or lineStyle[idx] == "solid" else Qt.DashLine))
            curve.nPts = npts
            curve.edmXdata = collections.deque(maxlen=npts )
            curve.edmYdata = collections.deque( maxlen=npts )
            if self.DebugFlag > 0: print('xyPlotData build curve', curve.xPv, curve.yPv, curve.updateMode)

        if self.xAxisStyle == "time":
            if self.updateTimerMs is None:
                self.clockStart = time.time()   # seconds since epoch
                self.setAxisScaleDraw(Qwt.QwtPlot.xBottom, AbsTimeScaleDraw(self))
            else:
                self.axisScaleEngine( Qwt.QwtPlot.xBottom ).setAttribute( Qwt.QwtScaleEngine.Inverted )
                self.setAxisScaleDraw(Qwt.QwtPlot.xBottom, TimeScaleDraw(time.time()))

        print(self.xLabelIntervals)
        if self.xLabelIntervals != None:
            medium = self.xMajorsPerLabel
            minor = self.xMinorsPerMajor
            print(self.xLabelIntervals, medium, minor)
            self.setAxisMaxMajor( Qwt.QwtPlot.xBottom, self.xLabelIntervals+1)
            if minor != None:
                self.setAxisMaxMinor( Qwt.QwtPlot.xBottom, minor)
        # Change of definition of updateTime: now being used to force data with time along
        # x axis to update every <specified> milliseconds (as opposed to waiting to redraw)
        # basically polling (doesn't keep any extra data points that may have come in)
        if self.updateTimerMs is not None:
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
    def axisInfo(self, prefix, object):
        '''read axis configuration information'''
        try:
            show = { 'x':'showXAxis', 'y':'showYAxis', 'y2':'showY2Axis' }[prefix]
        except:
            print("axisInfo: Bad prefix", prefix)
            return
        setattr(self, show, object.getIntProperty(show, 0))
        setattr(self, prefix+"AxisStyle", object.getStringProperty(prefix+"AxisStyle", None))  # only care about time and linear
        setattr(self, prefix+"AxisSrc",  object.getStringProperty(prefix+"AxisSrc", None))	# AutoScale, fromUser and fromPv
        setattr(self, prefix+"AxisFormat",  object.getStringProperty(prefix+"AxisFormat", None))	# AutoScale, fromUser and fromPv
        setattr(self, prefix+"AxisPrecision",  object.getStringProperty(prefix+"AxisPrecision", None))	# AutoScale, fromUser and fromPv
        setattr(self, prefix+"Min", object.getDoubleProperty(prefix+"Min", 0))
        setattr(self, prefix+"Max", object.getDoubleProperty(prefix+"Max", 0))
        setattr(self, prefix+"Label", object.getStringProperty(prefix+"Label", None))
        setattr(self, prefix+"LabelIntervals", object.getIntProperty(prefix+"LabelIntervals", None))
        setattr(self, prefix+"MajorsPerLabel", object.getIntProperty(prefix+"MajorsPerLabel", None))
        setattr(self, prefix+"MinorsPerMajor", object.getIntProperty(prefix+"MinorsPerMajor", None))
        setattr(self, prefix+"ShowLabelGrid", object.getIntProperty(prefix+"ShowLabelGrid", None))
        setattr(self, prefix+"ShowMajorGrid", object.getIntProperty(prefix+"ShowMajorGrid", None))
        setattr(self, prefix+"ShowMinorGrid", object.getIntProperty(prefix+"ShowMinorGrid", None))

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
                if self.xAxisStyle == "time" and self.updateTimerMs is None:
                    # plot against time, but only when the y PV updates
                    curve.edmXdata.append( time.time() )
                    curve.setData(list(curve.edmXdata), list(curve.edmYdata) )
                    redisplay(self)
                elif self.xAxisStyle != "time":
                    # auto-generate some x data
                    curve.edmXdata = [ xn for xn in range(0, len(curve.edmYdata)) ]
                    curve.setData(list(curve.edmXdata), list(curve.edmYdata) )
                    redisplay(self)
            else:
                # have x data - use X and Y directly
                curve.setData(list(curve.edmXdata), list(curve.edmYdata) )
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
        if curve.updateMode in [ "x", "xOrY" ] and updateTimerMs is None:
            if curve.yPv == None:
                return
            curve.setData(list(curve.edmXdata), list(curve.edmYdata))
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
        
            curve.setData(list(curve.edmXdata), list(curve.edmYdata))
        redisplay(self)

    def resetCallback(self, widget, **args):
        if hasattr(self, "curves") == 0:
            return
        for curve in self.curves:
            curve.setData([], [])
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
