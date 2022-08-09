from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# If opened as 'main', use our mainline
#
if __name__ == "__main__":
    print("""To call pyedm as a script rather than a module,
use 'python -m edm [edmargs...]'.""")
    exit()

# Standard 'main' imports

import sys
import argparse
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
    from PyQt5 import QtWidgets

    style = QtWidgets.QStyleFactory.create("plastique")
    QtWidgets.QApplication.setStyle(style)
    app = QtWidgets.QApplication(sys.argv)

    pyedm(argv)

    if len(edmApp.windowList) == 0:
        print("No Windows. Exiting.")
        exit()

    app.exec_()

class remapAction(argparse.Action):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        setattr(self, args[1], [] )

    def __call__(self, parser, namespace, values, option_string=None):
        getattr(self, self.dest).append( values)
        

# Called to load screens. 
# Interprets a subset of EDM flags.
# a Qt app must be in existance before pyedm is called.
#
def pyedm(argv):
    """pyedm(argv) - interpret EDM flags, and load screens"""
    mt = macroDictionary()
    mt.addMacro("!W", "!W%d" % ( mt.myid,) )
    mt.addMacro("!A", "!A1")

    parser = argparse.ArgumentParser()

    parser.add_argument( "--macro", "-m", action="append", default=[], help='introduces list of macros/expansions e.g -m "facility=beamline-5,section=z"')
    parser.add_argument( "--debug", "-d", action="count", default=0, help="produces diagnostic output of window creation and PV creation")
    parser.add_argument( "--remap", nargs=2, action="append", default=[], help="--remap PATH NEWPATH remaps paths matching PATH to NEWPATH")

# following items are not implemented - either low priority or not applicable
    parser.add_argument( "--execute", "-x", action="count", help="(not implemented) Open all displays in execute rather than edit mode" )
    parser.add_argument( "--noedit", action="count",  help="(not implemented) Remove capability to put display in edit mode, used with  -x to produce execute only operation" )
    parser.add_argument( "--ctl", nargs=1, help="(not implemented)Takes name of string process variable, writing a display file name to this string causes edm to open the display in execute mode")
    parser.add_argument( "--color", help="(not implemented) Set Colormode - index (default) or rgb")
    parser.add_argument( "--cmap", action="count", help="(not implemented) use private colormap if necessary")
    parser.add_argument( "--restart", action="count", help="(not implemented) Takes PID number, restart from last shutdown")
    parser.add_argument( "--convert", action="count", help="(not implemented) Convert input file to new versin and exit")
    parser.add_argument( "--server", action="count", help="(not implemented) Communicate with or become a display file server which can manage multiple displays")
    parser.add_argument( "--port", nargs=1, help="(not implemented) Use specified TCP/IP port number (default=19000)")
    parser.add_argument( "--local", action="count", help="(not implemented) Do not communicate with the display file server (default)" )
    parser.add_argument( "--one", action="count", help="(not implemented) Allow only one edm instance" )
    parser.add_argument( "--open", action="count", help="(not implemented) Request edm server to open files" )
    parser.add_argument( "--eolc", action="count", help="(not implemented) Exit when last screen is closed" )
    parser.add_argument( "--ul", action="count", help="(not implemented) Takes name of user written shareable library")

# any unused arguments are considered files.
    parser.add_argument( "files", nargs=argparse.REMAINDER, help="list of .edl files that will be used to create the display")

    results = parser.parse_args(argv)

    edmApp.DebugFlag = results.debug

    for macro in results.macro:
        mt.macroDecode(macro)

    edmApp.remap = results.remap

    for files in results.files:
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
myImports = ()

def genImport(pattern):
    global myImports
    files = glob.glob(pattern)
    for fname in files:
        if not fname.endswith(".py"):
            continue
        head, tail = os.path.split(fname[0:-3])
        if tail in myImports:
            continue
        myImports = myImports + (tail,)
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

