# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a group display class
#

from .edmApp import edmApp
from .edmWindowWidget import edmWindowWidget, mousePressEvent, mouseReleaseEvent, mouseMoveEvent
from .edmWidget import edmWidget
from .edmParentSupport import edmParentSupport

from PyQt5 import QtWidgets

class activeGroupClass(QtWidgets.QWidget, edmParentSupport, edmWidget):
    menuGroup = [ "display", "Group" ]
    '''group display widget
        because the data input is handled by the edmScreen module, there isn't much to
        do at this level, and there is no need of alternate file input handling here'''
    def __init__(self, parent=None, **kw):
        #super().__init__(parent, **kw)
        QtWidgets.QWidget.__init__(self, parent)
        edmWidget.__init__(self, parent)
        edmParentSupport.__init__(self, parent)
        if self.debug() : print(f"activeGroupClass __init__ {self}")

    def __repr__(self):
        ch = self.children()
        if len(ch) == 0:
            ch = "Empty"
        else:
            ch = ch[0]
        return f"<activeGroup {ch}...>"

    def edmCleanup(self):
        self.buttonInterest = []
        super().edmCleanup()

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject( objectDesc, **kw)
        self.parentx = int(objectDesc.getProperty("x")*edmApp.rescale)
        self.parenty = int(objectDesc.getProperty("y")*edmApp.rescale)
        self.macroTable = getattr(self.edmParent, "macroTable", None)
        # specific check here rather than 'try'
        # so we don't mask out AttributeError
        # from lower level calls.
        if not hasattr(self.objectDesc, "objectList"):
            self.objectDesc.objectList = []
        edmApp.generateWidget(self.objectDesc, self)
        # Unknown level of nesting, so the assumption is made that
        # this widget could contain something that would like
        # a mouse message
        self.edmParent.buttonInterest.append(self)

    def mousePressEvent(self, *args, **kw):
        mousePressEvent(self, *args, **kw)

    def mouseReleaseEvent(self, *args, **kw):
        mouseReleaseEvent(self, *args, **kw)

    def mouseMoveEvent(self, *args, **kw):
        mouseMoveEvent(self, *args, **kw)

    def redisplay(self):
        self.checkVisible()

    def findFgColor(self):
        return None

    def findBgColor(self):
        return None

edmApp.edmClasses["activeGroupClass"] = activeGroupClass
