# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# If opened as 'main', use our mainline
#
# MODULE LEVEL: top
#
import sys
import os

# pyedm imports
from .edmApp import edmApp

# searchPath states where to look for a module.
# default path must be set before calling 'setPath()'
edmApp.searchPath = [".", __path__[0], os.path.join(__path__[0],"modules") ]

from .edmWindowWidget import generateWindow, generateWidget, edmWindowWidget
from .edmScreen import edmScreen
from .edmMacro import macroDictionary
from .edmColors import findColorRule, colorTable
from .edmMain import pyedm_main, loadModules

''' There is an unfortunate need for __path__, which only exists
in __init__.py. Otherwise, this could all be part of edmApp
'''
def edmImport( modulename, modulepath=None):
    '''
        attempt to load a module that may or may not be part of the pyedm
        package.
        Exceptions are not caught here.
        - if called with explicit modulepath, does an import on that path.
        - otherwise, recursively calls with enties from searchPath
    '''
    if modulename in edmApp.myImports:
        return edmApp.myImports[modulename]
    if edmApp.debug() : print(f"searching {modulename} in {modulepath}")
    # if module path set, try an import
    if modulepath != None:
        if modulepath not in __path__:
            __path__.insert(0,modulepath)
            module = __import__(modulename, globals=globals(), locals=locals(), level=1)
            __path__.pop(0)
        else:
            module = __import__(modulename, globals=globals(), locals=locals(), level=1)
        edmApp.myImports[modulename] = module
        return module

    # module path not set; recurse with explicit path entries
    for path in edmApp.searchPath:
        try:
            module = edmImport(modulename, modulepath=path)
            return module
        except ImportError as exc:
            # this can be a problem if the module is found, but has an import error!
            # TODO - interpret exc
            print("importError", exc)
            pass
    # unable to find the module
    raise ImportError(f"unable to import module {modulename}")

edmApp.edmImport = edmImport
