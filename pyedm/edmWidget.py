from __future__ import print_function
from __future__ import absolute_import
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Generic widget support
#
from builtins import zip
from builtins import str
from builtins import object
import traceback
from PyQt5.QtCore import Qt#, SIGNAL
from PyQt5.QtGui import QPalette, QFontDatabase
from pyedm.edmPVfactory import buildPV, expandPVname
from pyedm.edmApp import edmApp, redisplay
import pyedm.edmFont as edmFont
import pyedm.edmColors as edmColors

from .edmWidgetSupport import edmWidgetSupport

from .edmEditWidget import edmEditInt

# Configuration and status information for a color for a widget.
# relates the Color Rule, the Color Value, the Alarm Status, and the
# Palette Set. When a change occurs to color value or alarm status,
# the widget "redisplay()" must be able to redraw
#
class reColorInfo(object):
    def __init__(self, widget, cr=None):
        self.widget = widget
        self.alarmSensitive = 0
        self.colorRule = cr
        self.alarmStatus = 0
        self.colorValue = 0.0
        self.colorPalette = ()
        self.lastColor = None

    def cleanup(self):
        try:
            self.alarmpv.del_callback(self)
            self.alarmpv = None
        except: pass
        try:
            self.colorpv.del_callback(self)
            self.colorpv = None
        except: pass
        self.widget = None      # break circular reference

    # called for an alarm sensitive color
    def addAlarmStatus(self, alarmPV, widget):
        if self.widget.DebugFlag > 0 : print("addAlarmStatus", alarmPV)
        self.alarmSensitive = 1
        self.alarmpv = alarmPV
        alarmPV.add_callback( self.onAlarmUpdate, self)

    def addColorPV(self, colorPV):
        if self.widget.DebugFlag > 0 :print("addColorPV", self, colorPV)
        self.colorpv = colorPV
        colorPV.add_callback( self.onColorUpdate, self)

    def onAlarmUpdate(self, widget, **kw):
        if self.widget.DebugFlag > 0 :print('onAlarmUpdate', self, kw)
        if self.alarmSensitive == 0 or "severity" not in kw:
            print("Useless onAlarmUpdate call!", self.alarmSensitive)
            return
        self.alarmStatus = kw["severity"]
        redisplay(self.widget)
    
    def onColorUpdate(self, widget, **kw):
        if self.widget.DebugFlag > 0 :print("onColorUpdate", self, kw)
        if "value" in kw:
            self.colorValue = kw["value"]
            redisplay(self.widget)

    # The force flag disables an optimization that keeps a colorinfo from resetting the last color.
    # This fails for controlbutton.py because the same palette is controlled by two different colorinfo
    # variables.
    def setColor(self, force=False):
        if self.widget == None: return  # true if cleanup in progress
        if self.widget.DebugFlag > 0 :print('setColor', self, self.alarmSensitive, self.alarmStatus)
        if self.widget.transparent == 1:
            col = edmColors.colorRule.invisible
        elif self.alarmSensitive and self.alarmStatus > 0:
            col = edmColors.getAlarmColor(self.alarmStatus, self.alarmpv.isValid )
        else:
            if self.colorRule == None:
                if self.widget.DebugFlag > 0 :print("colorInfo: no color rule!")
                return
            col = self.colorRule.getColor( self.colorValue)
        if col != self.lastColor or force:
            if self.widget.DebugFlag > 0 :print("Changing", self.widget, "palette", col, self.colorPalette, self.colorValue, self.alarmStatus, self.alarmSensitive)
            self.lastColor = col
            self.widget.setupPalette( col, self.colorPalette)
        return col

class edmWidget(edmWidgetSupport):
    ''' edmWidget - base class for all edm-style widgets.
            edmparent - containing widget
            DebugFlag - non-zero to print values to stdout
            visible - edm visibility flag (visPv, visMin, visMax edm fields used in calculation)
            lastVisible - previous state of the visibility flag
            transparent - non-zero if this widget is active without being displayed
            pvItem - dictionary of PVs for a widget; edmWidget's list contains most common PVs
                        array per instance: [0] - property name for related PV name; [1] property name for related PV class instance;
                                            [2] - if > 0, then call redisplay when pv in [1] updates;
                                            [3] - value callback function; [4] - value callback argument ;
                                            [5] - connect callback function ; [6] - connect callback argument
                    pvItem  might work better redefined as a class!
            object [defined in buildObject] - list of edm properties for this class read from a .edl file
            fgColorInfo [defined in findFgColor] - foreground color used for this widget
            bgColorInfo [defined in findBgColor] - background color used for this widget
                    NOTE that EDM distinguishes between a background color and a fill color, and how 'fill' is used with some text displays is not obvious.
            
            Some edmWidget instance properties are set indirectly from values in pvItem. In derived classes, class-specific properties are set indirectly
            from values in the pvItem property.
    '''
    def __init__(self, parent=None, **kw):
        if edmApp.DebugFlag :
            print("edmWidget __init__", self, parent, self.parent(), kw)
            traceback.print_stack()
        super().__init__(**kw)
        if parent == None:
            self.edmParent = self.parent()
        self.DebugFlag = edmApp.DebugFlag
        self.visible = 1
        self.lastVisible = 1
        self.transparent = 0
        # The 4 most common PV's. These can be over-ridden, and are not mandatory
        self.pvItem = { "controlPv" : [ "controlName", "controlPV", 1 ] ,
                "visPv" : [ "visName", "visPV", 0, self.onCheckVisible, None ],
                "alarmPv" : [ "alarmName", "alarmPV" ],
                "colorPv" : [ "colorName", "colorPV" ]
                    }
        #self.connect(self,SIGNAL("destroyed(QObject*)"), self.destructNotification)
        self.destroyed.connect(self.destructNotification)
        self.setStyle (edmApp.commonstyle)

    def destructNotification(self, me):
        if self.DebugFlag > 0 : print("destroying", me, "self:", self)
        self.cleanup()
        # del self

    def __del__(self):
        try:
            if self.DebugFlag > 0 : print("Deleting", self)
            self.cleanup()
        except Exception as N:
            if self.DebugFlag > 0 : print("__del__ failure for", self, N)

    def cleanup(self):
        '''remove callbacks and references to other objects'''
        # import sip
        # if self.DebugFlag > 0 :print("cleanup", self, sip.dump(self))
        # Not true errors - fgColorInfo, bgColorInfo might not exist with custom coloring information
        try: self.fgColorInfo.cleanup()
        except: pass
        try: self.bgColorInfo.cleanup()
        except: pass
        # if there is no valid Qt C++ component, quietly fail.
        try:
            for ch in self.children():
                if hasattr(ch, "cleanup") : ch.cleanup()
        except: pass

        # remove all known PV references
        for pvinfo in self.pvItem:
            self.delPV(self.pvItem[pvinfo][1])

    def delPV(self, pvname):
        '''delPV(pvname) - pvname is the attribute referencing a PV
        clean up callbacks, remove reference to the PV.
        Assumes that all referenced PV's are in the pvItem list'''
        try:
            pv = getattr(self, pvname, None)
            if pv != None:
                pv.del_callback(self)
                delattr(self, pvname)
        except RuntimeError:
            if hasattr(self, pvname):
                delattr(self, pvname)

    # Generic object creation
    def buildFromObject(self, object, attr=Qt.WA_TransparentForMouseEvents):
        if self.DebugFlag > 0: print("buildFromObject", object)
        self.setGeometry(object.getIntProperty("x")-1-self.edmParent.parentx,
        object.getIntProperty("y")-1-self.edmParent.parenty,
        object.getIntProperty("w")+2, object.getIntProperty("h")+2)
        self.object = object
        if attr != None:
            self.setAttribute(attr)
            self.setAttribute(Qt.WA_NoMousePropagation)
        #
        # Manage object visibility rules
        # do this before setting the visibility PV
        pvn = object.getStringProperty("visPv")
        if pvn != None:
            self.visMin = object.getDoubleProperty("visMin", 0.0)
            self.visMax = object.getDoubleProperty("visMax", 1.0)
            self.visInvert = object.getIntProperty("visInvert", 0)
            if self.visMin > self.visMax:
                self.visMin, self.visMax = self.visMax, self.visMin
            self.visible = 0
            self.lastVisible = 1
            self.setVisible(self.visible)
        # Manage display fonts
        # Do this before setting a PV that may cause a redisplay
        self.fontName = object.getStringProperty("font")
        if self.fontName != None:
            self.edmFont = edmFont.getFont(self.fontName)
            self.setFont(self.edmFont)
            if getattr(self, "setAlignment", None) != None:
                self.setAlignment( self.findAlignment("fontAlign"))
        #
        # Make generic PV connections
        #
        for tag in self.pvItem:
            self.pvSet(tag=tag)
        #
        # Manage object foreground and background colors
        # This expects that pv connections have already been made
        #
        self.findFgColor()
        self.findBgColor()
 
    @classmethod
    def getV3PropertyList(classRef, major, minor, release):
        '''get the list of property names for a V3 file. This should be over-ridden by each class'''
        idx = "%s-%s" % (major, minor)
        standard = ["x", "y", "w", "h" ]
        try:
            pt = standard + classRef.V3propTable[idx]
        except:
            print('no V3 table for', classRef, "index", idx)
            return standard
        return pt

    @classmethod
    def setV3PropertyList(classRef, propValue, tags):
        propName = classRef.getV3PropertyList(tags['major'], tags['minor'], tags['release'])
        if len(propValue) != len(propName):
            print("warning: mismatched property list", "class", tags['Class'], tags['major'], tags['minor'], len(propName), len(propValue))
            print(propName)
            print(propValue)

        for n,v in zip(propName, propValue):
            tags[n] = v


    def checkVisible(self):
        '''visibility check to be done before redisplay'''
        if self.lastVisible != self.visible:
            self.lastVisible = self.visible
            self.setVisible(self.visible)

    def redisplay(self):
        if self.DebugFlag > 0 :print('redisplay', self)
        self.checkVisible()
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        self.update()       # QT call to request a redraw.

    # Generic selection of foreground and background rules
    def findFgColor(self, fgcolor="fgColor", palette=(QPalette.WindowText,), alarmpv="FGalarm", fgalarm="fgAlarm"):
        self.fgColorInfo = self.findColor( fgcolor, palette, alarmpv, fgalarm)
        self.fgColorInfo.setColor()

    def findBgColor(self, bgcolor="bgColor", palette=(QPalette.Window,),
    alarmpv="BGalarm", bgalarm="bgAlarm", fillName="useDisplayBg", fillTest=1):
        self.bgColorInfo = self.findColor( bgcolor, palette, alarmpv, bgalarm, fillName, fillTest)
        self.bgColorInfo.setColor()

    # Generic selection of a palette entry. the Name pv's are the edm object
    # field names.
    # if fillName set, then this is the Field that, if == to fillTest, fill
    # with color, otherwise make transparent. This isn't exactly what EDM does.
    # NOTE: currently only called by findFgColor and findBgColor
    # if alarmName != 0, flag to look for alarm sensitivity
    def findColor( self, colorName, palette, alarmpv=None, alarmName=None, fillName=None, fillTest=True):
        if self.DebugFlag > 0 :print('findColor(', self, colorName, palette, alarmpv, alarmName, fillName, fillTest, ')')
        if self.DebugFlag > 0 :print('... alarmName=', self.object.getIntProperty(alarmName,0))
        # if there is a PV that we'll alarm against, list it here. Otherwise,
        # use the colorName to fill the background
        alarmid = self.getAlarmPv(alarmName)

        if fillName != None and self.object.getIntProperty(fillName, 0) == fillTest:
            colorRule = edmColors.findColorRule("builtin:transparent")
        else:
            colorRule = self.object.getColorProperty(colorName)
        rcinfo = reColorInfo(self, colorRule)
        rcinfo.colorPalette = palette
        if colorRule != None and len(colorRule.ruleList) > 1:
            self.setColorPV(rcinfo, colorName)
        if alarmid != None:
            rcinfo.addAlarmStatus(alarmid,self)
        return rcinfo

    #   default PV is the control PV, if there is one.
    def getAlarmPv(self, alarmName=None):
        # check if alarm sensitive: is so, find a PV to use
        if self.object.getIntProperty(alarmName, 0) == 0: return None
        return getattr(self, "alarmPV", getattr(self,"controlPV", None) )

    # Priority for using a color PV: "colorPV", "controlPV", "alarmPV"
    # individual widgets that don't agree with this list can over-ride the function.
    # colorName is available to select which PV's may be of interest.
    def setColorPV(self, rcinfo, colorName):
        if self.DebugFlag > 0 : print('setColorPV(', rcinfo, colorName, ')')
        if getattr(self, "colorPV", None) != None:
            rcinfo.addColorPV( self.colorPV)
        elif getattr( self, "controlPV", None) != None:
            rcinfo.addColorPV( self.controlPV)
        elif getattr( self, "alarmPV", None) != None:
            rcinfo.addColorPV(self.alarmPV)

    def findAlignment(self, alignName, defValue=Qt.AlignLeft):
        align = self.object.getStringProperty(alignName)
        if align != None:
            if align == "center" or align == "1":
                return Qt.AlignHCenter
            if align == "left" or align == "0":
                return Qt.AlignLeft
            if align == "right" or align == "2":
                return Qt.AlignRight
        return defValue
            
    # assign a color to a palette set
    def setupPalette(self, color, paletteList):
        if len(paletteList) == 0:
            print("setupPalette: ignoring widget", self, "color", color)
            return
        pal = self.palette()
        for colorRole in paletteList:
            pal.setColor( QPalette.Active, colorRole, color)
            pal.setColor( QPalette.Inactive, colorRole, color )
            pal.setColor( QPalette.Disabled, colorRole, color )
        self.setPalette(pal)

    # Creation of a tagged PV
    # This expects a number of things:
    # 1) that there is a dictionary 'pvItem' in this class
    # 2) that the value of pvItem[tag] is an array that has:
    #  i) the field to contain the pv Name
    #  ii) the field to contain the pv reference from buildPV
    #  iii) a field that is set to '1' if updates to this PV
    #       should cause a redisplay of the owning widget
    #  iv) a field that, if non-zero, is a widget callback
    #  v) a field that is the argument to the above callback
    #
    # the result is that 'setattr' creates widget."arg1" and
    # widget."arg2" for the pv reference
    #
    def pvSet(self, pvName=None, tag=None, checkChanged=False):
        '''create PV from the tag in the item list.
        'tag' must be specified and be a legitimate entry in pvItem[]
        if 'pvName' is specified, it is used instead of the 'tag' value.
        if 'checkChanged' is True, and the fully expanded PV name is
        different than the existing PV name, then the existing PV is
        replaced by a build of the new PV. This is used to support
        dynamic updates of the macro table.
        '''
        
        if tag not in self.pvItem:
            return None
        pvName = self.getName(pvName, tag)
        if pvName == None:
            return None
        item = self.pvItem[tag]
        mt = self.findMacroTable()
        if checkChanged:
            if edmApp.DebugFlag > 0: print("checkchanged:", pvName)
            oldPV = getattr(self, item[1], None)
            pref, newName = buildPVname(pvName, mt)
            if pref.upper() in pv.prefix and newName == pv.name:
                # no change
                return oldPV
            # get rid of the old PV
            self.delPV(item[1])

        setattr(self, item[0], pvName)
        connectCallback, connectCallbackArg = None, None
        if len(item) > 6 :
            connectCallback, connectCallbackArg = item[5:7]

        pv = buildPV(name=pvName, tag=tag, macroTable=mt,
            connectCallback=connectCallback, connectCallbackArg=connectCallbackArg)
        setattr(self, item[1], pv)
        if len(item) > 2 and item[2] == 1:
            pv.add_redisplay(self)
        if len(item) > 4 and item[3] != None:
            pv.add_callback(item[3], self, item[4])
        return pv

    # determine the name to use for a PV
    def getName(self, pvname, tag):
        if pvname != None and pvname != "":
            return pvname
        if tag in self.object.tagValue:
            return self.object.tagValue[tag]
        return None

    # change the visibility of a PV
    # only called if the corresponding keywords are set
    def onCheckVisible(self,  widget, value=None, **kw):
        self.lastVisible = self.visible
        try:
            value = float(value)
            self.visible = (value >= self.visMin and value < self.visMax)
            if self.visInvert > 0: self.visible = 1-self.visible
        except:
            # failures should force visibility
            print("onCheckVisible failure. Make it visible '%s'" % ( str(value),))
            self.visible = 1

        if self.lastVisible != self.visible:
            redisplay(self)
    #
    #
    # METHODS AND PROPERTIES TO SUPPORT WIDGET EDITING
    #
    #
    edmEditTitle = "Widget"
    edmEditPre = [ edmEditInt("x", "x", "x"), edmEditInt("y", "y", "y"), edmEditInt("w", "w", "w"), edmEditInt("h", "h", "h") ]
    edmEditList = []
    edmEditPost = []
    def buildEditWindow(self):
        pass

