# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: mid
#
# This is a mid-level module
# called from edmWindowWidget, edmParentSupport
#
# does general support of mouse input.
#
# Consider rewriting as a mixin
#

from enum import Enum

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication, QClipboard

from .edmApp import edmApp
from .edmEditWidget import edmRubberband, edmEdit
from .edmObject import edmObject

def mousePressEvent(widget, event):
    ''' mousePressEvent - handle mouse press events in a generic manner for EDM
    '''
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
        edmApp.showBackgroundMenu(widget, event)
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
    '''return a list of edm children at all levels of this widget
        pos is the current position in the defined widget'''
    widgetlist = []
    for ch in widget.children():
        if edmApp.debug() : print(f"check widget {widget} child {ch} point {pos} geometry {getattr(ch, 'geometry', lambda:'-')()}")
        if isinstance(ch, edmApp.edmWidget) and not ch.isWindow() and ch.geometry().contains(pos):
            widgetlist.append(ch)
            widgetlist += findEdmChildren(ch, ch.mapFrom(widget,pos))

    return widgetlist

def findActionWidget(parent, pos, debug=0):
    ''' findActionWidget - checks to see if there's a widget under the global position 'pos'
            that is a child of parent. Uses 'findEdmChildren'.
    '''
    widgetlist = findEdmChildren(parent, pos)
    if debug > 0 : print(f"findEdmChildren({parent}...) returns {widgetlist}")

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
    elif parent.editMode(check="cut"):
        parent.edmCutChild(parent.selectedWidget)
        parent.editMode(value="none")
    elif parent.editMode(check="copy"):
        cutcopy = edmObject().edmCopy(parent.selectedWidget.objectDesc)
        edmApp.cutCopyList = [cutcopy]
        parent.editMode(value="none")
    elif parent.editMode(check="raise"):
        parent.selectedWidget.raise_()
        parent.editMode(value="none")
    elif parent.editMode(check="lower"):
        parent.selectedWidget.lower()
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
