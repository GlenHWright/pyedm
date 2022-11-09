# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: base
#
# "global" variables.
# This is a base level file for importing, it must not directly or indirectly import any other pyedm files.
#
import os
import traceback
from PyQt5.QtWidgets import QStyle, QStyleFactory
import PyQt5.sip as sip

cur_dir = os.path.dirname(os.path.abspath(__file__))

class edmCommonStyle(QStyle) :
    def __init__(self):
        super().__init__()

class edmAppClass:
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
        self.timer = None
        self.DebugFlag = 0
        self.screenList = []
        self.windowList = []
        self.redisplayList = []
        self.blinkList = []
        self.allowEdit = True
        self.commonstyle = QStyleFactory.create("Plastique")
        self.edmClasses = {}
        self.macroTable = None

        # CLS HARD-CODED DEFAULTS
        if "EDMCOLORFILE" not in os.environ:
            os.environ['EDMCOLORFILE'] = os.path.join(cur_dir, "colors.list")
        self.setPath()

    def setPath(self):
        try: dfp = os.environ["EDMDATAFILES"]
        except:
            dfp = "."
        if ';' in dfp: # workaround for Windows drive paths
            self.dataPaths = dfp.split(";")
        else:
            self.dataPaths = dfp.split(':')

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
                except: traceback.print_exc()
            except AttributeError:
                traceback.print_exc()
                print("AttributeError exception: redisplay of widget", li)
            except:
                print(f"redisplay failure for {li}")
                traceback.print_exc()

    def debug(self, level=1, *, mesg=None, setDebug=None):
        if setDebug != None:
            self.DebugFlag = setDebug
        flag = self.DebugFlag >= level
        if flag and (mesg != None):
            print(mesg)
        return flag

    # add a widget to a list to redisplay on a timer tick
    def redisplay(self, widget, **kw):
        if widget not in self.redisplayList:
            self.redisplayList.append(widget)
        
edmApp = edmAppClass()

# add the widget to the redisplay request queue
def redisplay(widget, **kw):
    edmApp.redisplay(widget)
