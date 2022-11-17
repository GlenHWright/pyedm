# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# symbolClass Use portions of an edl file based on top-level "group" classification.
# This class uses PV's to compute and index, and redisplays the "subset" with the
# computed entry.
#
from .edmPVfactory import buildPV
from .edmApp import redisplay, edmApp
from .edmWidget import edmWidget
from . import edmWindowWidget
from .edmAbstractSymbol import AbstractSymbolClass
from .edmField import edmField
from .edmEditWidget import edmEdit, edmEditField, edmTagWidget

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QPainter, QFontMetrics
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QGridLayout

class QIntEdit(QtWidgets.QLineEdit):
    def __init__(self, value=None, *args, minval=None, maxval=None, width=None, **kw):
        if type(value) == int:
            value = str(value)
        super().__init__(value, *args, **kw)
        self.intValidator = QtGui.QIntValidator(self)
        if minval != None:
            self.intValidator.setBottom(minval)
        if maxval != None:
            self.intValidator.setTop(maxval)
        if width != None:
            self.setMaximumWidth(width)
        self.setValidator(self.intValidator)

class edmEditPVNAMES(edmEditField):
    def showEditWidget(self, *args, **kw):
        widget = QWidget()
        fm = QFontMetrics(widget.font())
        width = fm.boundingRect("000000").width()
        layout = QGridLayout()
        for idx in range(0,5):
            row = int(idx*2)
            layout.addWidget(QtWidgets.QLabel("PV name"), row, 0 )
            layout.addWidget(QtWidgets.QLineEdit(self.widget.controlPvs[idx]), row, 1, 1, -1)
            layout.addWidget(QtWidgets.QLabel("AND"), row+1, 0)
            layout.addWidget(QIntEdit(self.widget.andMask[idx], minval=0,  maxval=255, width=width), row+1, 1)
            layout.addWidget(QtWidgets.QLabel("XOR"), row+1, 2)
            layout.addWidget(QIntEdit(self.widget.xorMask[idx], minval=0, maxval=255, width=width), row+1, 3)
            layout.addWidget(QtWidgets.QLabel("Shift"), row+1, 4)
            layout.addWidget(QIntEdit(self.widget.shiftCount[idx], minval=-8, maxval=8, width=width), row+1, 5)
        widget.setLayout(layout)
        return edmTagWidget(None, widget)

class edmEditItems(edmEditField):
    def __init__(self, *args, **kw):
        super().__init__(*args,**kw)
        self.itemNumber = 0

    def showEditWidget(self,  *args, **kw):
        layout = QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Number of Items"), 0, 0, 1, 2)
        layout.addWidget(QIntEdit(self.widget.numStates, minval=0), 0, 2)
        layout.addWidget(QtWidgets.QLabel("Item Number"), 1, 0, 1, 2)
        layout.addWidget(QIntEdit(self.itemNumber+1), 1, 2 )
        layout.addWidget(QtWidgets.QLabel(">="), 2, 0)
        layout.addWidget(QIntEdit(self.widget.minValues[self.itemNumber]), 2, 1, 1, 2)
        layout.addWidget(QtWidgets.QLabel("<"), 3, 0)
        layout.addWidget(QIntEdit(self.widget.maxValues[self.itemNumber]), 3, 1, 1, 2)
        widget = QWidget()
        widget.setLayout(layout)
        return edmTagWidget(None, widget)

class symbolState:
    def __init__(self, min=0, max=1):
        self.min = min
        self.max = max

class symbolPV:
    def __init__(self, pvname, mt, idx, andMask=0, xorMask=0, shift=0):
        self.pv = buildPV(pvname,macroTable=mt)
        self.pvno = idx
        self.val = 0.0
        self.ival = 0
        self.andMask = andMask
        self.xorMask = xorMask
        self.shift = shift

class activeSymbolClass(AbstractSymbolClass):
    menuGroup = [ "display", "Dynamic Symbol" ]
    edmEntityFields = [
        edmField("file", edmEdit.String),
        edmField("truthTable", edmEdit.Bool),
        # PV information
        edmField("PVNAMES", edmEditPVNAMES),
        edmField("numPvs", edmEdit.Int, hidden=True),    # Filled in behind the scenes
        edmField("controlPvs", edmEdit.PV, array=True, defaultValue=None),
        edmField("andMask", edmEdit.Int, array=True, defaultValue=0),
        edmField("xorMask", edmEdit.Int, array=True, defaultValue=0),
        edmField("shiftCount", edmEdit.Int, array=True, defaultValue=0),
        # State information
        edmField("RANGES", edmEditItems),
        edmField("numStates", edmEdit.Int, hidden=True, defaultValue=0),    # needs extra management!
        edmField("minValues", edmEdit.Int, array=True, defaultValue=0),
        edmField("maxValues", edmEdit.Int, array=True, defaultValue=1)
        ]
    edmFieldList =  \
        AbstractSymbolClass.edmBaseFields + AbstractSymbolClass.edmColorFields + \
        edmEntityFields + AbstractSymbolClass.edmVisFields
    '''selects a "group" from an edm symbol file based on a calculated value'''
    V3propTable = {
        "1-5" : [   "file", "gateUpPv", "gateDownPv", "gateDownValue", "continuous", "rate", "numStates", "useOriginalSize",
            "ID", "initialIndex", "colorPv", "useOriginalColors", "fgColor", "bgColor", "showOOBState", "gateOnMouseOver" ]
    }
        
    def __init__(self, parent=None):
        super().__init__(parent)

    def edmCleanup(self):
        AbstractSymbolClass.edmCleanup(self)
        for pv in self.pvList:
            pv.pv.del_callback(self)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.file = objectDesc.getProperty("file", "")
        self.truthTable = objectDesc.getProperty("truthTable")
        # PV information
        self.numPvs = objectDesc.getProperty("numPvs")
        self.controlPvs = objectDesc.getProperty("controlPvs", arrayCount=5)
        self.andMask = objectDesc.getProperty("andMask", arrayCount=5)
        self.xorMask = objectDesc.getProperty("xorMask", arrayCount=5)
        self.shiftCount = objectDesc.getProperty("shiftCount", arrayCount=5)
        # State information
        self.statelist = []
        self.numStates = objectDesc.getProperty("numStates")
        self.minValues = objectDesc.getProperty("minValues", arrayCount=self.numStates)
        self.maxValues = objectDesc.getProperty("maxValues", arrayCount=self.numStates)

        if self.numStates > 0:
            self.statelist = [ symbolState(item[0], item[1]) for item in zip(self.minValues, self.maxValues) ]

        self.buildStateObjects(self.file)
        self.idxState = 0

        # set up callbacks for PV's
        self.pvList = []
        mt = self.findMacroTable()
        for idx in range(0,self.numPvs):
            pv = symbolPV(self.controlPvs[idx], mt, idx)
            self.pvList.append(pv)
            pv.andMask = self.andMask[idx]
            pv.xorMask = self.xorMask[idx]
            pv.shiftCount = self.shiftCount[idx]
            pv.pv.add_callback(self.calcState, self, pv)
            
    def calcState(self, item, **kw):
        if 'userArgs' not in kw:
            return
        thispv = kw['userArgs']
        thispv.val = kw["value"]
        thispv.ival = int(thispv.val)
        if self.truthTable:
            if thispv.val == 0.0:
                self.idxState = self.idxState & ~(1<<thispv.idx)
            else:
                self.idxState = self.idxState | (1<<thispv.idx)
            self.curState = self.statelist[self.idxState]
            redisplay(self)
            return
        if self.numPvs == 1 and thispv.andMask == 0 and thispv.xorMask == 0 and thispv.shiftCount == 0:
            istate = thispv.ival
        else:
            ival = thispv.ival
            if self.andMask[thispv.idx]:
                ival = ival & self.andMask[thispv.idx]
            ival = ival ^ self.xorMask[thispv.idx]
            if self.shiftCount[thispv.idx] < 0:
                ival = ival >> (-self.shiftCount[thispv.idx])
            else:
                ival = ival << self.shiftCount[thispv.idx]
            thispv.ival = ival
            istate = 0
            for pv in self.pvList:
                istate = istate | pv.ival

        for item in self.statelist:
            if istate >= item.min and istate < item.max:
                self.curState = item
                redisplay(self)
                return
        print(f"No state selected: istate={istate}, count={len(self.statelist)}/{self.numStates}")

    def mousePressEvent(self, event):
        edmWindowWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        edmWindowWidget.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        edmWindowWidget.mouseMoveEvent(self, event)

edmApp.edmClasses["activeSymbolClass"] = activeSymbolClass


