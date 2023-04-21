# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#
# This is a high-level module
# called from __init__ and edmAbstractSymbol
#
#
# Handles top-level EDM windows
#

from enum import Enum

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication, QClipboard

from .edmApp import edmApp
from .edmScreen import edmScreen
from .edmWidgetSupport import edmWidgetSupport
from .edmParentSupport import edmParentSupport
from .edmMouseHandler import mousePressEvent, mouseReleaseEvent, mouseMoveEvent
from .edmWidget import edmWidget
#
# A simple top-level widget, and support for managing mouse buttons.
# This module also contains generic mouse support routines that
# are called from numerous different widgets.
#

class edmWindowWidget(QtWidgets.QWidget, edmWidgetSupport, edmParentSupport):
    '''edmWindowWidget - top-level window widget for an edm screen.
        manage mouse clicks on behalf of children'''
    def __init__(self, parent=None, **kwargs):
        QtWidgets.QWidget.__init__(self, parent, **kwargs)
        edmParentSupport.__init__(self, parent, **kwargs)

    def __repr__(self):
        return f"<edmWindowWidget {self.windowTitle()}>"

    def getProperty(self, *args, **kw):
        return self.edmScreenRef.getProperty(*args, **kw)

    def setProperty(self, tag, value):
        if hasattr(self, "edmScreenRef"):
            self.edmScreenRef.addTag(tag, value)

    def checkProperty(self, *args, **kw):
        return self.edmScreenRef.checkProperty(*args, **kw)

    def updateTags(self, tags):
        ''' updateTags(tags) - rebuild the screens tags from the tag list provided.
        '''
        for tag in tags.values():
            self.edmScreenRef.tags[tag.tag] = tag
        self.setDisplayProperties()


    def generateWindow(self, screen, *, myparent=None, macroTable=None, dataPaths=None):
        '''generateWindow - fill in self with widgets from objects in 'screen' list'''
        if edmApp.debug() : print("generateWindow", screen, "Parent:", myparent, "macroTable:", macroTable)
        if myparent:
            self.edmParent = myparent
        self.dataPaths = dataPaths
        self.edmScreenRef = screen
        if myparent != None and macroTable == None:
            self.macroTable = getattr(myparent, "macroTable", None)
        else:
            self.macroTable = macroTable

        self.setDisplayProperties()
        self.parentx = 0
        self.parenty = 0
        generateWidget(screen, self)
        self.show()
        if edmApp.debug() : print("done generateWindow")
        return self
    
    def setDisplayProperties(self):
        pal = self.palette()
        self.fgRule = self.getProperty("fgColor")
        if self.fgRule:
                pal.setColor( self.foregroundRole(), self.fgRule.getColor() )

        self.bgRule = self.getProperty("bgColor")
        if self.bgRule:
                pal.setColor( self.backgroundRole(), self.bgRule.getColor() )

        title = self.getProperty("title")
        if title != "":
            self.setWindowTitle("PyEdm - " + self.macroExpand(title))
        else:
            self.setWindowTitle("PyEdm - " + self.getProperty("Filename"))
        self.setPalette(pal)
        x = self.getProperty("x")
        y = self.getProperty("y")
        self.move(x,y)
        w = self.getProperty("w")
        h = self.getProperty("h")
        self.resize(w,h)

    def getParentScreen(self):
        try:
            return self.edmParent.getParentScreen()
        except AttributeError:
            # this can be no edmParent or None edmParent
            pass
        return self

    def saveToFile(self, *args, **kw):
        self.edmScreenRef.saveToFile(*args, **kw)

    def mousePressEvent(self, event):
        mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        mouseMoveEvent(self, event)

    def resizeEvent(self, event):
        self.setProperty("w", self.width())
        self.setProperty("h", self.height())

    def moveEvent(self, event):
        pos = event.pos()
        self.setProperty("x", pos.x())
        self.setProperty("y", pos.y())

    def closeEvent(self, event):
        ''' before closing a window, give all
            widgets a chance to clean up.
        '''
        if edmApp.debug(1) : print(f"closeEvent: cleaning up {self}")
        self.edmCleanup()
        event.accept()
        if edmApp.debug() : print("done closeEvent")

    def edmCleanup(self):
        # To Do: add check for unsaved changes
        #
        if edmApp.debug(1) : print(f"edmCleanup {self}")
        try:
            self.edmParent.edmCleanupChild(self)
        except AttributeError:
            pass
        self.edmParent = None
        self.selectedWidget = None
        self.focusedWidget = None
        self.buttonInterest.clear()
        self.edmEditList.clear()

        for child in self.children():
            try:
                child.edmCleanup()
            except AttributeError as exc:
                print(f"WindowWidget closeEvent: child {child} lacking edmCleanup! {exc}")
        try:
            edmApp.windowList.remove(self)
        except ValueError as exc:
            if edmApp.debug() : print(f"Unable to remove windowWidget {self} from window list -- already gone!")

        self.destroy()

    def getEditPropertiesList(self):
        return self.edmScreenRef.edmFieldList

    @staticmethod
    def buildNewWindow():
        ''' buildNewWindow - create a new empty window.
        '''
        screen = edmScreen()
        parent = edmWindowWidget()
        for field in edmScreen.edmFieldList:
            screen.addTag(field.tag, field.defaultValue)

        screen.addTag("Filename", "**NEW**")
        screen.addTag("Class", "Screen")
        window = generateWindow(screen, macroTable=edmApp.macroTable)
        edmApp.windowList.append(window)

def generateWidget(screen, parent):
    '''
     generate widgets based on the screen description. The expectation is that 'parent'
     is a container widget and the widgets generated from screen.objectList will be
     built within parent.
    '''
    if edmApp.debug(1) : print("generateWidget", screen, parent, getattr(parent,"macroTable", None))
    for obj in screen.objectList:
        if edmApp.debug() :  print(f"checking object {obj} {obj.tags}")
        otype =  obj.tags["Class"].value
        if edmApp.debug() :  print("checking object type", otype)
        if otype in edmApp.edmClasses:
            widget = edmApp.edmClasses[otype](parent)
            widget.buildFieldList(obj)
            widget.buildFromObject(obj)
        else:
            if edmApp.debug() : print("Unknown object type", otype, "in", edmApp.edmClasses)
    if edmApp.debug() : print("Done generateWidget")
    
def generateWindow(screen, **kw):
    '''
    creates an edmWindowWidget, and calls widget.generateWindow(screen, **kw)
    create an 'edmWindowWidget' as a parent window and populate it with widgets from
    the screen description.
    '''
    parent = edmWindowWidget()
    parent.generateWindow(screen, **kw)
    return parent

edmApp.generateWindow = generateWindow
edmApp.generateWidget = generateWidget
edmApp.buildNewWindow = edmWindowWidget.buildNewWindow
