# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Abstract symbolClass to use portions of an edl file based
# on the top level groups within the file
#
# MODULE LEVEL: high
#
# Any class inheriting 'AbstractSymbolClass' must have a field of 'statelist'
# of the length of the number of supported states.
#
from .edmWindowWidget import generateWidget
from .edmApp import redisplay
from .edmScreen import edmScreen
from .edmWidget import edmWidget

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea
from PyQt5.QtGui import QPalette, QPainter

class symbolWidget(QWidget,edmWidget):
    def __init__(self, parent=None, **kw):
        super().__init__(parent, **kw)

class AbstractSymbolClass(QFrame,edmWidget):
    def __init__(self, parent=None, **kw):
        super().__init__(parent, **kw)
        #self.setLineWidth(2)
        #self.setFrameShape(QFrame.Panel|QFrame.Sunken)
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def buildStateObjects(self, filename, macroTable=None):
        '''
           load the named file, and search out all objects that define groups.
        '''
        self.edmScreen = edmScreen(filename, macroTable, self.findDataPaths() )
        # build a list of items from the file
        self.stateObjects = []
        for item in self.edmScreen.objectList:
            if item.tags["Class"].value == "activeGroupClass":
                self.stateObjects.append(item)

        # Opportunity For Confusion:
        # Qt Widgets are relative to their parent. EDM widgets are relative to
        # the screen they're on.
        # So, the group widget needs to be changed to '0,0'. All children widgets
        # must have their x,y adjusted by the group offset.
        # Because the widgets haven't been built yet, the object tags will be
        # updated. code is ugly because we're skipping a step
        self.macroTable = getattr(self.edmParent, "macroTable", None)
        for s_obj, s_item in zip(self.stateObjects,self.statelist):
            groupx = int(s_obj.tags["x"].value)
            groupy = int(s_obj.tags["y"].value)
            self.moveItem(s_obj, groupx, groupy)
            s_item.widgets = symbolWidget(self)
            s_item.widgets.parentx = 0
            s_item.widgets.parenty = 0
            generateWidget(s_obj, s_item.widgets)
            self.buttonInterest.append(s_item.widgets)
            s_item.widgets.hide()
        self.lastState = None
        self.curState = self.statelist[0]

    def moveItem(self, item, offx, offy):
        myx = int(item.tags["x"].value)
        myy = int(item.tags["y"].value)
        item.tags["x"].value =  str(myx-offx)
        item.tags["y"].value =  str(myy-offy)
        if hasattr(item, "objectList"):
            for subItem in item.objectList:
                self.moveItem(subItem, offx, offy)

    def redisplay(self):
        self.checkVisible()
        if self.curState == self.lastState:
            return
        if hasattr(self.curState, "widgets") == False:
            return
        if self.lastState != None:
            self.lastState.widgets.hide()
        self.curState.widgets.show()
        self.lastState = self.curState

