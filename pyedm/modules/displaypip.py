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
from .edmWidget import edmWidget, pvItemClass
from .edmWindowWidget import edmWindowWidget, generateWidget, mousePressEvent, mouseReleaseEvent, mouseMoveEvent
from . import edmColors
from .edmField import edmField, edmTag
from .edmEditWidget import edmEdit, edmEditField
from .edmProperty import converter

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea

class edmEditPIP(edmEdit.SubScreen):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.colvalue = {}
        self.newtags = {}
        self.numDsps = self.widget.numDsps
        for idx, fld in enumerate(self.edmfield.group):
            self.colvalue[idx] = self.widget.objectDesc.getProperty(fld.tag, arrayCount=self.numDsps).copy()

    def buildLayout(self):
        layout = QtWidgets.QGridLayout()
        # add column headers, and create the array of values
        for idx, fld in enumerate(self.edmfield.group):
            label = QtWidgets.QLabel(fld.tag)
            label.setFrameShape(QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken)
            layout.addWidget(label, 0, idx)

        for row in range(self.numDsps):
            for idx, fld in enumerate(self.edmfield.group):
                tagw = fld.editClass(fld.tag, fld, self.widget, **fld.editKeywords)
                w = tagw.showEditWidget(self.colvalue[idx][row]).nolabel()
                layout.addWidget(w, row+1, idx)
                tagw.newValue.connect(lambda tag, value, row=row,col=idx:self.onNewValue(tag,value,row,col))
            remove = QtWidgets.QPushButton("Remove")
            layout.addWidget(remove, row+1, len(self.edmfield.group))
            remove.clicked.connect(lambda clicked, rmRow=row: self.removeRow(rmRow))
        addrow = QtWidgets.QPushButton("Add Display")
        layout.addWidget(addrow, self.numDsps+1, 0)
        addrow.clicked.connect(self.addRow)

        return layout

    def removeRow(self, curveNum):
        ''' removeRow - copy the gridlayout to a new gridlayout,
            ignoring the row to be deleted.
        '''
        print(f"edmEditCurveConfig removeRow {curveNum}")
        for idx in range(len(self.colvalue)):
            self.colvalue[idx].pop(curveNum)
            self.numDsps -= 1
        layout = self.buildLayout()
        self.changeLayout(layout)
        self.newtags["numDsps"] = self.numDsps


    def addRow(self):
        print(f"edmEditCurveConfig {self} addRow")
        self.numDsps += 1
        for idx, fld in enumerate(self.edmfield.group):
            self.colvalue[idx].append(converter(edmTag(fld.tag, fld.defaultValue), fld, None))
            self.onNewValue(fld.tag, self.colvalue[idx][-1], self.numDsps-1, idx)
        layout = self.buildLayout()
        self.changeLayout(layout)
        self.newtags["numDsps"] = self.numDsps

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

    def edmCleanup(self):
        try:
            self.edmParent.buttonInterest.remove(self)
        except (AttributeError,IndexError):
            pass    # parents may remove buttonintest
        self.edmParent = None
        self.buttonInterest = []
        super().edmCleanup()

    def mousePressEvent(self, event):
        # strange operation - the scroll widget catches mouse
        # events before the top-level window. To translate,
        # the mouse positions have to be rewritten.
        # Currently, this does NOT capture the mouse events!
        mousePressEvent(self, event)

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
            edmField("edit Menu", edmEditPIP, group = [
                edmField("displayFileName", edmEdit.String, array=True),
                edmField("menuLabel", edmEdit.String, array=True),
                edmField("symbols", edmEdit.String, array=True),
                edmField("replaceSymbols", edmEdit.Bool, array=True),
                edmField("propagateMacros", edmEdit.Bool, array=True),
                edmField("noScroll", edmEdit.Bool),
                ] ),
            edmField("ignoreMulitplexors", edmEdit.Bool)
            ]
    V3propTable = {
        "1-0" : [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "filePv", "file" ]
            }
    def __init__(self, parent=None):
        QScrollArea.__init__(self,parent)
        edmWidget.__init__(self,parent)
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
                pass    # widgets may clear buttonInterest before calling child edmCleanup()
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
        self.scr = edmApp.edmScreen( filename, mt, self.findDataPaths() )
        if len(self.scr.objectList) == 0:
            return
        self.scrollable.macroTable = mt
        generateWidget(self.scr, self.scrollable)
        self.scrollable.edmScreen = self.scr
        w,h = int(self.scr.tags["w"].value), int(self.scr.tags["h"].value)
        self.scrollable.setGeometry(0,0, int(w*edmApp.rescale), int(h*edmApp.rescale) )
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


edmApp.edmClasses["activePipClass"] = activePipClass

