# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
#
# This is a low level module. It must only be called from higher level modules.
#
# Provide support for classes that need macro support or support for data path searches
# attempt to provide this as a mixin
#
from .edmApp import edmApp, debugClass

class edmWidgetSupport(debugClass):

    def macroExpand(self, str):
        '''find the appropriate macro table, and return the expanded string'''
        try: return self.findMacroTable().expand(str)
        except TypeError as e:
            print(f"type error in macro expand: {type(str)} {str}")
        except Exception as e:
            print("macro expansion failed for", self, e.message)
        return str

    def findMacroTable(self):
        '''find the appropriate macro table for this widget instance'''
        try:
            if self.macroTable != None: return self.macroTable
        except AttributeError:
            pass
        try: return self.edmParent.findMacroTable()
        except AttributeError:
            pass
        print("No valid table from", self)
        return None

    def findDataPaths(self):
        '''find the file search path for this widget instance'''
        try:
            if self.dataPaths != None: return self.dataPaths
        except: pass

        try: return self.edmParent.findDataPaths()
        except: pass

        return edmApp.dataPaths
