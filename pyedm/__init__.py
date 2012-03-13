# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# If opened as 'main', use our mainline
#

from __future__ import print_function

if __name__ == "__main__":
    print( """To call pyedm as a script rather than a module,
use 'python -m edm [edmargs...]'.""") 
    exit()

# Standard 'main' imports

import sys
import getopt
import glob
import os
import threading

# pyedm imports
from pyedm.edmApp import edmApp
import pyedm.edmDisplay as edmDisplay
from pyedm.edmScreen import edmScreen, readInput
from pyedm.edmMacro import macroDictionary
from pyedm.edmColors import findColorRule

# Mainline
# loads all the windows, and starts a QT application.
#
def pyedm_main(argv):
    """pyedm_main(argv) - start QT, and load flags"""
    from PyQt4 import QtGui

    style = QtGui.QStyleFactory.create("plastique")
    QtGui.QApplication.setStyle(style)
    app = QtGui.QApplication(sys.argv)

    pyedm(argv)

    if len(edmApp.windowList) == 0:
        print ("No Windows. Exiting.")
        exit()

    app.exec_()

# Called to load screens. 
# Interprets a subset of EDM flags.
# a Qt app must be in existance before pyedm is called.
#
def pyedm(argv):
    """pyedm(argv) - interpret EDM flags, and load screens"""
    mt = macroDictionary()
    mt.addMacro("!W", "!W%d" % ( mt.myid,) )
    mt.addMacro("!A", "!A1")
    try:
        opts, args = getopt.getopt(argv,"hdm:")
    except getopt.GetoptError:
        print ('getopt failure...')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            pass
        elif opt == "-m":
            mt.macroDecode(arg)
        elif opt == "-d":
            edmApp.DebugFlag = edmApp.DebugFlag+1
            print ("global debugging enabled")

    # Each argument is taken as a file name. Each file name will generate one
    # window.
    for files in args:
        scr = edmScreen(files, mt)
        if scr.valid():
            edmApp.screenList.append(scr)

    # All the file arguments have been read. Generate the screens.
    #

    for scr in edmApp.screenList :
        window = edmDisplay.generateWindow(scr,macroTable=mt)
        edmApp.windowList.append(window)

    edmApp.startTimer()
    return 0

def loadScreen(fileName, macros="", parentWidget=None, parentDictionary=None, dataPaths=None, debugFlag=None):
    if debugFlag != None:
        edmApp.DebugFlag = debugFlag
    mt = macroDictionary(parentDictionary)
    mt.addMacro("!W", "!W%d" % ( mt.myid,) )
    mt.macroDecode(macros)
    if dataPaths != None: dataPaths = dataPaths.split(";")
    scr = edmScreen(fileName, macroTable=mt, paths=dataPaths)
    if scr.valid():
        edmApp.screenList.append(scr)
        if parentWidget == None:
            # No parent widget, just display the screen
            window = edmDisplay.generateWindow(scr, macroTable=mt,paths=dataPaths)
            edmApp.windowList.append(window)
        else:
            # a parent widget, we'll just load the screen
            parentWidget.macroTable = mt
            parentWidget.dataPaths = dataPaths
            pal = parentWidget.palette()
            try:
                parentWidget.fgRule = findColorRule(scr.tagValue["fgColor"])
                pal.setColor( parentWidget.foregroundRole(), parentWidget.fgRule.getColor() )
            except: pass
            try:
                parentWidget.bgRule = findColorRule(scr.tagValue["bgColor"])
                pal.setColor( parentWidget.backgroundRole(), parentWidget.bgRule.getColor() )
            except: pass
            parentWidget.setPalette(pal)
            edmDisplay.generateWidget(scr, parentWidget)

# Prevent duplication on names: if there are (e.g.) multiple edmPVepics.py files
# in the path, the first one gets imported, and then myImports[] flags 'edmPVepics'
# as having been imported.
myImports = []

def genImport(pattern):
    global myImports
    files = glob.glob(pattern)
    for fname in files:
        if not fname.endswith(".py"):
            continue
        head, tail = os.path.split(fname[0:-3])
        if tail in myImports:
            continue
        myImports.append(tail)
        path = sys.path[:]
        sys.path.insert(0,  head)
        if head not in __path__:
            __path__.insert(0,head)
        __import__(tail, globals(), locals(), [], 1 )
        sys.path = path

searchPath = [".", __path__[0], os.path.join(__path__[0],"modules") ]
# Note that ';' is used to allow Windows "C:\path" style to be valid.
if "PYTHONEDMPATH" in os.environ:
    searchPath = os.environ["PYTHONEDMPATH"].split(";") + searchPath
for path in searchPath:
    genImport(os.path.join(path,"edmPV*"))
    genImport(os.path.join(path,"display*.py"))
    genImport(os.path.join(path,"monitor*.py"))
    genImport(os.path.join(path,"control*.py"))

