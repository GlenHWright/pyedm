# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
#
# This is a low-level module, and must only import base level pyedm modules
#
# provide general macro text substitution support.

from pyedm.edmApp import edmApp
import re

class macroDictionary:
    idno = 0
    def __init__(self, parent=None):
        self.macroTable = {}
        self.parent = parent
        macroDictionary.idno = macroDictionary.idno+1
        self.myid = macroDictionary.idno

    def __str__(self):
        return "Macro Dictionary %d of %d" % (self.myid, macroDictionary.idno)

    def edmCleanup(self):
        pass

    # Call to explicitly add a "name" entry, which expands to "value"
    # Note that the test of 'name in value' means that its possible this
    # is a recursive definition. This can happen when building a macro table
    # for a call to a related screen, and passing the macro can be done
    # explicitly with MYMACRO=$(MYMACRO). By calling self.expand(), we
    # set the current value of MYMACRO.
    def addMacro(self, name, value=None):
        name = name.lstrip()
        if edmApp.debug(): print(self, "adding macro <%s> with value <%s>" % (name, value))
        if value != None and name in value:       # possible recursion: try an early expansion
            value = self.expand(value)
        self.macroTable[name] = value

    # Call with possible comma separated list of macros, with '=' separating
    # macro names from values
    def macroDecode(self, name, value=None):
        if name == None:
            return
        if value != None:
            self.addMacro(name, value)
            return

        for oneMacro in name.split(","):
            nm = oneMacro.split("=")
            if len(nm) > 1:
                self.addMacro(nm[0], nm[1])
            else:
                self.addMacro(nm[0])

    def findValue(self, macName):
        if edmApp.debug() : print(self, "looking for", macName)
        if macName in self.macroTable:
            if edmApp.debug(): print("  ... found", self.macroTable[macName])
            return self.macroTable[macName]
        if self.parent:
            value = self.parent.findValue(macName)
            if value != None:
                return value
        if edmApp.debug(): print(" ... not found")
        # informative warning, not an error
        print("Macro", macName, "not found in table", self)
        return None

    def expand( self, input, depth=0):
        '''expand(input, depth=0) : perform a keyword substitution -
            looks for $(NAME) in input, and replaces it with
            the value from this macro table or, failing that,
            the value from the closest parent.
            if NAME is not found, the string remains unchanged.
            Macro loops should be prevented by use of 'depth'.
        '''
        success = False
        source = re.split("(\$\([^)]*\))", input)
        result = ""
        for part in source:
            if part[0:2] == "$(" and part[-1] == ")":
                value = self.findValue(part[2:-1])
                if value != None:
                    result = result + value
                    success = True
                    continue
            result = result + part
        if success and depth < 10 and "$" in result and input != result:
            return self.expand(result, depth+1)
        return result

    # create a new table that is a child of this table.
    def newTable(self):
        return macroDictionary(self)
