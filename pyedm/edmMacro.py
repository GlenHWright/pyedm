from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from builtins import object
from pyedm.edmApp import edmApp
import re

class macroDictionary(object):
    idno = 0
    def __init__(self, parent=None):
        self.macroTable = {}
        self.parent = parent
        macroDictionary.idno = macroDictionary.idno+1
        self.myid = macroDictionary.idno

    def __str__(self):
        return "Macro Dictionary %d of %d" % (self.myid, macroDictionary.idno)

    def __del__(self):
        pass

    # Call to explicitly add a "name" entry, which expands to "value"
    def addMacro(self, name, value=None):
        name = name.lstrip()
        if edmApp.DebugFlag > 0: print(self, "adding macro <%s> with value <%s>" % (name, value))
        if value != None and name in value:       # possible recursion: try an early expansion
            value = self.expand(value)
        self.macroTable[name] = value

    # Call with possible comma separated list of macros, with '=' separating
    # macro names from values
    def macroDecode(self, name, value=None):
        if value != None:
            return self.addMacro(name, value)

        for oneMacro in name.split(","):
            nm = oneMacro.split("=")
            if len(nm) > 1:
                self.addMacro(nm[0], nm[1])
            else:
                self.addMacro(nm[0])

    def findValue(self, macName):
        if edmApp.DebugFlag > 0 : print(self, "looking for", macName)
        if macName in self.macroTable:
            if edmApp.DebugFlag > 0: print("  ... found", self.macroTable[macName])
            return self.macroTable[macName]
        if self.parent:
            value = self.parent.findValue(macName)
            if value != None:
                return value
        if edmApp.DebugFlag > 0: print(" ... not found")
        print("Macro", macName, "not found in table", self)
        return None

    def expand( self, input):
        '''perform a keyword substitution - no recursion'''
        success = 0
        source = re.split("(\$\([^)]*\))", input)
        result = ""
        for part in source:
            if part[0:2] == "$(" and part[-1] == ")":
                value = self.findValue(part[2:-1])
                if value != None:
                    result = result + value
                    success = 1
                    continue
            result = result + part
        if success and "$" in result:
            return self.expand(result)
        return result

    # create a new table that is a child of this table.
    def newTable(self):
        return macroDictionary(self)
