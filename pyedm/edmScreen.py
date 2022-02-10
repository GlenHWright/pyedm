from __future__ import print_function
from __future__ import absolute_import
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from builtins import object
import pyedm.edmDisplay as edmDisplay
from .edmObject import edmObject
from pyedm.edmApp import edmApp
import os

class NextError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#
# A class that defines a single EDM window (or screen).
#
class edmScreen(object):
    # initialize a screen area. if given a filename, read it in. 
    def __init__(self, Filename=None, macroTable=None, paths=None):
        self.objectList = []
        if Filename != None:
            self.addFile(Filename, macroTable, paths)
        self.version = [None]

    def valid(self):
        return self.objectList != []

    def addFile(self, fileName, macroTable=None, paths=None):
        if edmApp.DebugFlag > 0: print("reading file", fileName)
        self.tagValue = {"Class": "Screen "+fileName}
        if paths == None:
            paths = edmApp.dataPaths

        dir = os.path.dirname(fileName)
        if len(dir)>0:
            if not dir in paths:
                paths.append(dir)

        if not fileName.endswith(".edl"):
            filename += ".edl"
        for remap in edmApp.remap:
            if fileName.startswith(remap[0]):
                fileName = fileName.replace(remap[0], remap[1], 1)
                if edmApp.DebugFlag > 0: print("filename remapped to", fileName)
                break

        edlFp = readInput(fileName, paths)
        if edlFp.valid():
            self.version = edlFp.nextline.split(" ")
            if self.version[0] == "3":
                endTag = self.read3ScreenProperties(edlFp)
                while self.read3ObjectProperties(self, edlFp, macroTable, endTag=endTag):
                    pass
            else:
                self.readScreenProperties(edlFp)
                while self.readObjectProperties(self, edlFp, macroTable):
                    pass
            if "title" not in self.tagValue:
                self.tagValue["title"] = fileName
            edlFp.close()
        else:
            print("Unable to open '%s' in" % (fileName,), paths)

    def read3ScreenProperties(self, edlFp):
        endTag = "<<<E~O~D>>>"
        altEndTag="E\002O\002D"
        emptyString = "<<<empty>>>"
        self.tagValue["major"] = self.version[0]
        self.tagValue["minor"] = self.version[1]
        self.tagValue["release"] = self.version[2]
        try:
            for tag in ["x", "y", "w", "h", "font", "fontAlign", "ctlFont", "ctlFontAlign" ]:
                self.tagValue[tag] = edlFp.getNextLine(endTag)

            for tag in [ "fgColor", "bgColor", "textColor", "ctlFgColor1", "ctlFgColor2", "ctlBgColor1", "topShadowColor", "botShadowColor", "offsetColor"]:
                # 3.1 files have 'index' before colors
                if edlFp.getNextLine(endTag) == "index":
                    edlFp.getNextLine(endTag)
                self.tagValue[tag] = edlFp.nextline

            for tag in [ "title", "gridShow", "snapToGrid",  "gridSize", "orthoLineDraw", "pvType", "id", "activateCallback", "deactivateCallback", "btnFont", "btnAlignment" ]:
                if edlFp.getNextLine(endTag) == emptyString:
                    self.tagValue[tag] = ""
                else:
                    self.tagValue[tag] = edlFp.nextline

            if edlFp.getNextLine() != endTag:
                if edlFp.nextline == altEndTag:
                    return altEndTag
                print("Not working....")
                print(self.tagValue)

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
                    self.tagValue[tagname[0]] = 1
                elif tagname[1][0] == '{':
                    self.tagValue[tagname[0]] = edlFp.readBlock()
                elif tagname[1][0] == '"':
                    self.tagValue[tagname[0]] = tagname[1][1:-1]
                else:
                    self.tagValue[tagname[0]] = tagname[1]
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
                obj.tagValue["Class"] = classname
                obj.tagValue["major"] = "0"
                obj.tagValue["minor"] = "0"
                obj.tagValue["release"] = "0"
                try:
                    obj.tagValue["x"] = edlFp.getNextLine()
                    obj.tagValue["y"] = edlFp.getNextLine()
                    obj.tagValue["w"] = edlFp.getNextLine()
                    obj.tagValue["h"] = edlFp.getNextLine()
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
            if edmApp.DebugFlag > 0:
                print("V3 classname", classname, mmr)
            obj = edmObject(parent=container)
            obj.tagValue["Class"] = classname
            obj.tagValue["major"] = mmr[0]
            obj.tagValue["minor"] = mmr[1]
            obj.tagValue["release"] = mmr[2]
            propValue = []
            while edlFp.getNextLine() != endTag:
                if edlFp.nextline == emptyString:
                        edlFp.nextline = None
                propValue.append(edlFp.nextline)
            # We need to have class information at this point, but we aren't ready to create a class instance.
            # find out if we even know about this class
            try:
                classRef = edmDisplay.edmClasses[classname]
            except:
                print("No V3 Class/Property for", classname)
            classRef.setV3PropertyList(propValue, obj.tagValue)
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
                    obj.tagValue["Class"] = tagname[1]
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
                    obj.tagValue[tagname[0]] = 1
                elif tagname[1][0] == '{':
                    obj.tagValue[tagname[0]] = edlFp.readBlock()
                elif tagname[1][0] == '"':
                    obj.tagValue[tagname[0]] = tagname[1][1:-1]
                else:
                    obj.tagValue[tagname[0]] = tagname[1]
        except NextError as ne:
            pass

        if obj != None:
            obj.show()
            return 1
        return 0

#
# A class that reads lines from an EDL file.
#
class readInput(object):
    debugFlag=0
    def __init__(self, fn=None, paths=[".",]):
        self.reuseLine=0
        self.eof = 1
        if fn != None:
            self.open(fn, paths)
        else:
            self.filename = ""
            self.nextline = ""
            self.fp = None

    def __del__(self):
        pass

    def valid(self):
        return self.fp != None

    def open(self, fn, paths):
        self.eof = 0
        if "/" in fn:
            for p in edmApp.remap:
                if fn.startswith(p[0]):
                    fn = fn.replace(p[0], p[1], 1)
                    break

        if edmApp.DebugFlag > 0:
            print("Requesting open edm file *", fn, "*")
        self.filename = fn
        if fn[0] == "/":
            try:
                self.fp = open(fn, "r")
                self.getNextLine()
                return
            except IOError:
                pass

        for path in paths:
            try:
                if edmApp.DebugFlag > 0:
                    print("open - searching path ", path, " file ", fn)
                self.fp = open(os.path.join(path,fn), "r")
                self.getNextLine()
                return
            except IOError:
                pass
        self.fp = None
        self.eof = 1
        self.nextline = ""

    def close(self):
        if self.fp != None:
            self.fp.close()
            self.fp = None

    def getNextLine(self, EOB=None):
        ''' read a single line. raise an exception on EOF or End-Of-Block. reuseLine to allow
            back up a single line
            '''
        while self.eof == 0:
            if self.reuseLine > 0:
                self.reuseLine = self.reuseLine-1
                return self.nextline
            self.nextline = self.fp.readline()
            if self.nextline == "" :
                self.eof = 1
                raise NextError("EOF")
            if EOB != None and self.nextline == EOB:
                raise NextError("End Of Block")
            if self.nextline[0] != '#':
                self.nextline = self.nextline.strip("\n")
                break

        if edmApp.DebugFlag>1 or self.debugFlag > 0:
            print('got *',self.nextline,'*')
        if self.eof == 1:
            return None
        return self.nextline

    def readBlock(self):
        lineList = []
        while self.getNextLine() != None:
            if self.nextline[0] == '}':
                return lineList
            lineList.append(self.nextline.strip("\t ") )
        return lineList
