# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QEvent, QObject
from PyQt4.Qt import QApplication, QClipboard
from PyQt4.QtGui import QMenu
from edmWidgetSupport import edmWidgetSupport
from edmWidget import edmWidget
from edmEditWidget import edmEditWidget
# from __future__ import print_function
# A simple top-level widget, and support for managing mouse buttons.
#

class edmWindowWidget(QtGui.QWidget, edmWidgetSupport):
    '''Widget that manages mouse clicks on behalf of children'''
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        edmWidgetSupport.__init__(self)
        self.editMode = False            # edit mode might be able to work 'better' in pyEdm, but need to support saving embedded windows!
        self.selectedWidget = []      # set to the edmWidget entry that's been selected in edit mode; must be a descendant of this widget.
        self.focusedWidget = None       # if hovering over a widget, check that we're still over the same widget.
        self.propertyWindow = None      # the propertyWindow for selectedWidget
        self.buttonInterest = []
        self.backgroundMenuEdit = edmBackgroundMenuHandler(parent=self, edit=True)
        self.backgroundMenuRun = edmBackgroundMenuHandler(parent=self, edit=False)

    def mousePressEvent(self, event):
        mousePressEvent(self, event, editMode=self.editMode)

    def mouseReleaseEvent(self, event):
        mouseReleaseEvent(self, event, editMode=self.editMode)

    def mouseMoveEvent(self, event):
        # in edit mode, if selectedWidget set, then adjust the widget's position
        if self.editMode:
            if len(self.selectedWidget) == 0: return
            event.accept()
            return
        # in normal mode, check hover possibilities
        pass
        event.accept()

    def getEditMode(self):
        return self.editMode

    def setEditMode(self, filter=None):
        '''don't install filter on 'self', as the mouse event is used to trigger
           the menu for switching to execute mode
        '''
        self.editMode = True
        self.filter = edmEditMouseFilter()
        for ch in self.children():
            ch.setEditMode(self.filter)

    def setExecuteMode(self):
        self.editMode = False
        for ch in self.children():
            ch.setExecuteMode()
        self.filter = None

# NOTE: this is code that is also called from classes that don't inherit edmWindowWidget
# if it could be made to work properly in edmWidgetSupport (I didn't have success with that)
# then it could be moved there.
#
def mousePressEvent(widget, event, editMode=False):
    debug = getattr(widget, "DebugFlag", 0)


    if editMode:
        if not hasattr(widget, "selectedWidget"):
            return  # don't accept the event, this should punt the request to a different widget
        # if right mouse in edit mode, only allow menu selection
        if event.button() == Qt.RightButton:
            widget.backgroundMenuEdit.displayMenu(widget, event)
            event.accept()
            return
        # check if clicking a selected widget. If so, then bring up the properties window.
        pos = event.pos()
        search = True
        if len(widget.selectedWidget) > 0:
            if widget.selectedWidget[0].geometry().contains(pos):
               widget.propertyWindow = widget.selectedWidget[0].edmEditWidget(widget)
               widget.propertyWindow.show()
               search = False
        if search:
            widget.selectedWidget = []
            for ch in widget.children():
                if isinstance(ch, edmWidget) and not ch.isWindow() and ch.geometry().contains(pos):
                    widget.selectedWidget.append(ch)


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
                if debug>0 : print "Changing focus to:", ch
                ch.setFocus()
            ch.mousePressEvent( QtGui.QMouseEvent(event.type(), point, event.globalPos(), event.button(), event.buttons(), event.modifiers() ) )
            found = True

    if found:
        event.accept()
        return
    # if a right button click, generate an "edm" menu
    if event.button() == Qt.RightButton:
        try:
            widget.backgroundMenuRun.displayMenu(widget, event)
            event.accept()
        except:
            pass
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
        if hasattr(ch, "buttonInterest"):
            if findDragName(ch, ch.mapFromParent(pos)):
                return True
        if hasattr(ch, "pvItem") == False:
            continue
        for item in ch.pvItem.values():
            pv = getattr(ch, item[1], None)
            if pv == None:
                continue

            name = QtCore.QString(pv.getPVname())
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

class edmBackgroundMenuHandler(QMenu):
    def __init__(self, parent, edit=False):
        QMenu.__init__(self)
        self.parent = parent
        if edit:
            self.setEditActions()
        else:
            self.setRunActions()

    def setEditActions(self):
        self.addAction("Execute", self.onExecute)
        self.addAction("Save", self.onExecute)
        self.addAction("Save To Current Path", self.onExecute)
        self.addAction("Save As...", self.onExecute)
        self.addAction("Select All", self.onExecute)
        self.addAction("Paste (v)", self.onExecute)
        self.addAction("Paste in Place (V)", self.onExecute)
        self.addAction("Display Properties", self.onExecute)
        self.addAction("Close", self.onExecute)
        self.addAction("Open...", self.onExecute)
        self.addAction("Load Display Scheme...", self.onExecute)
        self.addAction("Save Display Scheme...", self.onExecute)
        self.addAction("Auto Make Symbol", self.onExecute)
        self.addAction("Edit Outliers", self.onExecute)
        self.addAction("Find Main Window", self.onExecute)
        self.addAction("Undo (z)", self.onExecute)
        self.addAction("Print...", self.onExecute)
        self.addAction("Refresh", self.onExecute)
        self.addAction("Help", self.onExecute)

    def setRunActions(self):
        self.addAction("Edit", self.onEdit)
        self.addAction("Open...", self.onEdit)
        self.addAction("Close", self.onEdit)
        self.addAction("Toggle Title", self.onEdit)
        self.addAction("Find Main Window", self.onEdit)
        self.addAction("Print...", self.onEdit)
        self.addAction("Refresh", self.onEdit)

    def displayMenu(self, widget=None, event=None):
        self.exec_(event.globalPos() )

    def onExecute(self):
            self.parent.setExecuteMode()

    def onEdit(self):
            self.parent.setEditMode()


#
# The challenge: mouse clicks almost always get eaten by the child, and not propogated to the parent. This is the expected result in "execute" mode,
# but not in "edit". This takes a captured mouse event and propogates the Press and Release events to the highest object.
#
class edmEditMouseFilter(QObject):
    '''when installed, throws away all mouse events
    '''
    def __init__(self):
        QObject.__init__(self)

    def eventFilter(self, obj, event):
        if event.type() in [ QEvent.MouseButtonPress, QEvent.MouseButtonRelease] :
            parent = getattr(obj,"edmParent", None)
            nextObj = None
            while parent:
                nextObj = parent
                parent = getattr(nextObj, "edmParent", None)

            if nextObj != None:
                newEvent = QtGui.QMouseEvent(event.type(), nextObj.mapFromGlobal(event.globalPos()), event.button(), event.buttons(), event.modifiers() )
                if event.type() == QEvent.MouseButtonPress:
                    nextObj.mousePressEvent( newEvent)
                else:
                    nextObj.mouseReleaseEvent( newEvent)
            return True

        if event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove, QEvent.MouseTrackingChange]:
            return True

        return False
