# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#

# Standard 'main' imports

import sys
import signal
import os
import argparse
import glob

from PyQt5 import QtWidgets

# pyedm imports
from .edmApp import edmApp
from .edmWindowWidget import generateWindow, generateWidget, edmWindowWidget
from .edmScreen import edmScreen
from .edmMacro import macroDictionary
from .edmColors import findColorRule, colorTable

def sigint_handler(*args):
    for window in edmApp.windowList:
        window.edmCleanup()
    QtWidgets.QApplication.quit()

# Mainline
# loads all the windows, and starts a QT application.
#
def pyedm_main(argv):
    """pyedm_main(argv) - start QT, and load flags"""

    signal.signal(signal.SIGINT, sigint_handler)
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
    parser.add_argument( "--new", action="count", default=0, help="creates a new window for editing")
    parser.add_argument( "--noedit", action="count",  default=0, help="Remove capability to put display in edit mode, used with  -x to produce execute only operation" )
    parser.add_argument( "-noedit", action="count",  default=0, help="Remove capability to put display in edit mode, used with  -x to produce execute only operation" )
    parser.add_argument( "--autosize", action="count", default=0, help="expand text widgets to avoid clipping characters" )
    parser.add_argument( "--scale", type=float, default=1.0, help="scale offsets and sizes" )
    parser.add_argument( "--delimiter", action="store",  default=';', help="change the delimter character used by environment variables" )
# following items are not implemented - either low priority or not applicable
    parser.add_argument( "--execute", "-x", action="count", help="(not implemented) Open all displays in execute rather than edit mode" )
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
    parser.add_argument( "-eolc", action="count", help="(not implemented) Exit when last screen is closed" )
    parser.add_argument( "--ul", action="count", help="(not implemented) Takes name of user written shareable library")

# any unused arguments are considered files.
    parser.add_argument( "files", nargs=argparse.REMAINDER, help="list of .edl files that will be used to create the display")

    results = parser.parse_args(argv)

    ''' order of operations
            1. check for debugging
            2. determine delimiter
            3. set edmApp paths
            4. read color table
            5. import modules
            6. interpret remaining flags
            7. read command line files
    '''
    edmApp.DebugFlag = results.debug
    edmApp.delimiter = results.delimiter
    edmApp.rescale = results.scale

    edmApp.setPath()
    colorTable.loadColor()
    loadModules()
    for macro in results.macro:
        mt.macroDecode(macro)

    edmApp.macroTable = mt
    edmApp.remap = results.remap
    edmApp.autosize = results.autosize

    if results.noedit:
        edmApp.allowEdit = False

    for files in results.files:
        scr = edmScreen(files, mt)
        if scr.valid():
            edmApp.screenList.append(scr)

    # All the file arguments have been read. Generate the screens.
    #

    for scr in edmApp.screenList :
        window = generateWindow(scr,macroTable=mt)
        edmApp.windowList.append(window)

    if results.new:
        edmWindowWidget.buildNewWindow()

    edmApp.startTimer()
    return 0

def loadScreen(fileName, macros="", parentWidget=None, parentDictionary=None, dataPaths=None, debugFlag=None):
    if debugFlag != None:
        edmApp.DebugFlag = debugFlag
    mt = macroDictionary(parentDictionary)
    mt.addMacro("!W", "!W%d" % ( mt.myid,) )
    mt.macroDecode(macros)
    if dataPaths != None: dataPaths = dataPaths.split(edmApp.delimiter)
    scr = edmScreen(fileName, macroTable=mt, paths=dataPaths)
    if not scr.valid():
        return
    # file loaded successfully, either build a top-level window or set this as
    # the contents.

    # track this window on the app's screen list.
    edmApp.screenList.append(scr)

    if parentWidget == None:
        # No parent widget, just display the screen
        window = generateWindow(scr, macroTable=mt,paths=dataPaths)
        edmApp.windowList.append(window)
    else:
        # a parent widget, we'll just load the screen
        parentWidget.macroTable = mt
        parentWidget.dataPaths = dataPaths
        pal = parentWidget.palette()
        try:
            parentWidget.fgRule = findColorRule(scr.tags["fgColor"].value)
            pal.setColor( parentWidget.foregroundRole(), parentWidget.fgRule.getColor() )
        except:     # intentional global ignore of exceptions.
            pass
        try:
            parentWidget.bgRule = findColorRule(scr.tags["bgColor"].value)
            pal.setColor( parentWidget.backgroundRole(), parentWidget.bgRule.getColor() )
        except:     # intentional global ignore of exceptions.
            pass
        parentWidget.setPalette(pal)
        generateWidget(scr, parentWidget)

def genImport(pattern):
    if edmApp.debug() : print(f"genImport {pattern}")
    files = glob.glob(pattern)
    for fname in files:
        if not fname.endswith(".py"):
            continue
        head, tail = os.path.split(fname[0:-3])
        edmApp.edmImport(tail, modulepath=head)

def loadModules():
    ''' load modules selectively for EDM 'extensible' operation. This allows
        adding and over-riding existing modules.
        Note that the latter can be challenging.
    '''
    for path in edmApp.searchPath:
        genImport(os.path.join(path,"edmPV*.py"))
        genImport(os.path.join(path,"display*.py"))
        genImport(os.path.join(path,"monitor*.py"))
        genImport(os.path.join(path,"control*.py"))
