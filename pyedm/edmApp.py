# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# "global" variables.
#
from __future__ import print_function
import sip
import os
import traceback
from PyQt4.QtGui import QStyle, QStyleFactory

class edmCommonStyle(QStyle) :
    def __init__(self):
        QStyle.__init__(self)

class edmAppClass:
    def __init__(self):
        self.timer = None
        self.DebugFlag = 0
        self.screenList = []
        self.windowList = []
        self.redisplayList = []
        self.blinkList = []
        self.commonstyle = QStyleFactory.create("Plastique")

        # CLS HARD-CODED DEFAULTS
        if "EDMCOLORFILE" not in os.environ:
            os.environ['EDMCOLORFILE'] = "/home/epics/edmBase1-10f/colors.list"
        self.setPath()

    def setPath(self):
        try: dfp = os.environ["EDMDATAFILES"]
        except:
            dfp = "."
        self.dataPaths = dfp.split(";")

    def addBlink(self, widget):
        if widget not in self.blinkList:
            self.blinkList.append(widget)

    def delBlink(self, widget):
        if widget in self.blinkList:
            self.blinkList.remove(widget)

    def startTimer(self):
        if self.timer == None:
            from PyQt4.QtCore import QTimer, SIGNAL
            self.timer = QTimer()
            self.timer.connect(self.timer, SIGNAL("timeout()"), self.onTimer)
            self.timer.start(100)

    def onTimer(self):
        copyDisplay, self.redisplayList = self.redisplayList, []
        for li in copyDisplay:
            if sip.isdeleted(li):
                print ('necessary cleanup of', li.__dict__)
                try: li.cleanup()
                except: traceback.print_exc()
                continue
                
            try:
                li.redisplay()
            except RuntimeError:
                traceback.print_exc()
                print ("forcing cleanup of", li.__dict__)
                try: li.cleanup()
                except: traceback.print_exc()
            except AttributeError:
                traceback.print_exc()
                if hasattr(li, "controlPV"):
                    print ("AttributeError exception: redisplay of", li.controlPV, li.controlName, "Widget=", li)
                else:
                    print ("AttributeError exception: redisplay of widget", li)
            except:
                traceback.print_exc()

    # add a widget to a list to redisplay on a timer tick
    def redisplay(self, widget, **kw):
        if widget not in self.redisplayList:
            self.redisplayList.append(widget)
        
edmApp = edmAppClass()

# add the widget to the redisplay request queue
def redisplay(widget, **kw):
    edmApp.redisplay(widget)
