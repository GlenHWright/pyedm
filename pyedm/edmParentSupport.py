# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.

# MODULE LEVEL: high
#
# Provides common tools for items that contain sub-items
#
from enum import Enum

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import QApplication, QClipboard

from .edmApp import edmApp
from .edmWidget import edmWidget, buildNewWidget
from .edmEditWidget import edmShowEdit, edmRubberband, edmEdit
from .edmScreen import edmScreen
from .edmColors import findColorRule
from .edmField import edmField, edmTag
from . import edmMouseHandler
#
# A support widget for code common to any widget that is a parent to other edm widgets
# Any widget that inherits from here will provide mouse support and child edit support
#

editModeEnum = Enum("editmode", "none edit move copy cut paste")
class edmParentSupport:
    '''edmParentSupport - common interface for container widgets
        manage mouse clicks on behalf of children'''
    def __init__(self, parent=None, **kwargs):
        self.edmParent = parent
        self.editModeValue = editModeEnum.none      # edit mode might be able to work 'better' in pyEdm, but need to support saving embedded windows!
        self.selectedWidget = None      # set to the edmWidget entry that's been selected in edit mode; must be a descendant of this widget.
        self.rubberband = None          # if set, then this is a resize/move widget.
        self.focusedWidget = None       # if hovering over a widget, check that we're still over the same widget.
        self.buttonInterest = []
        self.edmEditList = []


    def edmCleanup(self):
        # To Do: add check for unsaved changes
        #
        if self.rubberband:
            rb, self.rubberband = self.rubberBand, None
            rb.destroy()
            rb = None
        self.edmParent = None
        self.selectedWidget = None
        self.focusedWidget = None
        self.buttonInterest.clear()
        self.edmEditList.clear()

        for child in self.children():
            try:
                child.edmCleanup()
            except AttributeError as exc:
                print(f"WindowWidget edmCleanup: child {child} lacking edmCleanup! {exc}")
        try:
            edmApp.windowList.remove(self)
        except ValueError as exc:
            # some widgets always generate this (e.g. group widgets). There must be a better way
            if self.debug() : print(f"Unable to remove windowWidget {self} from window list -- already gone!")

        self.destroy()

    def editMode(self, *,check="none", value=None):
        if edmApp.debug(): print(f"edmParentSupport editMode {self} {check} {value}")
        if value != None:
            self.editModeValue = editModeEnum[value]
            if value == "none":
                self.selectedWidget = None
        return self.editModeValue == editModeEnum[check]

    def edmShowEdit(self, thisWidget):
        if edmApp.debug(): print(f"add {thisWidget} to {self} {self.edmEditList}")
        if thisWidget not in self.edmEditList:
            self.edmEditList.append(thisWidget)
            thisWidget.showEditWindow = edmShowEdit(thisWidget, self)
        else:
            try:
                thisWidget.showEditWindow.show()
            except BaseException as exc:
                print(f"failed to display edit window: reason {exc}")

    def edmHideEdit(self, edmEditWindow):
        ''' remove widget from editing list
        '''
        if edmApp.debug(): print(f"remove {edmEditWindow} from {self} {self.edmEditList}")
        if edmEditWindow in self.edmEditList:
            edmEditWindow.showEditWindow = None
            self.edmEditList.remove(edmEditWindow)

class windowMenu(QtWidgets.QMenu):
    '''
        windowMenu.
        class for custom window menu
        Displays on the WindowMenu background or on widgets
        that have set the .WA_TransparentForMouseEvents
        attribute.
    '''
    def __init__(self, *args, edmWidget=None, position=None, **kw):
        super().__init__(*args, **kw)
        self.edmWidget = edmWidget
        self.position = position
        self.addSection(str(edmWidget))
        self.setMenuAction("Edit", self.selectEdit)
        self.setMenuAction("Move/Resize", self.moveMode)
        self.setMenuAction("Widget Copy", self.copy)
        self.setMenuAction("Widget Paste", self.paste)
        self.setMenuAction("Widget Cut", self.cut)
        self.buildNewWidgetMenu(self.addMenu("New Widget"))
        self.setMenuAction("Edit Screen", self.editScreen)
        self.setMenuAction("Save", self.saveWindow)
        self.setMenuAction("Save As ...", self.saveAsWindow)
        self.setMenuAction("Open...", self.openWindow)
        self.setMenuAction("New Window", self.newWindow)
        self.setMenuAction("Reset", self.edmReset)

    def setMenuAction(self, name, perform):
        action = self.addAction(name)
        action.triggered.connect(perform)

    def selectEdit(self):
        self.edmWidget.editMode(value="edit")
        edmMouseHandler.findActionWidget(self.edmWidget, self.position)

    def moveMode(self):
        self.edmWidget.editMode(value="move")
        edmMouseHandler.findActionWidget(self.edmWidget, self.position)

    def newWindow(self):
        edmApp.buildNewWindow()

    def editScreen(self):
        self.edmWidget.edmShowEdit(self.edmWidget)
        
    def saveWindow(self):
        try:
            self.edmWidget.getParentScreen().saveToFile()
        except BaseException as exc:
            print(f"Unable to save file for {self.edmWidget}\nBecause {exc}")

    def saveAsWindow(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(parent=self.edmWidget, 
                caption="Save To...", filter="JSON edl (*.jedl)")
        try:
            filename = filename[0]
            self.edmWidget.getParentScreen().saveToFile(filename)
        except BaseException as exc:
            print(f"Unable to save file for {self.edmWidget}\nBecause {exc}")

    def openWindow(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(parent=self.edmWidget, 
                caption="Open...", filter="JSON edl (*.jedl);;edl (*.edl)")
        try:
            filename = filename[0]
            mt = edmApp.macroTable
            scr = edmScreen(filename, mt)
            if scr.valid():
                edmApp.screenList.append(scr)
                window = edmApp.generateWindow(scr,macroTable=mt)
                edmApp.windowList.append(window)
        except BaseException as exc:
            print(f"Unable to open file {filename}\n     because {exc}")

    def copy(self):
        self.edmWidget.editMode(value="copy")
        edmMouseHandler.findActionWidget(self.edmWidget, self.position)

    def paste(self):
        self.edmWidget.editMode(value="paste")

    def cut(self):
        self.edmWidget.editMode(value="cut")
        edmMouseHandler.findActionWidget(self.edmWidget, self.position)

    def edmReset(self):
        self.edmWidget.editMode(value="none")

    def buildNewWidgetMenu(self, parentMenu):
        namemap = {}
        namemap["display"] = parentMenu.addMenu("display")
        namemap["monitor"] = parentMenu.addMenu("monitor")
        namemap["control"] = parentMenu.addMenu("control")
        for clsName,cls in edmApp.edmClasses.items():
            action = namemap[cls.menuGroup[0]].addAction(cls.menuGroup[1])
            action.triggered.connect(
                    lambda action,clsName=clsName,cls=cls, position=self.position:
                        buildNewWidget(parent=self.edmWidget,source=clsName,widgetClassRef=cls,position=position)
                    )


def showBackgroundMenu(widget, event):
    ''' show a background menu for a widget.
        to do - ensure widget is a window widget
    '''
    if edmApp.allowEdit is False:
        return
    menu = windowMenu(edmWidget=widget, position=event.pos())
    menu.exec_(event.globalPos())
    menu.edmWidget = None

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

#####
##### Over-write placeholders
#####
edmApp.showBackgroundMenu = showBackgroundMenu
