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

from enum import Enum

from .edmApp import redisplay, edmApp
from .edmScreen import edmScreen
from .edmWidget import edmWidget, pvItemClass
from .edmWindowWidget import edmWindowWidget, generateWidget, mousePressEvent, mouseReleaseEvent, mouseMoveEvent
from . import edmColors
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea

class scrolledWidget(edmWindowWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edmParent=parent
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.buttonInterest = []
        if parent:
            self.edmParent.buttonInterest.append(self)

    def mousePressEvent(self, event):
        # strange operation - the scroll widget catches mouse
        # events before the top-level window. To translate,
        # the mouse positions have to be rewritten.
        if True or self.edmParent.editMode(check="none"):
            mousePressEvent(self, event)
        else:
            self.edmParent.mousePressEvent(event)

    def xxmouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event)

    def xxmouseMoveEvent(self, event):
        mouseMoveEvent(self, event)

    def xxedmShowEdit(self, widget):
        ''' edmShowEdit - act like a window!
            we have the situation where the widget has been clicked in
            edit mode, and now we probably don't have the desired
            widget because the child selection is wrong!
        '''
        parent = self.edmParent
        while not hasattr(parent, "edmShowEdit"):
            parent = parent.edmParent
        return parent.edmShowEdit(self.edmParent)

class activePipClass(QScrollArea,edmWidget):
    menuGroup = [ "display", "PIP"]
    buildPipEnum =   Enum("buildPip", "stringPV file menu", start=0 )
    buildPipList = {
                buildPipEnum(0): "buildPipStringPV",
                buildPipEnum(1): "buildPipFile",
                buildPipEnum(2): "buildPipMenu" }
    edmEntityFields = [
            edmField("topShadowColor", edmEdit.Color),
            edmField("botShadowColor", edmEdit.Color),
            edmField("displaySource", edmEdit.Enum, enumList=buildPipEnum, defaultValue="stringPV"),
            edmField("filePv", edmEdit.PV),
            edmField("labelPv", edmEdit.PV),
            edmField("file", edmEdit.String),
            edmField("center", edmEdit.Int, defaultValue=0),
            edmField("setSize", edmEdit.Int, defaultValue=0),
            edmField("sizeOfs", edmEdit.Int, defaultValue=0),
            edmField("numDsps", edmEdit.Int, defaultValue=0),
            edmField("displayFileName", edmEdit.String, array=True),
            edmField("menuLabel", edmEdit.String, array=True),
            edmField("symbols", edmEdit.String, array=True),
            edmField("replaceSymbols", edmEdit.Bool, array=True),
            edmField("propagateMacros", edmEdit.Bool, array=True),
            edmField("noScroll", edmEdit.Bool),
            edmField("ignoreMulitplexors", edmEdit.Bool)
            ]
    V3propTable = {
        "1-0" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "filePv", "file" ]
            }
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pvItem["filePv"] = pvItemClass( "PVname", "filePV")
        self.pvItem["labelPv"] = pvItemClass( "PVlabel", "labelPV")
        self.setLineWidth(2)
        self.setFrameShape(QFrame.Panel|QFrame.Sunken)
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.scrollable = None
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def edmCleanup(self):
        '''remove references to other items.'''
        scrollable =  self.scrollable
        self.scrollable = None
        if scrollable:
            scrollable.edmCleanup()
            self.buttonInterest.clear()
            try:
                self.edmParent.buttonInterest.remove(self)
            except ValueError:
                pass    # some widgets clear buttonInterest before calling child edmCleanup()
        super().edmCleanup()

    def buildFromObject(self, objectDesc, **kw):
        rebuild = kw.get('rebuild', False)
        if not rebuild:
            objectDesc.addTag("bgColor", "builtin:transparent")  # edm PIP uses parent's background color - not quite the same...
        kw['attr'] = None
        super().buildFromObject( objectDesc, **kw)

        self.scrollable = scrolledWidget(self)
        self.displaySource = objectDesc.getProperty("displaySource", "stringPV")
        self.numDsps = objectDesc.getProperty("numDsps", 0)
        if self.displaySource in self.buildPipList:
            getattr(self,self.buildPipList[self.displaySource])()

    def setupScreen(self, filename, mt):
        '''setupScreen is called each time a file is selected for display'''
        print(f"pip opening {filename}")
        self.scr = edmScreen( filename, mt, self.findDataPaths() )
        if len(self.scr.objectList) == 0:
            return
        self.scrollable.macroTable = mt
        generateWidget(self.scr, self.scrollable)
        self.scrollable.setGeometry(0,0, int(self.scr.tags["w"].value), int(self.scr.tags["h"].value) )
        self.setWidget(self.scrollable)
        # over-ride the widget's color info with what the screen has available.
        pal = self.scrollable.palette()
        try:
            self.fgColor = edmColors.findColorRule(self.scr.tags["fgColor"].value)
            pal.setColor( self.foregroundRole(), self.fgColor.getColor())
        except:
            pass
        try:
            self.bgColor = edmColors.findColorRule(self.scr.tags["bgColor"].value)
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
        self.setupScreen( self.macroExpand(self.objectDesc.getProperty("file")), self.findMacroTable())

    def buildPipMenu(self):
        '''build screens based on a menu selection'''
        self.filenames = self.objectDesc.getProperty("displayFileName", arrayCount=self.numDsps, defValue="")
        if self.filenames == None:
            return
        self.symbollist = self.objectDesc.getProperty("symbols", arrayCount=self.numDsps, defValue="")
        self.menuLabels = self.objectDesc.getProperty("menuLabel", arrayCount=self.numDsps, defValue="")
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
        # PIP has changed - remove old screen
        self.scrollable.hide()
        for child in self.scrollable.children():
            if self.debug() : print("redisplay: cleanup", child)
            if not child.isWidgetType() : continue
            child.edmCleanup()
            child.edmParent = None
            child.setParent(None)
            child.deleteLater()
        self.scrollable.buttonInterest = []
        self.setupScreen( self.fileFromPV, self.selectMt)

    def xxxmousePressEvent(self, event):
        self.edmParent.mousePressEvent(event)

    def xxxmouseReleaseEvent(self, event):
        self.edmParent.mouseReleaseEvent(event)

    def xxxmouseMoveEvent(self, event):
        self.edmParent.mouseMoveEvent(event)


edmApp.edmClasses["activePipClass"] = activePipClass

