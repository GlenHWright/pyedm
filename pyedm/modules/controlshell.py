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
import pyedm.edmDisplay as edmDisplay
from pyedm.edmWidget import edmWidget

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
    def __init__(self, parent=None):
        super().__init__(parent)

    def setV3PropertyList(classRef, values, tag):
        for name in [ "INDEX", "fgColor", "INDEX", "bgColor", "INDEX", "topShadowColor", "INDEX", "botShadowColor",
            "command0", "buttonLabel", "font", "invisible", "closeDisplay", "autoExecPeriod", "multipleInstances",
            "initialDelay", "password", "lock", "label0", "numCmds" ]:
            tag[name] = values.pop(0)

        cmd = [tag['command0'] ]
        label = [tag['label0'] ]
        for idx in range(1, int(tag['numCmds']) ):
            cmd.append( value.pop(0))
            label.append( value.pop(0) )

        tag['commandLabel'] = label
        tag['command'] = cmd

        tag['requiredHostName'] = value.pop(0)
            
    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.update()
        name = self.object.getStringProperty("buttonLabel", None)
        if name != None:
            self.setText(name)
        if self.object.getIntProperty("invisible",0) == 1:
            self.transparent = 1
            self.setFlat(1)
                                            
        self.numCmds = object.getIntProperty("numCmds")
        self.cmdLabel = object.decode("commandLabel", self.numCmds)
        self.command = object.decode("command", self.numCmds)
        self.threads = [None]*self.numCmds
        if self.cmdLabel == None:
            self.cmdLabel = self.command
        if len(self.cmdLabel) == 1:
            #self.connect(self, SIGNAL("pressed()"), self.onPress)
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
        print("onMenu(", idx , ")")
        if self.threads[idx] and self.threads[idx].isAlive():
            # To Do. Support for multiple "exec's" of a command.
            return

        self.threads[idx] = shellThread(self.command[idx])
        self.threads[idx].daemon = True

        self.threads[idx].start()

    def lostChild(self, childIdx):
        print("lost child", childIdx)
        self.widgets[childIdx] = None
        
edmDisplay.edmClasses["shellCmdClass"] = shellCmdClass

