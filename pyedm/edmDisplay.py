# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# generateWindow(screen) - build a QWidget for a screen entry, and fill it in
# generateWidget(screen,parent) - build child widgets of "parent".
from pyedm.edmApp import edmApp
from PyQt4.QtCore import Qt
from edmColors import findColorRule
from pyedm.edmWindowWidget import edmWindowWidget
# from __future__ import print_function

global edmClasses
edmClasses = {}

def generateWidget(screen, parent):
    global edmClasses
    if edmApp.DebugFlag : print "generateWidget", screen, parent, getattr(parent,"macroTable", None)
    for obj in screen.objectList:
        otype =  obj.tagValue["Class"]
        if edmApp.DebugFlag :  print "checking object type", otype
        if otype in edmClasses:
            widget = edmClasses[otype](parent)
            widget.buildFromObject(obj)
        else:
            if edmApp.DebugFlag : print "Unknown object type", otype, "in", edmClasses
    if edmApp.DebugFlag : print "Done generateWidget"
    
def generateWindow(screen, myparent=None, macroTable=None, dataPaths=None):
    if edmApp.DebugFlag : print "generateWindow", screen, "Parent:", myparent, "macroTable:", macroTable
    parent = edmWindowWidget()
    parent.edmParent = myparent
    parent.dataPaths = dataPaths
    if myparent != None and macroTable == None:
        parent.macroTable = getattr(myparent, "macroTable", None)
    else:
        parent.macroTable = macroTable
    # To Do: get "x y w h fgColor bgColor" here
    #
    pal = parent.palette()
    parent.fgRule = None
    parent.bgRule = None
    # Technically, these colors could be color rules or "invisible".
    # We'll ignore those possibilities for now.
    if "fgColor" in screen.tagValue:
        parent.fgRule = findColorRule(screen.tagValue["fgColor"])
        if parent.fgRule:
            pal.setColor( parent.foregroundRole(), parent.fgRule.getColor() )
    if "bgColor" in screen.tagValue:
        parent.bgRule = findColorRule(screen.tagValue["bgColor"])
        if parent.bgRule:
            pal.setColor( parent.backgroundRole(), parent.bgRule.getColor() )
    if "title" in screen.tagValue:
        parent.setWindowTitle("PyEdm - " + parent.macroExpand(screen.tagValue["title"]))
    parent.setPalette(pal)
    parent.parentx = 0
    parent.parenty = 0
    generateWidget(screen, parent)
    parent.show()
    if edmApp.DebugFlag : print "done generateWindow"
    return parent
