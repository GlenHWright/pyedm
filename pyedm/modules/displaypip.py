from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module displays a "picture in picture", or embedded screen.
#
# There are at least 3 different setups for EDM PIP:
# 1) simple include with no macros. A filename is taken as input, and displayed
#       numDsps == 0; displaySource == "file"
# 2) filename specified by a string PV. When the PV changes, a new screen is
# loaded.
#       filePV set, != ""; displaySource == "stringPV"
# 3) a menu list of files. A PV gives the index to use, and a screen with a
# macro list is displayed.
#       numDsps > 0; displaySource == "menu"

import pyedm.edmDisplay as edmDisplay
from pyedm.edmApp import redisplay
from pyedm.edmScreen import edmScreen
from pyedm.edmWidget import edmWidget
import pyedm.edmWindowWidget as edmWindowWidget
import pyedm.edmColors as edmColors

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea

class scrolledWidget(QWidget, edmWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def mousePressEvent(self, event):
        edmWindowWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        edmWindowWidget.mouseReleaseEvent(self, event)

class activePipClass(QScrollArea,edmWidget):
    V3propTable = {
        "1-0" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "filePv", "file" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["filePv"] = [ "PVname", "filePV", 0 ]
        self.pvItem["labelPv"] = [ "PVlabel", "labelPV", 0 ]
        self.setLineWidth(2)
        self.setFrameShape(QFrame.Panel|QFrame.Sunken)
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.scrollable = None
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def cleanup(self):
        '''remove references to other items.'''
        scrollable =  self.scrollable
        self.scrollable = None
        edmWidget.cleanup(scrollable)
        edmWidget.cleanup(self)

    def buildFromObject(self, objectDesc):
        objectDesc.tagValue["bgColor"] = "builtin:transparent"  # edm PIP uses parent's background color.
        edmWidget.buildFromObject(self, objectDesc,attr=None)

        self.scrollable = scrolledWidget(self)
        self.displaySource = objectDesc.getStringProperty("displaySource", "stringPV")
        self.numDsps = objectDesc.getIntProperty("numDsps", 0)
        if self.displaySource in buildPipList:
            getattr(self,buildPipList[self.displaySource])()

    def setupScreen(self, filename, mt):
        '''setupScreen is called each time a file is selected for display'''
        print(f"pip opening {filename}")
        self.scr = edmScreen( filename, mt, self.findDataPaths() )
        if len(self.scr.objectList) == 0:
            return
        self.scrollable.macroTable = mt
        edmDisplay.generateWidget(self.scr, self.scrollable)
        self.scrollable.setGeometry(0,0, int(self.scr.tagValue["w"]), int(self.scr.tagValue["h"]) )
        self.setWidget(self.scrollable)
        # over-ride the widget's color info with what the screen has available.
        pal = self.scrollable.palette()
        try:
            self.fgColor = edmColors.findColorRule(self.scr.tagValue["fgColor"])
            pal.setColor( self.foregroundRole(), self.fgColor.getColor())
        except:
            pass
        try:
            self.bgColor = edmColors.findColorRule(self.scr.tagValue["bgColor"])
            pal.setColor( self.backgroundRole(), self.bgColor.getColor())
        except:
            pass
        self.scrollable.setPalette(pal)
        pal = self.palette()
        pal.setColor( self.backgroundRole(), self.bgColor.getColor())
        self.setPalette(pal)
        self.scrollable.show()
        self.scrollable.update()

    def buildPipFile(self):
        self.setupScreen( self.macroExpand(self.objectDesc.getStringProperty("file")), self.findMacroTable())

    def buildPipMenu(self):
        '''build screens based on a menu selection'''
        self.filenames = self.objectDesc.decode("displayFileName",self.numDsps, "")
        if self.filenames == None:
            return
        self.symbollist = self.objectDesc.decode("symbols",self.numDsps, "")
        basemt = self.findMacroTable()
        self.filenames = [ basemt.expand(fn) for fn in self.filenames]
        if self.symbollist == None:
            self.mtlist = [basemt]*self.numDsps
        else:
            self.mtlist = []
            for sym in self.symbollist:
                mt = basemt.newTable()
                mt.macroDecode(basemt.expand(sym))
                self.mtlist.append( mt)
        if not hasattr(self, "filePV") :
            # display the first file, and we're done
            self.setupScreen(self.filenames[0], self.mtlist[0])
            return
        if self.filePV.callbackList == []:
            self.filePV.add_callback( self.newMenuPV, self)

    def newMenuPV(self, arg, **kw):
        '''use the PV value as an index to determine which file to display'''
        idx = kw['value']
        try: idx = int(idx)
        except: idx=0
        if idx >= 0 and idx < len(self.filenames):
            self.selectMt = self.mtlist[idx]
            self.fileFromPV = self.selectMt.expand(self.filenames[idx])
            redisplay(self)

    def buildPipStringPV(self):
        '''build screens based on PV value. Not much that can be done here, wait for the value callbacks
        in order to generate the screens'''
        if not hasattr(self, "filePV") :
            return
        if self.filePV.callbackList == [] :
            self.filePV.add_callback( self.newPipStringPV, self)

    def newPipStringPV(self, arg, **kw):
        self.fileFromPV = self.macroExpand(kw['value'])
        self.selectMt = self.findMacroTable()
        redisplay(self)                 # ensure that the widget work is done in thread 0

    def redisplay(self, **kw):
        if self.visible != self.lastVisible:
            self.lastVisible = self.visible
            self.setVisible(self.visible)
        if self.fileFromPV == "":
            return
        self.scrollable.hide()
        for child in self.scrollable.children():
            if self.DebugFlag > 0 : print("redisplay: cleanup", child)
            if not child.isWidgetType() : continue
            child.cleanup()
            child.edmParent = None
            child.setParent(None)
            child.deleteLater()
        self.scrollable.buttonInterest = []
        self.setupScreen( self.fileFromPV, self.selectMt)

buildPipList = {  "stringPV":"buildPipStringPV",  "file": "buildPipFile", "menu": "buildPipMenu" }

edmDisplay.edmClasses["activePipClass"] = activePipClass

