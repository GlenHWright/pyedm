from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module loads and displays images. Note that it handles
# both 'gif' and 'png', and is capable of being extended based on
# the capabilities of the QImage(file) constructor

import pyedm.edmDisplay as edmDisplay
import os
from pyedm.edmApp import edmApp
from pyedm.edmWidget import edmWidget
from pyedm.edmAbstractShape import abstractShape
from pyedm.edmEditWidget import edmEdit

from PyQt4.QtGui import QFrame, QPainter, QImage

class activeImageClass(abstractShape):
    V3propTable = {
        "1-2" : [ "file", "refreshRate", "uniformSize", "fastErase" ]
        }

    edmEditList = [
        edmEdit.String("GIF File", "file"),
        edmEdit.Int("Refresh Rate (ms)", "refreshRate"),
        edmEdit.CheckButton("Uniform Size", "uniformsize"),
        edmEdit.CheckButton("Fast Erase", "fastErase")
        ]

    def __init__(self, parent=None):
        abstractShape.__init__(self,parent)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self, object)
        self.filename = object.getStringProperty("file", None)
        self.filename = self.macroExpand(self.filename)
        self.image = None
        for path in edmApp.dataPaths:
            fn = os.path.join(path, self.filename)
            try:
                os.stat(fn)
                self.image = QImage(fn)
                break
            except OSError:
                pass
        if self.image == None:
            print("Invalid filename:", self.filename)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        if self.image != None:
            painter.drawImage(0, 0, self.image)
        
edmDisplay.edmClasses["cfcf6c8a_dbeb_11d2_8a97_00104b8742df"] = activeImageClass
edmDisplay.edmClasses["activePngClass"] = activeImageClass

