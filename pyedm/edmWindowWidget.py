# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#
# This is a high-level module
# called from __init__ and edmAbstractSymbol
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
from .edmParentSupport import edmParentSupport, showBackgroundMenu, windowMenu
from .edmWidget import edmWidget, buildNewWidget
from .edmEditWidget import edmShowEdit, edmRubberband, edmEdit
from .edmColors import findColorRule
from .edmField import edmField, edmTag
#
# A simple top-level widget, and support for managing mouse buttons.
# This module also contains generic mouse support routines that
# are called from numerous different widgets.
#

editModeEnum = Enum("editmode", "none edit move resize")
class edmWindowWidget(QtWidgets.QWidget, edmWidgetSupport, edmParentSupport):
    '''edmWindowWidget - top-level window widget for an edm screen.
        manage mouse clicks on behalf of children'''
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        '''
        self.edmParent = parent
        self.editModeValue = editModeEnum.none      # edit mode might be able to work 'better' in pyEdm, but need to support saving embedded windows!
        self.selectedWidget = None      # set to the edmWidget entry that's been selected in edit mode; must be a descendant of this widget.
        self.rubberband = None          # if set, then this is a resize/move widget.
        self.focusedWidget = None       # if hovering over a widget, check that we're still over the same widget.
        self.edmScreen = None              # set to the edmScreen object
        self.buttonInterest = []
        self.edmEditList = []
        '''

    def __repr__(self):
        return f"<edmWindowWidget {self.windowTitle()}>"

    def getProperty(self, *args, **kw):
        return self.edmScreen.getProperty(*args, **kw)

    def updateTags(self, tags):
        ''' updateTags(tags) - rebuild the screens tags from the tag list provided.
        '''
        for tag in tags.values():
            self.edmScreen.tags[tag.tag] = tag
        self.setDisplayProperties()


    def generateWindow(self, screen, *, myparent=None, macroTable=None, dataPaths=None):
        if edmApp.debug() : print("generateWindow", screen, "Parent:", myparent, "macroTable:", macroTable)
        if myparent:
            self.edmParent = myparent
        self.dataPaths = dataPaths
        self.edmScreen = screen
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
        if title != None:
            self.setWindowTitle("PyEdm - " + self.macroExpand(title))
        else:
            self.setWindowTitle("PyEdm - " + self.getProperty("Filename"))
        self.setPalette(pal)

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
        print(f"closeEvent: cleaning up {self}")
        self.edmCleanup()
        event.accept()
        print("done closeEvent")

    def edmCleanup(self):
        # To Do: add check for unsaved changes
        #

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
            pass

        self.destroy()

    def getEditPropertiesList(self):
        return self.edmScreen.edmFieldList

    def buildNewWindow(self):
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
    debug = getattr(widget, "DebugFlag", 0)

    if debug > 0: print(f"mousePressEvent({widget},{event},{widget.editMode()}")
    if not widget.editMode(check="none"):
        # if right mouse in edit mode, only allow menu selection
        if event.button() == Qt.RightButton:
            showBackgroundMenu(widget, event)
            event.accept()
            return
        print(f"clicked edit={widget.editModeValue} RB={widget.rubberband}")
        # if in rubberband mode, pass the event along.
        if widget.rubberband:
            if widget.rubberband.mousePressEvent(event) == False:
                widget.rubberband.inactive()
                widget.rubberband = None
                widget.editMode(value="none")
            event.accept()
            return
        # check if clicking a widget. If so, then bring up the properties window.
        pos = event.pos()
        widgetlist = []
        for ch in widget.children():
            if isinstance(ch, edmWidget) and not ch.isWindow() and ch.geometry().contains(pos):
                widgetlist.append(ch)

        # opportunity for improvement: 
        # display a menu of widgets, and allow selection.
        if len(widgetlist) == 0:
            print("did not select widget - try again!")
            event.accept()
            return

        if len(widgetlist) == 1:
            if debug > 0: print(f"found widget {widgetlist[0]}")
            widget.selectedWidget = widgetlist[0]
        else:
            widget.selectedWidget = showWidgetMenu(widgetlist, event)

        if widget.selectedWidget == None:
            print("did not select widget - try again!")
            event.accept()
            return

        if widget.editMode(check="edit"):
            widget.edmShowEdit(widget.selectedWidget)
            widget.editMode(value="none")

        elif widget.editMode(check="move"):
            if widget.rubberband == None:
                widget.rubberband = edmRubberband(widget=widget.selectedWidget)
            else:
                widget.rubberband.active(widget.selectedWidget)
            if widget.selectedWidget.geometry().contains(pos):
                widget.rubberband.mousePressEvent(event)

        elif widget.editMode(check="resize"):
            # obsolete? covered by move/resize "move" mode
            if widget.rubberband == None:
                widget.rubberband = edmRubberband(widget=widget.selectedWidget)
            else:
                widget.rubberband.active(widget.selectedWidget)
            if widget.selectedWidget.underMouse():
                widget.rubberband.mousePressEvent(event)

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
        if ch.isWidgetType() and not ch.isWindow() and not ch.isHidden() and ch.geometry().contains(pos):
            point = ch.mapFromParent(pos)
            if ch.focusPolicy() != Qt.NoFocus:
                if debug>0 : print("Changing focus to:", ch)
                ch.setFocus()
            ch.mousePressEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
            found = True

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
    if not widget.editMode(check="none"):
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
    if widget.editMode(check="move") or widget.editMode(check="resize"):
        widget.rubberband.mouseMoveEvent(event)
        event.accept()
        return
    pos = event.pos()
    for ch in widget.buttonInterest:
        if ch.isWidgetType() and not ch.isWindow() and not ch.isHidden() and ch.geometry().contains(pos):
            point = ch.mapFromParent(pos)
            ch.mouseMoveEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
    # in normal mode, check hover possibilities
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


def showWidgetMenu(widgetlist, event):
    menu = edmEditWidgetMenu(edmWidgets=widgetlist)
    menu.exec_(event.globalPos())
    return menu.selected


def generateWidget(screen, parent):
    '''
     generate widgets based on the screen description. The expectation is that 'parent'
     is a container widget and the widgets generated from screen.objectList will be
     built within parent.
    '''
    if edmApp.debug() : print("generateWidget", screen, parent, getattr(parent,"macroTable", None))
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


