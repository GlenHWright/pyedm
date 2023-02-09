# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#
# This is a high-level module
# called from __init__ and edmAbstractSymbol
# referenced by edmWindowWidget
#
#
# Handles top-level EDM windows, and has common routines to support mouse events
#

from enum import Enum

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication, QClipboard

from .edmApp import edmApp
from .edmScreen import edmScreen
from .edmWidgetSupport import edmWidgetSupport
from .edmParentSupport import edmParentSupport, showBackgroundMenu
from .edmWidget import edmWidget
from .edmEditWidget import edmRubberband, edmEdit
from .edmColors import findColorRule
from .edmField import edmField, edmTag
#
# A simple top-level widget, and support for managing mouse buttons.
# This module also contains generic mouse support routines that
# are called from numerous different widgets.
#

class edmWindowWidget(QtWidgets.QWidget, edmWidgetSupport, edmParentSupport):
    '''edmWindowWidget - top-level window widget for an edm screen.
        manage mouse clicks on behalf of children'''
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

    def __repr__(self):
        return f"<edmWindowWidget {self.windowTitle()}>"

    def getProperty(self, *args, **kw):
        return self.edmScreenRef.getProperty(*args, **kw)

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
        # To Do: get "x y w h " here
        #
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

def mousePressEvent(widget, event):
    # handle mouse press events.
    debug = getattr(widget, "DebugFlag", 0)

    if debug > 0: print(f"mousePressEvent({widget},{event},{event.pos()},{widget.editMode()}")

    # if in rubberband mode, pass the event along.
    if widget.rubberband and widget.editMode(check="none"):
        if widget.rubberband.mousePressEvent(event) == False:
            widget.rubberband.inactive()
            widget.rubberband = None
            widget.editMode(value="none")
        event.accept()
        return

    if event.button() == Qt.LeftButton and not widget.editMode(check="none"):
        # making a selection in one of the edit modes.

        if debug > 0 : print(f"clicked edit={widget.editModeValue} RB={widget.rubberband}")
        # check if clicking a widget. If so, then bring up the properties window.
        pos = event.pos()
        findActionWidget(widget, pos, debug=debug)   # ignore return value; widget.selectedWidget already set

        if widget.selectedWidget == None and not widget.editMode(check="none"):
            print(f"didn't select widget - try again!")

        event.accept()
        return

    if event.button() == Qt.MidButton:
        if findDragName(widget, event.pos()) :
            event.accept()
            return

    found = False
    # need a list of widgets that might be interested in mouse clicks.
    pos = event.pos()
    # additional code needed here for Mac systems. See childAt_helper() in gui/kernel/qwidget.cpp
    for ch in widget.buttonInterest:
        if ch.isWindow() or ch.isHidden():  # ignore these children
            continue
        if ch.isWidgetType() and ch.geometry().contains(pos):
            point = ch.mapFromParent(pos)
            if ch.focusPolicy() != Qt.NoFocus:
                if debug>0 : print("Changing focus to:", ch)
                ch.setFocus()
            chEvent =  QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) 
            ch.mousePressEvent( chEvent)
            if chEvent.isAccepted():
                found = True
                break

    if debug > 0 : print(f"found:{found} accepted:{event.isAccepted()} button:{event.button()}")
    if found:
        event.accept()
        return
    # if a right button click, and not otherwise taken by a child widget, generate an "edm" menu
    if event.button() == Qt.RightButton:
        showBackgroundMenu(widget, event)
        event.accept()
        return
    # Potential: evaluate other mouse clicks that didn't get a widget

def mouseReleaseEvent(widget, event):
    if widget.rubberband:
        widget.rubberband.mouseReleaseEvent(event)
        event.accept()
        return
    pos = event.pos()
    for ch in widget.buttonInterest:
        if ch.isWidgetType() and not ch.isWindow() and not ch.isHidden() and ch.geometry().contains(pos):
            point = ch.mapFromParent(pos)
            ch.mouseReleaseEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
    event.accept()

def mouseMoveEvent(widget, event):
    # if we're moving or resizing a widget, the rubberband should take this event
    if widget.rubberband != None:
        widget.rubberband.mouseMoveEvent(event)
        event.accept()
        return
    pos = event.pos()
    for ch in widget.buttonInterest:
        if ch.isWidgetType() and not ch.isWindow() and not ch.isHidden() and ch.geometry().contains(pos):
            point = ch.mapFromParent(pos)
            ch.mouseMoveEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
    # TODO: in normal mode, check hover possibilities
    event.accept()

# If a middle button click, then try and find a child under the mouse pointer.
# if the child has "buttonInterest" attribute, then recurse
def findDragName(widget, pos):
    childlist = widget.children()
    childlist.reverse()
    for ch in childlist:
        if not ch.isWidgetType() or ch.isWindow() or ch.isHidden() or ch.geometry().contains(pos) == 0:
            continue
        try:
            if hasattr(ch, "buttonInterest"):
                if findDragName(ch, ch.mapFromParent(pos)):
                    return True
            if hasattr(ch, "pvItem") == False:
                continue
        except AttributeError:
            # some reimplementations of getattr make a recursive call to hasattr
            pass
        for item in ch.pvItem.values():
            # This tests whether a particular PV was assigned when creating the widget.
            pv = getattr(ch, item.attributePV, None)
            if pv == None:
                continue

            # Note - this returns the name used for the connection, not the name
            # before any macro expansion. This allows the name to be used directly
            # in copy and paste.
            name = pv.getPVname()
            QApplication.clipboard().setText(name, QClipboard.Clipboard);
            QApplication.clipboard().setText(name, QClipboard.Selection);


            d = QtGui.QDrag(ch)
            mimeData = QtCore.QMimeData()
            mimeData.setText(name)
            d.setMimeData(mimeData)

            w = ch.fontMetrics().width(name)
            h = ch.fontMetrics().height()
            pm = QtGui.QPixmap(w+2, h+2)
            paint = QtGui.QPainter(pm)
            paint.setFont(ch.font())
            paint.eraseRect(0, 0, w+2, h+2)
            paint.drawText(1, h, name)
            paint.end()
            d.setPixmap(pm)
            d.exec_()
            return True
    return False

def findEdmChildren(widget, pos):
    '''return a list of edm children at all levels of this widget'''
    widgetlist = []
    for ch in widget.children():
        if edmApp.debug() : print(f"check widget {widget} child {ch} point {pos} geometry {getattr(ch, 'geometry', lambda:'-')()}")
        if isinstance(ch, edmWidget) and not ch.isWindow() and ch.geometry().contains(pos):
            widgetlist.append(ch)
            widgetlist += findEdmChildren(ch, ch.mapFrom(widget,pos))

    return widgetlist

def findActionWidget(parent, pos, debug=0):
    ''' findActionWidget - checks to see if there's a widget under the global position 'pos'
            that is a child of parent. Uses 'findEdmChildren'.
    '''
    widgetlist = findEdmChildren(parent, pos)
    if debug >= 0 : print(f"findEdmChildren({parent}...) returns {widgetlist}")

    if len(widgetlist) == 0:
        parent.selectedWidget = None
        return None

    if len(widgetlist) == 1:
        if debug > 0: print(f"found widget {widgetlist[0]}")
        parent.selectedWidget = widgetlist[0]
    else:
        parent.selectedWidget = showWidgetMenu(widgetlist, parent.mapToGlobal(pos))

    if parent.selectedWidget == None:
        return None

    if parent.editMode(check="edit"):
        parent.edmShowEdit(parent.selectedWidget)
        parent.editMode(value="none")
    elif parent.editMode(check="move"):
        if parent.rubberband == None:
            parent.rubberband = edmRubberband(widget=parent.selectedWidget)
        else:
            parent.rubberband.active(parent.selectedWidget)
        parent.editMode(value="none")

    return parent.selectedWidget

class edmEditWidgetMenu(QtWidgets.QMenu):
    '''
        edmEditWidgetMenu
        Takes a list of widgets, and displays a list
        allowing selection of a single entry.
    '''
    def __init__(self, *args, edmWidgets=[], **kw):
        super().__init__(*args, **kw)
        self.selected = None
        for widget in edmWidgets:
            self.setMenuAction(widget.__str__(), lambda flag,w=widget:self.displayWidget(w), widget)

    def setMenuAction(self, name, perform, widget):
        action = self.addAction(name)
        action.widget = widget
        action.triggered.connect(perform)

    def displayWidget(self, widget):
        self.selected = widget


def showWidgetMenu(widgetlist, globalPos):
    menu = edmEditWidgetMenu(edmWidgets=widgetlist)
    menu.exec_(globalPos)
    return menu.selected


def generateWidget(screen, parent):
    '''
     generate widgets based on the screen description. The expectation is that 'parent'
     is a container widget and the widgets generated from screen.objectList will be
     built within parent.
    '''
    if edmApp.debug(1) : print("generateWidget", screen, parent, getattr(parent,"macroTable", None))
    for obj in screen.objectList:
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
    generateWindow(screen, myparent, macroTable, dataPaths)
    create an 'edmWindowWidget' as a parent window and populate it with widgets from
    the screen description.
    '''
    parent = edmWindowWidget()
    parent.generateWindow(screen, **kw)
    return parent

edmApp.generateWindow = generateWindow
edmApp.generateWidget = generateWidget
edmApp.buildNewWindow = edmWindowWidget.buildNewWindow
