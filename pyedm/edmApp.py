# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: base
#
# "global" variables.
# This is a base level file for importing, it must not directly or indirectly import any other pyedm files.
#
# For importing, this module needs to be a base-level module. However, reasonable design integration
# means that this should be able to reference higher level modules and classes!
# The approach taken to achieve this is to make some virtual-equivalent functions (should
# be abstract methods) and these get filled in by the higher-level method.
#
# Cleaner implementation:
#  edmApp should be created and initialized at the top level __init__, and other modules should not
#  reference the edmApp module directly. It might make the most sense to have allow multiple edmApp's
#  which might make remote display requests more doable.
#
import os
import traceback
from PyQt5.QtWidgets import QStyle, QStyleFactory
import PyQt5.sip as sip

cur_dir = os.path.dirname(os.path.abspath(__file__))

class edmCommonStyle(QStyle) :
    def __init__(self):
        super().__init__()

class debugClass:
    '''
        provides a common debug/trace handler for different classes.
    '''

    def debug(self, level=1, *, mesg=None, setDebug=None):
        ''' debug(level, mesg, setDebug) - debugging test for general cases. Note that edmWidgets
            have their own debug method.
        '''
        if setDebug != None:
            self.DebugFlag = setDebug

        try:
            flag = self.DebugFlag >= level
        except AttributeError:
            flag = edmApp.DebugFlag >= level
            self.DebugFlag = edmApp.DebugFlag

        if flag and (mesg != None):
            print(mesg)
        return flag


class edmAppClass(debugClass):
    '''
        edmAppClass:
        contains the "global" definitions for an application.
    '''
    ''' It may be
        desirable in the future to change the edmApp.edmApp references
        to a method edmApp() in widgets and windows to pull the specific
        app entry. This would allow independent window groups, each with
        their own color schemes and macro tables. I'm unsure of the benefit
        this has over just running multiple apps.
    '''
    def __init__(self):
        self.debug(setDebug=0)
        self.timer = None
        self.screenList = []
        self.windowList = []
        self.redisplayList = []
        self.blinkList = []
        self.cutCopyList = []
        self.allowEdit = True
        self.commonstyle = QStyleFactory.create("Plastique")
        self.edmClasses = {}
        self.delimiter = ':'   # edm compatible, may not be windows friendly
        self.macroTable = None
        self.searchPath = None

        # CLS HARD-CODED DEFAULTS
        if "EDMCOLORFILE" not in os.environ:
            os.environ['EDMCOLORFILE'] = os.path.join(cur_dir, "colors.list")
        #self.setPath()
        # myImports prevents duplication on names: if there are (e.g.) multiple edmPVepics.py files
        # in the path, the first one gets imported, and then myImports[] flags 'edmPVepics'
        # as having been imported.
        # This all seemed necessary in python 2.4. This should be re-evaluated in light of
        # import improvements in python 3
        #
        self.myImports = {}

    def setPath(self):
        try: dfp = os.environ["EDMDATAFILES"]
        except (IndexError,KeyError):
            dfp = "."
        self.dataPaths = dfp.split(edmApp.delimiter)

        # Note that ';' may be used to allow Windows "C:\path" style to be valid
        if "PYTHONEDMPATH" in os.environ:
            self.searchPath = os.environ["PYTHONEDMPATH"].split(edmApp.delimiter) + self.searchPath
        
    def addBlink(self, widget):
        if widget not in self.blinkList:
            self.blinkList.append(widget)

    def delBlink(self, widget):
        if widget in self.blinkList:
            self.blinkList.remove(widget)

    def startTimer(self):
        if self.timer == None:
            from PyQt5.QtCore import QTimer
            self.timer = QTimer()
            self.timer.timeout.connect(self.onTimer)
            self.timer.start(100)

    def onTimer(self):
        '''
        onTimer - run items that need to be in the main thread.
        1) check for deleted C++ widget entries, and clean up
            the epics portion.
        Note that the global 'except's are intentional, as
        failures in the timer routine can otherwise cause things
        to break in unhealthy ways.
        '''
        copyDisplay, self.redisplayList = self.redisplayList, []
        for li in copyDisplay:
            if sip.isdeleted(li):
                print('necessary cleanup of', li)
                try:
                    li.edmCleanup()
                except RuntimeError:
                    pass    # most likely due to 'isdeleted()'
                except BaseException as exc:
                    print(f"Cleanup failure for {li} in onTimer")
                    traceback.print_exc()
                continue
            try:
                li.redisplay()
            except RuntimeError:
                traceback.print_exc()
                print("RuntimeError exception: forcing cleanup of", li)
                try: li.edmCleanup()
                except RuntimeError:
                    pass
                except: traceback.print_exc()
            except AttributeError:
                traceback.print_exc()
                print("AttributeError exception: redisplay of widget", li)
            except:
                print(f"redisplay failure for {li}")
                traceback.print_exc()

    # add a widget to a list to redisplay on a timer tick
    def redisplay(self, widget, **kw):
        if widget not in self.redisplayList:
            self.redisplayList.append(widget)

    @staticmethod
    def edmScreen(*args,**kw):
        ''' edmScreen - return a class instance of edmScreen
        '''
        raise AttributeError("edmScreen must be redefined before use!")

    @staticmethod
    def generateWidget(*args,**kw):
        raise AttributeError("generateWidget must be redefined before use!")

    @staticmethod
    def generateWindow(*args,**kw):
        raise AttributeError("generateWindow must be redefined before use!")

    @staticmethod
    def buildNewWindow(*args,**kw):
        raise AttributeError("buildNewWindow must be redefined before use!")

    @staticmethod
    def showBackgroundMenu(*args,**kw):
        raise AttributeError("showBackgroundMenu must be redefined before use!")

    @staticmethod
    def edmImport(*args, **kw):
        raise AttributeError("edmImport must be redefined before use!")
        
    class edmWidget:
        def __init__(self, *args, **kw):
            raise AttributeError("edmWidget must be redefined before use!")


## ugly - creates a global edmApp instance.
edmApp = edmAppClass()
    
# add the widget to the redisplay request queue
def redisplay(widget, **kw):
    edmApp.redisplay(widget)
