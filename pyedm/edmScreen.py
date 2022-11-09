# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Manages saving and loading screen files.
# it does not create windows or widgets.
#
# MODULE LEVEL: mid
#
# This is a mid-level module. It must only call low level or base level modules
#

import traceback
import json
import os
from enum import Enum

from PyQt5.QtGui import QFont, QFontInfo

from .edmObject import edmObject
from . import edmProperty
from . import edmFont
from .edmEditWidget import edmEdit, edmTag, fontAlignEnum
from .edmColors import colorRule
from .edmApp import edmApp
from .edmField import edmTag, edmField

class NextError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#
# A class that holds the definition a single EDM window (or screen).
# edmScreen is responsible to load a description from a source
# (most likely a .edl file, but can be changed).
# This is where the objectDesc is created.
# This description is then used by other classes to create the
# display window.
#
class edmScreen(edmObject):
    usePixmapEnum = Enum("usePixmap", ["By env var", "Never", "Always" ] , start=0)
    edmFieldList = [
            edmField("major", edmEdit.Int, 4),
            edmField("minor", edmEdit.Int, 0),
            edmField("release", edmEdit.Int, 1),
            edmField("x", edmEdit.Int, 100),
            edmField("y", edmEdit.Int, 100),
            edmField("w", edmEdit.Int, 100),
            edmField("h", edmEdit.Int, 100),
            edmField("title", edmEdit.String, None),
            edmField("defPVtype", edmEdit.String, None),
            edmField("fgColor", edmEdit.Color, 14),
            edmField("bgColor", edmEdit.Color, 6),
            edmField("showGrid", edmEdit.Bool, False),
            edmField("snapToGrid", edmEdit.Bool, False),
            edmField("gridSpacing", edmEdit.Int, 10),
            edmField("orthoLineMove", edmEdit.Bool, False),
            edmField("orthoLineDraw", edmEdit.Bool, False),
            edmField("disableScrolling", edmEdit.Bool, False),
            edmField("usePixmap", edmEdit.Enum, defaultValue=0, enumList=usePixmapEnum),
            edmField("textFg", edmEdit.Color, defaultValue=14),
            edmField("control1Fg", edmEdit.Color, defaultValue=14),
            edmField("control2Fg", edmEdit.Color, defaultValue=14),
            edmField("control1Bg", edmEdit.Color, defaultValue=0),
            edmField("control2Bg", edmEdit.Color, defaultValue=0),
            edmField("topShadow", edmEdit.Color, defaultValue=0),
            edmField("bottomShadow", edmEdit.Color, defaultValue=14),
            edmField("textFont", edmEdit.FontInfo, defaultValue="helvetica-medium-r-18"),
            edmField("textAlign", edmEdit.Enum, enumList=fontAlignEnum, defaultValue="left"),
            edmField("controlFont", edmEdit.FontInfo, defaultValue="helvetica-medium-r-18"),
            edmField("controlAlign", edmEdit.Enum, enumList=fontAlignEnum, defaultValue="left"),
            edmField("buttonFont", edmEdit.FontInfo, defaultValue="helvetica-medium-r-18"),
            edmField("buttonAlign", edmEdit.Enum, enumList=fontAlignEnum, defaultValue="left"),
            edmField("Filename", edmEdit.String, defaultValue=None),
            ]


    ''' edmScreen - read a file, and create an object list.
    '''
    def __init__(self, Filename=None, macroTable=None, paths=None):
        super().__init__()
        self.edmFields = self.edmFieldList
        self.objectList = []    # updated by 'edmObject' when this instance is the parent
        if Filename != None:
            self.addFile(Filename, macroTable, paths)
        self.version = [None]

    def valid(self):
        return self.objectList != []

    def addFile(self, fileName, macroTable=None, paths=None):
        if edmApp.debug(): print("reading file", fileName)
        if paths == None:
            paths = edmApp.dataPaths

        dir = os.path.dirname(fileName)
        if len(dir)>0:
            if not dir in paths:
                paths.append(dir)

        # if no suffix, look for an edl file. This is non-standard edm.
        if not ( fileName.endswith(".edl") or fileName.endswith(".jedl")):
            fileName += ".edl"

        if fileName.endswith(".jedl") or fileName.endswith(".edljson"):
            self.readJSONfile(fileName, macroTable, paths)
        else:
            self.addTag( "Class",  "Screen" )
            self.addTag( "Filename" ,  fileName )

            try:
                with readInput(fileName, paths) as edlFp:
                    self.version = edlFp.getNextLine().split(" ")
                    if self.version[0] == "3":
                        endTag = self.read3ScreenProperties(edlFp)
                        while self.read3ObjectProperties(self, edlFp, macroTable, endTag=endTag):
                            pass
                    else:
                        self.readScreenProperties(edlFp)
                        while self.readObjectProperties(self, edlFp, macroTable):
                            pass
            except FileNotFoundError as exc:
                print(f"{exc}")
                return

        for f in self.edmFieldList:
            try:
                self.tags[f.tag].field = f
            except KeyError:
                pass    # tags do not have to be complete

    def readJSONfile(self,fn, macroTable, paths):
        try:
            with readInput(fn, paths) as edlFp:
                jsonDesc = json.load(edlFp.fp)
                self.buildJSONobject(jsonDesc, self)
            self.addTag("Filename", fn)   # over-ride input name.
        except FileNotFoundError as exc:
            print(f"{exc}")
            return

    @staticmethod
    def buildJSONobject(jsonDesc, target):
        for key, value in jsonDesc.items():
            if isinstance(value, dict): # currently, this indicates a font.
                target.addTag(key, edmFont.getFont(value))
            elif isinstance(value, list):   # either an array list or a group widget list
                if key == "edmWidgets":
                    target.objectList = []
                    target.addTag("parentx", "0")
                    target.addTag("parenty", "0")
                    for desc in value:
                        obj = edmObject(parent=target)
                        edmScreen.buildJSONobject(desc, obj)
                else:
                    target.addTag(key, value) # adds an explicit array.
            else:
                target.addTag(key, value)

    # note: edmObject also has an addTag field - make sure this is the reference you want!
    def addTag(self, field, value):
        self.tags[field] = edmTag(field, value)

    def saveToFile(self, filename=None):
        ''' saveToFile
            create a JSON file. if filename unspecified, use the tag['Filename'].value
        '''
        if filename == None:
            filename = self.tags["Filename"].value

        if filename.endswith(".edl"):
            filename = filename.removesuffix(".edl") +  ".jedl"
        elif not filename.endswith(".jedl"):
            filename = filename + ".jedl"

        with open(filename, "w") as fp:
            json.dump(self, fp, cls=edmEncoder)

    def read3ScreenProperties(self, edlFp):
        endTag = "<<<E~O~D>>>"
        altEndTag="E\002O\002D"
        emptyString = "<<<empty>>>"
        self.addTag("major", self.version[0])
        self.addTag("minor", self.version[1])
        self.addTag("release", self.version[2])
        try:
            for tag in ["x", "y", "w", "h", "font", "fontAlign", "ctlFont", "ctlFontAlign" ]:
                self.addTag(tag, edlFp.getNextLine(endTag))

            for tag in [ "fgColor", "bgColor", "textColor", "ctlFgColor1", "ctlFgColor2", "ctlBgColor1", "topShadowColor", "botShadowColor", "offsetColor"]:
                # 3.1 files have 'index' before colors
                if edlFp.getNextLine(endTag) == "index":
                    edlFp.getNextLine(endTag)
                self.addTag(tag, edlFp.nextline)

            for tag in [ "title", "gridShow", "snapToGrid",  "gridSize", "orthoLineDraw", "pvType", "id", "activateCallback", "deactivateCallback", "btnFont", "btnAlignment" ]:
                if edlFp.getNextLine(endTag) == emptyString:
                    self.addTag(tag, "")
                else:
                    self.addTag(tag, edlFp.nextline)

            if edlFp.getNextLine() != endTag:
                if edlFp.nextline == altEndTag:
                    return altEndTag
                print("Not working....")
                print(edlFp.nextline)

        except NextError as ne:
            if ne.value == "EOF":
                print("Unexpected EOF in version 3 file")
            if ne.value == "End Of Block":
                print("unexected end of properties block in version 3 file")
        return endTag

    def readScreenProperties(self, edlFp):
        '''read edl version 4 screen properties'''
        try:
            while edlFp.getNextLine() != None:
                if edlFp.nextline == "endScreenProperties":
                    return 1
                tagname = edlFp.nextline.split(" ", 1)
                if len(tagname) == 1:
                    self.addTag(tagname[0], 1)
                elif tagname[1][0] == '{':
                    self.addTag(tagname[0], edlFp.readBlock() )
                elif tagname[1][0] == '"':
                    self.addTag(tagname[0], tagname[1][1:-1] )
                else:
                    self.addTag(tagname[0], tagname[1] )
            return 0
        except NextError as ne:
            print("EOF reading screen properties!")

    def read3ObjectProperties(self, container, edlFp, macroTable, endTag = "<<<E~O~D>>>"):
        ''' read version 3 edl class properties'''
        obj = None
        emptyString = "<<<empty>>>"
        try:
            # First line is class name, 2nd is version info
            classname = edlFp.getNextLine()

            if classname == "}":    # end of a group
                return 0
            # Groups have to be just a little bit different...
            if classname == "activeGroupClass":
                obj = edmObject(parent=container)
                obj.addTag("Class", classname)
                obj.addTag("major", "0" )
                obj.addTag("minor", "0" )
                obj.addTag("release", "0" )
                try:
                    obj.addTag("x", edlFp.getNextLine() )
                    obj.addTag("y", edlFp.getNextLine() )
                    obj.addTag("w", edlFp.getNextLine() )
                    obj.addTag("h", edlFp.getNextLine() )
                    if edlFp.getNextLine() != "{":
                        print("group syntax - expected {")
                        return 0
                except:
                    print("Unable to read group header info")
                    return 0
                obj.objectList = []
                obj.show()
                while self.read3ObjectProperties( obj, edlFp, macroTable, endTag="E\002O\002D") == 1:
                    pass

                if edlFp.getNextLine() != endTag:
                    print('group syntax - expected end tag')
                    return 0
                return 1
            #

            mmr = edlFp.getNextLine().split(" ")
            if edmApp.debug():
                print("V3 classname", classname, mmr)
            obj = edmObject(parent=container)
            obj.addTag("Class", classname )
            obj.addTag("major", mmr[0] )
            obj.addTag("minor", mmr[1] )
            obj.addTag("release", mmr[2] )
            propValue = []
            while edlFp.getNextLine() != endTag:
                if edlFp.nextline == emptyString:
                        edlFp.nextline = None
                propValue.append(edlFp.nextline)
            # We need to have class information at this point, but we aren't ready to create a class instance.
            # find out if we even know about this class
            try:
                classRef = edmApp.edmClasses[classname]
                classRef.setV3PropertyList(propValue, obj.tags)
            except:
                print("No V3 Class/Property for", classname)
            return 1

        except NextError as ne:
            if ne.value == "EOF":
                if obj != None:
                    print("Unexpected EOF reading version 3 object")
            elif ne.value == "End Of Block":
                print("Unexpected end-of-block reading version 3 object")
        return 0

    def readObjectProperties(self, container, edlFp, macroTable):
        ''' read version 4 edl class properties'''
        inObject = 0
        obj = None
        try:
            while edlFp.getNextLine() != None:
                if edlFp.nextline == "endObjectProperties":
                    inObject = 0
                    continue
                if edlFp.nextline == "endGroup":
                    return 1
                if edlFp.nextline[0:7] == "object ":
                    if obj != None:
                        edlFp.reuseLine = 1
                        obj.show()
                        return 1
                    obj = edmObject(parent=container)
                    tagname = edlFp.nextline.split(" ", 1)
                    obj.addTag("Class", tagname[1])
                    continue
                if edlFp.nextline == "beginObjectProperties":
                    inObject = 1
                    continue
                if edlFp.nextline == "endGroup":
                    return 1
                if inObject == 0:
                    continue
                if edlFp.nextline == "beginGroup":
                    obj.objectList = []
                    obj.show()
                    while self.readObjectProperties( obj, edlFp, macroTable) == 1:
                        if edlFp.nextline == "endGroup":
                            break
                    continue
                tag = edlFp.nextline
                tagname = tag.split(" ", 1)
                if len(tagname) == 1:
                    obj.addTag(tagname[0], 1)
                elif tagname[1][0] == '{':
                    obj.addTag(tagname[0], edlFp.readBlock())
                elif tagname[1][0] == '"':
                    obj.addTag(tagname[0], tagname[1][1:-1])
                else:
                    obj.addTag(tagname[0], tagname[1])
        except NextError as ne:
            pass

        if obj != None:
            obj.show()
            return 1
        return 0

#
# A class that reads lines from an EDL file.
#
class readInput:
    def __init__(self, fn, paths=[".",]):
        self.reuseLine=0
        self.eof = 1
        if fn != None:
            self.open(fn, paths)
        else:
            self.filename = ""
            self.nextline = ""
            self.fp = None

    def __enter__(self):
        return self

    def __exit__(self,*args,**kw):
        print(f"readInput._exit__({self}:{args},{kw})")
        self.close()

    def valid(self):
        return self.fp != None

    def open(self, fn, paths):
        self.eof = 0
        if "/" in fn:
            for p in edmApp.remap:
                if fn.startswith(p[0]):
                    fn = fn.replace(p[0], p[1], 1)
                    break

        if edmApp.debug():
            print("Requesting open edm file *", fn, "*")
        self.filename = fn
        if fn[0] == "/":
            try:
                self.fp = open(fn, "r")
                self.getNextLine()
                return
            except FileNotFoundError:
                pass

        for path in paths:
            try:
                if edmApp.debug():
                    print("open - searching path ", path, " file ", fn)
                filetotry = os.path.join(path,fn)
                for p in edmApp.remap:
                    if filetotry.startswith(p[0]):
                        filetotry = filetotry.replace(p[0], p[1], 1)
                        break
                self.fp = open(filetotry, "r")
                return
            except FileNotFoundError:
                pass
        self.fp = None
        self.eof = True
        self.nextline = ""
        raise FileNotFoundError(f"unable to open {fn} in paths {paths}")

    def close(self):
        if self.fp != None:
            self.fp.close()
            self.fp = None

    def getNextLine(self, EOB=None):
        ''' read a single line. raise an exception on EOF or End-Of-Block. reuseLine to allow
            back up a single line
            '''
        while self.eof == False:
            if self.reuseLine > 0:
                self.reuseLine = self.reuseLine-1
                return self.nextline
            self.nextline = self.fp.readline()
            if self.nextline == "" :
                self.eof = True
                raise NextError("EOF")
            if EOB != None and self.nextline == EOB:
                raise NextError("End Of Block")
            if self.nextline[0] != '#':
                self.nextline = self.nextline.strip("\n")
                break

        if edmApp.debug(2):
            print('got *',self.nextline,'*')
        if self.eof == True:
            return None
        return self.nextline

    def readBlock(self):
        lineList = []
        while self.getNextLine() != None:
            if self.nextline[0] == '}':
                return lineList
            lineList.append(self.nextline.strip("\t ") )
        return lineList

class edmEncoder(json.JSONEncoder):
    '''
        edmEncoder -
        rebuild the edm tags in a JSON-friendly way
    '''
    def default(self, obj):
        if isinstance(obj, edmScreen):
            return { **obj.tags , "edmWidgets" : obj.objectList }
        if isinstance(obj, edmObject):
            if hasattr(obj, 'objectList'):
                return {**obj.tags , "edmWidgets" : obj.objectList }
            return obj.tags
        if isinstance(obj, edmTag):
            if getattr(obj.field, 'array', 0):
                return edmProperty.decode(obj, obj.field)
            return edmProperty.converter(obj, obj.field, None)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, QFont):
            fi = QFontInfo(obj)
            return { "family" : fi.family(), "pointSize" : fi.pointSize(), "bold" : fi.bold(), "italic" : fi.italic() }
        if isinstance(obj, colorRule):
            return f'index {obj.numeric}'
            
        return json.JSONEncoder.default(self, obj)
