from __future__ import print_function
from __future__ import absolute_import
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication, QClipboard
from .edmWidgetSupport import edmWidgetSupport
from .edmWidget import edmWidget
# A simple top-level widget, and support for managing mouse buttons.
#

class edmWindowWidget(QtWidgets.QWidget, edmWidgetSupport):
    '''Widget that manages mouse clicks on behalf of children'''
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.edmParent = parent
        self.editMode = False            # edit mode might be able to work 'better' in pyEdm, but need to support saving embedded windows!
        self.selectedWidget = None      # set to the edmWidget entry that's been selected in edit mode; must be a descendant of this widget.
        self.focusedWidget = None       # if hovering over a widget, check that we're still over the same widget.
        self.propertyWindow = None      # the propertyWindow for selectedWidget
        self.buttonInterest = []

    def mousePressEvent(self, event):
        mousePressEvent(self, event, editMode=self.editMode)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event, editMode=self.editMode)

    def mouseMoveEvent(self, event):
        # in edit mode, if selectedWidget set, then adjust the widget's position
        if self.editMode:
            if self.selectedWidget == None: return
            event.accept()
            return
        # in normal mode, check hover possibilities
        pass
        event.accept()

def mousePressEvent(widget, event, editMode=False):
    debug = getattr(widget, "DebugFlag", 0)

    if editMode:
        # if right mouse in edit mode, only allow menu selection
        if event.button() == Qt.RightButton:
            showBackgroundMenu(widget, event)
            event.accept()
            return
        # check if clicking a selected widget. If so, then bring up the properties window.
        pos = event.pos()
        if self.selectedWidget:
            if self.selectedWidget.geometry().contains(pos):
               self.propertyWindow = edmShowEdit(self.selectedWidget)
        else:
            widgetlist = []
            for ch in widget.children():
                if isinstance(ch, edmWidget) and not ch.isWindow() and ch.geometry().contains(pos):
                    widgetlist.append(ch)

            # opportunity for improvement: 
            if len(widgetlist) > 0:
                self.selectedWidget = widgetlist[0]

        event.accept()
        return

    if event.button() == Qt.MidButton:
        if findDragName(widget, event.pos()) :
            event.accept
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
    # if a right button click, generate an "edm" menu
    if event.button() == Qt.RightButton:
        showBackgroundMenu(widget, event)
        event.accept()
        return
    # Potential: evaluate other mouse clicks that didn't get a widget

def mouseReleaseEvent(widget, event, editMode=False):
        pos = event.pos()
        for ch in widget.buttonInterest:
            if ch.isWidgetType() and not ch.isWindow() and not ch.isHidden() and ch.geometry().contains(pos):
                point = ch.mapFromParent(pos)
                ch.mouseReleaseEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
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
        for item in list(ch.pvItem.values()):
            pv = getattr(ch, item[1], None)
            if pv == None:
                continue

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

def showBackgroundMenu(widget, event):
    pass
