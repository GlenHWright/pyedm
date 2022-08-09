#from __future__ import print_function
#from __future__ import absolute_import
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from .edmApp import edmApp

class edmWidgetSupport:
    def __init__(self): # this seems unnecessary...
         super().__init__()
    '''methods shared by edmWidget and edmWindowWidget'''
    def macroExpand(self, str):
        '''find the appropriate macro table, and return the expanded string'''
        try: return self.findMacroTable().expand(str)
        except:
            print("macro expansion failed for", self)
        return str

    def findMacroTable(self):
        '''find the appropriate macro table for this widget instance'''
        try:
            if self.macroTable != None: return self.macroTable
        except:
            pass
        try: return self.edmParent.findMacroTable()
        except:
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
