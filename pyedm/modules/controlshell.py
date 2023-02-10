from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# This module runs a shell command.

#
# there are a number of important considerations. The most important
# is the management of the macros, so that macro expansion occurs using
# the correct macro set.
#
from builtins import range
import os
from threading import Thread
from .edmApp import edmApp
from .edmWidget import edmWidget
from .edmField import edmField, edmTag
from .edmEditWidget import edmEdit

from PyQt5.QtWidgets import QPushButton, QMenu
from PyQt5.QtGui import QPalette
#from PyQt5.QtCore import SIGNAL

class popUpMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

class shellThread(Thread):
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        os.system(self.cmd)

class shellCmdClass(QPushButton,edmWidget):
    menuGroup = [ "control", "Shell Command" ]
    edmEntityFields = [
            edmField("numCmds", edmEdit.Int, hidden=True),
            edmField("command", edmEdit.String, array=True),
            edmField("commandLabel", edmEdit.String, array=True),
            edmField("buttonLabel", edmEdit.String),
            edmField("invisible", edmEdit.Bool, defaultValue=False)
            ] + edmWidget.edmFontFields
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def setV3PropertyList(classRef, values, obj):
        for name in [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "command0", "buttonLabel", "font", "invisible", "closeDisplay", "autoExecPeriod", "multipleInstances",
            "initialDelay", "password", "lock", "label0", "numCmds" ]:
            obj.addTag(name, values.pop(0))

        cmd = [obj.tags['command0'].value ]
        label = [obj.tags['label0'].value ]
        for idx in range(1, int(tag['numCmds']).value ):
            cmd.append( values.pop(0))
            label.append( values.pop(0) )

        obj.addTag( "commandLabel", label)
        obj.addTag("command", cmd)

        obj.addTag( "requiredHostName", values.pop(0))
            
    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        name = self.objectDesc.getProperty("buttonLabel")
        if name != None:
            self.setText(name)
        if self.objectDesc.getProperty("invisible"):
            self.transparent = True
            self.setFlat(1)
                                            
        self.numCmds = objectDesc.getProperty("numCmds")
        self.cmdLabel = objectDesc.getProperty("commandLabel", arrayCount=self.numCmds)
        self.command = objectDesc.getProperty("command", arrayCount=self.numCmds)
        self.threads = [None]*self.numCmds
        if self.cmdLabel == None:
            self.cmdLabel = self.command
        if len(self.cmdLabel) == 1:
            self.pressed.connect(self.onPress)
        else:
            self.newmenu = popUpMenu(self)
            self.setMenu(self.newmenu)
            self.actions = [ self.newmenu.addAction(menu, lambda idx=idx:self.onMenu(idx)) for (idx,menu) in enumerate(self.command) ]
        self.edmParent.buttonInterest.append(self)

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText,))
        self.fgColorInfo.setColor()
    
    def findBgColor(self):
        self.bgColorInfo = self.findColor("bgColor", (QPalette.Button,))
        self.bgColorInfo.setColor()

    def onPress(self):
        self.onMenu(0)

    def onMenu(self, idx):
        print(f"onMenu({idx}) => {self.command[idx]}")
        if self.threads[idx] and self.threads[idx].is_alive():
            print("Unable to run multiple instances of {self.command[idx]}")
            # To Do. Support for multiple "exec's" of a command.
            return

        self.threads[idx] = shellThread(self.command[idx])
        self.threads[idx].daemon = True

        self.threads[idx].start()

    def lostChild(self, childIdx):
        print("lost child", childIdx)
        self.widgets[childIdx] = None
        
edmApp.edmClasses["shellCmdClass"] = shellCmdClass

