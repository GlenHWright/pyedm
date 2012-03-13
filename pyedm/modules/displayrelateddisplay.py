# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a related display

#
# there are a number of important considerations. The most important
# is the management of the macros, so that macro expansion occurs using
# the correct macro set.
#
import os
import pyedm.edmDisplay as edmDisplay
from pyedm.edmScreen import edmScreen
from pyedm.edmWidget import edmWidget
from pyedm.edmDisplay import generateWindow

from PyQt4.QtGui import QPushButton, QMenu, QPalette
from PyQt4.QtCore import SIGNAL

class popUpMenu(QMenu):
    def __init__(self, parent=None):
        QMenu.__init__(self, parent)

class relatedDisplayClass(QPushButton,edmWidget):
    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        edmWidget.__init__(self, parent)

    def buildFromObject(self, object):
        edmWidget.buildFromObject(self,object)
        self.update()
        name = self.object.getStringProperty("buttonLabel", None)
        if name != None:
            self.setText(name)
        if self.object.getIntProperty("invisible",0) == 1:
            self.transparent = 1
            self.setFlat(1)
                                            
        self.filelist = self.object.decode("displayFileName")
        self.poslist = self.object.decode("setPosition")
        self.menulist = self.object.decode("menuLabel")
        self.symbollist = self.object.decode("symbols")
        numDsps = self.object.getIntProperty("numDsps", "0")
        
        if numDsps == 0:
            print "relatedDisplayClass: no files to display"
            return

        self.filename = [ self.macroExpand(filename) for filename in self.filelist]
        self.generated = [ None for idx in range(0, len(self.filename))]
        self.widgets = [ None for idx in range(0, len(self.filename))]
        if len(self.filename) == 1:
            self.connect(self, SIGNAL("pressed()"), self.onPress)
        else:
            self.newmenu = popUpMenu(self)
            self.setMenu(self.newmenu)
            self.actions = [ self.newmenu.addAction(menu, lambda idx=idx:self.onMenu(idx)) for (menu,idx) in zip(self.menulist,range(0,len(self.filename))) ]
        self.edmParent.buttonInterest.append(self)

    @classmethod
    def setV3PropertyList(classRef, values, tags):
        for name in [ "x", "y", "w", "h", "fgColor", "bgColor", "topShadowColor", "botShadowColor"]:
           if values[0] == "index" : values.pop(0) 
           tags[name] = values.pop(0)
        filelist = []       ; tags['displayFileName'] = filelist
        labellist = []      ; tags['menulabel'] = labellist
        closeaction = []    ; tags['closeAction'] = closeaction
        setposition = []    ; tags['setPosition'] = setposition
        allowDups = []      ; tags['allowDups'] = allowDups
        cascade = []        ; tags['cascade'] = cascade
        symbollist = []     ; tags['symbols'] = symbollist
        replacelist = []    ; tags['replaceSymbols'] = replacelist
        propagatelist = []  ; tags['propagateMacros'] = propagatelist
        destPvExp = []      ; tags['pv'] = destPvExp
        sourceExp = []      ; tags['value'] = sourceExp
        filelist.append( '"%s"'% (values.pop(0), ) )
        labellist.append( '"%s"'% (values.pop(0), ) )
        tags['fontTag'] = values.pop(0)
        tags['invisible'] = values.pop(0)
        closeaction.append(values.pop(0) )
        setposition.append(values.pop(0) )
        tags['numPvs'] = values.pop(0)
        for idx in range( 0,int(tags['numPvs']) ):
            destPvExp.append('"%s"'% (values.pop(0), ) )
            sourceExp.append('"%s"'% (values.pop(0), ) )
        allowDups.append( values.pop(0) )
        cascade.append( values.pop(0) )
        symbollist.append( '"%s"'% (values.pop(0), ) )
        replacelist.append( values.pop(0) )
        propagatelist.append( values.pop(0) )
        tags['useFocus'] = values.pop(0)
        tags['numDsps'] = values.pop(0)
        numDsps = int( tags['numDsps'] )
        for idx in range(1, numDsps):
            filelist.append( '"%s"'% (values.pop(0), ) )
            labellist.append( '"%s"'% (values.pop(0), ) )
            closeaction.append(values.pop(0) )
            setposition.append(values.pop(0) )
            allowDups.append( values.pop(0) )
            cascade.append( values.pop(0) )
            symbollist.append( '"%s"'% (values.pop(0), ) )
            replacelist.append( values.pop(0) )
            propagatelist.append( values.pop(0) )
            
        tags['buttonLabel'] = values.pop(0)
        tags['noEdit'] = values.pop(0)
        if int(tags['minor'] ) > 5:
            tags['xPosOffset'] = values.pop(0)
            tags['yPosOffset'] = values.pop(0)
            if int(tags['minor']) > 6:
                tags['button3Popup'] = values.pop(0)

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText,), "FGalarm", "fgAlarm")
        self.fgColorInfo.setColor()
    
    def findBgColor(self):
        self.bgColorInfo = self.findColor("bgColor", (QPalette.Button,))
        self.bgColorInfo.setColor()

    def onPress(self):
        self.onMenu(0)

    def onMenu(self, idx):
        try:
            if self.generated[idx] == None:
                mt = self.findMacroTable()
                filename = mt.expand(self.filename[idx])
                mt = mt.newTable()
                mt.addMacro("!W", "!W%d" %(mt.myid,) )
                if self.symbollist != None: mt.macroDecode( self.symbollist[idx])
                self.generated[idx] = edmScreen( filename, mt, self.findDataPaths())
                self.generated[idx].macroTable = mt
                self.widgets[idx] = None

            if self.widgets[idx] == None:
                self.widgets[idx] = generateWindow( self.generated[idx], myparent=self, macroTable=self.generated[idx].macroTable)
                self.widgets[idx].connect( self.widgets[idx], SIGNAL("destroyed()"), lambda idx=idx:self.lostChild(idx) )
            self.widgets[idx].show()

        #except:
            #print "onMenu exception"
        finally:
            pass

    def lostChild(self, childIdx):
        print "lost child", childIdx
        self.widgets[childIdx] = None
        
edmDisplay.edmClasses["relatedDisplayClass"] = relatedDisplayClass

