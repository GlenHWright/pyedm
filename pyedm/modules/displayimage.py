from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module loads and displays images. Note that it handles
# both 'gif' and 'png', and is capable of being extended based on
# the capabilities of the QImage(file) constructor

import os
from pathlib import Path
from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmAbstractShape import abstractShape
from .edmField import edmField
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QImage

class activeImageClass(abstractShape):
    menuGroup = ["display", "Image"]
    edmEntityFields = [
            edmField("file", edmEdit.String, None),
            edmField("refreshRate", edmEdit.Int, 0),
            edmField("uniformSize", edmEdit.Bool, False),
            edmField("fastErase", edmEdit.Bool, False),
            edmField("noErase", edmEdit.Bool, False)
            ]
    edmFieldList = abstractShape.edmBaseFields + edmEntityFields + abstractShape.edmVisFields
    V3propTable = {
        "1-2" : [ "file", "refreshRate", "uniformSize", "fastErase" ]
        }
    def __init__(self, *args, **kwargs):
        if edmApp.DebugFlag > 0 : print("activeImageClass __init()__", self, args, kwargs)
        super().__init__(*args,**kwargs)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        self.filename = objectDesc.getProperty("file", None)
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

    def findFgColor(self):
        return None

    def paintEvent(self, event=None):
        painter = QPainter(self)
        if event == None:
            painter.eraseRect(0, 0, self.width(), self.height() )
        if self.image != None:
            painter.drawImage(0, 0, self.image)
        
edmApp.edmClasses["cfcf6c8a_dbeb_11d2_8a97_00104b8742df"] = activeImageClass
edmApp.edmClasses["activePngClass"] = activeImageClass

