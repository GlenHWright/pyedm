from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module loads and displays images. Note that it handles
# both 'gif' and 'png', and is capable of being extended based on
# the capabilities of the QImage(file) constructor

import pyedm.edmDisplay as edmDisplay
import os
from pathlib import Path
from pyedm.edmApp import edmApp
from pyedm.edmWidget import edmWidget
from pyedm.edmAbstractShape import abstractShape

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QImage

class activeImageClass(abstractShape):
    V3propTable = {
        "1-2" : [ "file", "refreshRate", "uniformSize", "fastErase" ]
        }
    def __init__(self, *args, **kwargs):
        if edmApp.DebugFlag > 0 : print("activeImageClass __init()__", self, args, kwargs)
        super().__init__(*args,**kwargs)

    def buildFromObject(self, objectDesc):
        edmWidget.buildFromObject(self, objectDesc)
        self.filename = objectDesc.getStringProperty("file", None)
        self.filename = self.macroExpand(self.filename)
        self.image = None
        for path in edmApp.dataPaths:
            fn = os.path.join(path, self.filename)
            for remap in edmApp.remap:
                if fn.startswith(remap[0]):
                    fn = fn.replace(remap[0], remap[1], 1)

            for suffix in [ "", ".png", ".gif" ] :
                if Path(fn + suffix).is_file():
                    self.image = QImage(fn)
                    break
            if self.image != None:
                break

        if self.image == None:
            print("file not found", self.filename, "in", edmApp.dataPaths, "last tried:", fn)

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        if self.image != None:
            painter.drawImage(0, 0, self.image)
        
edmDisplay.edmClasses["cfcf6c8a_dbeb_11d2_8a97_00104b8742df"] = activeImageClass
edmDisplay.edmClasses["activePngClass"] = activeImageClass

