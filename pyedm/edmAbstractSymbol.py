# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Abstract symbolClass to use portions of an edl file based
# on the top level groups within the file
#
# Any class inheriting 'AbstractSymbolClass' must have a field of 'statelist'
# of the length of the number of supported states.
#
import pyedm.edmDisplay as edmDisplay
from pyedm.edmApp import redisplay
from pyedm.edmScreen import edmScreen
from pyedm.edmWidget import edmWidget

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QWidget, QFrame, QScrollArea, QPalette, QPainter

class symbolWidget(QWidget,edmWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        edmWidget.__init__(self,parent)

class AbstractSymbolClass(QFrame,edmWidget):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        edmWidget.__init__(self, parent)
        #self.setLineWidth(2)
        #self.setFrameShape(QFrame.Panel|QFrame.Sunken)
        self.parentx = 0
        self.parenty = 0
        self.scr = None
        self.buttonInterest = []
        self.edmParent.buttonInterest.append(self)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)

    def buildStateObjects(self, filename, macroTable=None):
        self.edmScreen = edmScreen(filename, macroTable, self.findDataPaths() )
        # build a list of items from the file
        self.stateObjects = []
        for item in self.edmScreen.objectList:
            if item.tagValue["Class"] == "activeGroupClass":
                self.stateObjects.append(item)

        # Opportunity For Confusion:
        # Qt Widgets are relative to their parent. EDM widgets are relative to
        # the screen they're on.
        # So, the group widget needs to be changed to '0,0'. All children widgets
        # must have their x,y adjusted by the group offset.
        # Because the widgets haven't been built yet, the object tagValues will be
        # updated.
        self.macroTable = getattr(self.edmParent, "macroTable", None)
        for item in zip(self.stateObjects,self.statelist):
            groupx = item[0].getIntProperty("x", 0)
            groupy = item[0].getIntProperty("y", 0)
            self.moveItem(item[0], groupx, groupy)
            item[1].widgets = symbolWidget(self)
            item[1].widgets.parentx = 0
            item[1].widgets.parenty = 0
            edmDisplay.generateWidget(item[0], item[1].widgets)
            self.buttonInterest.append(item[1].widgets)
            item[1].widgets.hide()
        self.lastState = None
        self.curState = self.statelist[0]

    def moveItem(self, item, offx, offy):
        myx = item.getIntProperty("x", 0)
        myy = item.getIntProperty("y", 0)
        item.tagValue["x"] = str(myx-offx)
        item.tagValue["y"] = str(myy-offy)
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

