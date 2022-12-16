# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Module for generating a widget for a related display

#
# there are a number of important considerations. The most important
# is the management of the macros, so that macro expansion occurs using
# the correct macro set.
#
import os

from PyQt5.QtWidgets import QPushButton, QMenu
from PyQt5.QtGui import QPalette

from .edmApp import edmApp
from .edmScreen import edmScreen
from .edmWidget import edmWidget
from .edmField import edmField
from .edmEditWidget import edmEdit
from .edmWindowWidget import generateWindow

class popUpMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

class relatedDisplayClass(QPushButton,edmWidget):
    menuGroup = ["display", "Related Display"]
    edmEntityFields = [
            edmField("buttonLabel", edmEdit.String),
            edmField("invisible", edmEdit.Bool),
            edmField("numDsps", edmEdit.Int, hidden=True),
            edmField("displayFileName", edmEdit.String, array=True),
            edmField("setPosition", edmEdit.Bool, array=True),
            edmField("menuLabel", edmEdit.String, array=True),
            edmField("symbols", edmEdit.String, array=True)
            ] + edmWidget.edmFontFields

    def __init__(self, parent=None):
        super().__init__(parent)

    def buildFromObject(self, objectDesc, **kw):
        super().buildFromObject(objectDesc, **kw)
        name = self.objectDesc.getProperty("buttonLabel", None)
        if name != None:
            self.setText(self.macroExpand(name))
        if self.objectDesc.getProperty("invisible",0) == 1:
            self.transparent = 1
            self.setFlat(1)
                                            
        numDsps = self.objectDesc.getProperty("numDsps", "0")
        
        if numDsps == 0:
            print("relatedDisplayClass: no files to display")
            return
        self.filelist = self.objectDesc.getProperty("displayFileName",arrayCount=numDsps)
        self.poslist = self.objectDesc.getProperty("setPosition",arrayCount=numDsps)
        self.menulist = self.objectDesc.getProperty("menuLabel",arrayCount=numDsps)
        self.symbollist = self.objectDesc.getProperty("symbols",arrayCount=numDsps)

        self.filename = [ self.macroExpand(filename) for filename in self.filelist]
        self.generated = [ None for idx in range(0, len(self.filename))]
        self.widgets = [ None for idx in range(0, len(self.filename))]
        if len(self.filename) == 1:
            self.pressed.connect(self.onPress)
        else:
            self.newmenu = popUpMenu(self)
            self.setMenu(self.newmenu)
            self.actions = [ self.newmenu.addAction(menu, lambda idx=idx:self.onMenu(idx)) for (menu,idx) in zip(self.menulist,list(range(0,len(self.filename)))) ]
        self.edmParent.buttonInterest.append(self)

    def edmCleanup(self):
        if self.debug() : print(f"cleanup related {self.generated} {self.widgets}")
        try:
            self.edmParent.buttonInterest.remove(self)
        except ValueError:
            pass
        self.generated = None
        self.widgets = None
        self.actions = None
        self.pressed.disconnect()
        super().edmCleanup()

    @classmethod
    def setV3PropertyList(classRef, values, obj):
        for name in [ "x", "y", "w", "h", "fgColor", "bgColor", "topShadowColor", "botShadowColor"]:
           if values[0] == "index" : values.pop(0) 
           obj.addTag(name, values.pop(0))
        filelist = []     
        labellist = []   
        closeaction = []
        setposition = []  
        allowDups = []   
        cascade = []    
        symbollist = []
        replacelist = []   
        propagatelist = []
        destPvExp = []   
        sourceExp = []  
        filelist.append( f'"{values.pop(0)}"')
        labellist.append(f'"{values.pop(0)}"')
        obj.addTag('fontTag', values.pop(0))
        obj.addTag('invisible', values.pop(0))
        closeaction.append(values.pop(0) )
        setposition.append(values.pop(0) )
        obj.addTag('numPvs', values.pop(0))
        for idx in range( 0,int(obj.tags['numPvs'].value) ):
            destPvExp.append(f'"{values.pop(0)}"')
            sourceExp.append(f'"{values.pop(0)}"')
        allowDups.append( values.pop(0) )
        cascade.append( values.pop(0) )
        symbollist.append( f'"{values.pop(0)}"')
        replacelist.append( values.pop(0) )
        propagatelist.append( values.pop(0) )
        obj.addTag('useFocus', values.pop(0))
        obj.addTag('numDsps', values.pop(0))
        numDsps = int( obj.tags['numDsps'].value )
        for idx in range(1, numDsps):
            filelist.append( f'"{values.pop(0)}"')
            labellist.append( f'"{values.pop(0)}"')
            closeaction.append(values.pop(0) )
            setposition.append(values.pop(0) )
            allowDups.append( values.pop(0) )
            cascade.append( values.pop(0) )
            symbollist.append( f'"{values.pop(0)}"')
            replacelist.append( values.pop(0) )
            propagatelist.append( values.pop(0) )
            
        obj.addTag('buttonLabel',values.pop(0))
        obj.addTag('noEdit',  values.pop(0))
        obj.addTag('displayFileName',  filelist)
        obj.addTag('menulabel',  labellist)
        obj.addTag('closeAction',  closeaction)
        obj.addTag('setPosition',  setposition)
        obj.addTag('allowDups',  allowDups)
        obj.addTag('cascade',  cascade)
        obj.addTag('symbols',  symbollist)
        obj.addTag('replaceSymbols',  replacelist)
        obj.addTag('propagateMacros',  propagatelist)
        obj.addTag('pv',  destPvExp)
        obj.addTag('value',  sourceExp)
        if int(obj.tags['minor'].value ) > 5:
            obj.addTag('xPosOffset', values.pop(0))
            obj.addTag('yPosOffset', values.pop(0))
            if int(obj.tags['minor'].value) > 6:
                obj.addTag('button3Popup', values.pop(0))

    def findFgColor(self):
        self.fgColorInfo = self.findColor("fgColor", (QPalette.ButtonText,), alarmPV="FGalarm", alarmName="fgAlarm")
        self.fgColorInfo.setColor()
    
    def findBgColor(self):
        self.bgColorInfo = self.findColor("bgColor", (QPalette.Button,))
        self.bgColorInfo.setColor()

    def onPress(self):
        self.onMenu(0)

    def onMenu(self, idx):
        if self.debug(1) : print(f"onMenu({idx}) {self.generated} {self.widgets}")
        try:
            if self.generated[idx] == None:
                mt = self.findMacroTable()
                mt = mt.newTable()
                mt.addMacro("!W", "!W%d" %(mt.myid,) )
                if self.symbollist != None: mt.macroDecode( self.symbollist[idx])
                self.generated[idx] = edmScreen( self.filename[idx],mt,self.findDataPaths())
                self.generated[idx].macroTable = mt
                self.widgets[idx] = None

        except BaseException as exc:
            print(f"related display: onMenu({idx}) macro/edmScreen failed: {exc}")
            return

        if self.widgets[idx] == None:
            self.widgets[idx] = generateWindow( self.generated[idx], myparent=self, macroTable=self.generated[idx].macroTable)
            self.widgets[idx].destroyed.connect(lambda *args, idx=idx: self.lostChild(*args, childIdx=idx))
        self.widgets[idx].show()

    def edmCleanupChild(self, child):
        try:
            idx = self.widgets.index(child)
            self.widgets[idx] = None
            self.generated[idx] = None
        except AttributeError:
            pass    # self.widgets already cleaned up
        except BaseException as exc:
            print(f"edmCleanupChild self:{self} child:{child} failed: {exc}")

    def lostChild(self, *args, childIdx=None):
        if self.debug() : print(f"lostChild {args} {childIdx}  {self.widgets}")
        if self.widgets != None and childIdx != None:
            self.widgets[childIdx] = None
        
edmApp.edmClasses["relatedDisplayClass"] = relatedDisplayClass

