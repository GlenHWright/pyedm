# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: high
#
# This is a high level module: 
# Generic widget support.
#
from builtins import zip
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QFontDatabase

from .edmPVfactory import buildPV, expandPVname, edmPVbase
from .edmApp import edmApp
from .edmObject import edmObject
from . import edmFont
from . import edmColors
from .edmField import edmField, edmTag
from .edmWidgetSupport import edmWidgetSupport
from .edmEditWidget import edmEdit, fontAlignEnum, edmRubberband
from .edmScreen import edmScreen

# assign a color to a palette set
def setupPalette(widget, color, paletteList):
    if len(paletteList) == 0:
        print("setupPalette: ignoring widget", widget, "color", color)
        return
    pal = widget.palette()
    for colorRole in paletteList:
        pal.setColor( QPalette.Active, colorRole, color)
        pal.setColor( QPalette.Inactive, colorRole, color )
        pal.setColor( QPalette.Disabled, colorRole, color )
    widget.setPalette(pal)

#
class reColorInfo:
    ''' 
        reColorInfo:
        Configuration and status information for a color for a widget.
        relates the Color Rule, the Color Value, the Alarm Status, and the
        Palette Set. When a change occurs to color value or alarm status,
        the widget "redisplay()" must be able to redraw
    '''
    def __init__(self, widget, cr=None):
        self.widget = widget
        self.alarmpv = None
        self.alarmSensitive = False
        self.alarmStatus = 0
        self.colorPV = None
        self.colorRule = cr
        self.colorValue = 0.0
        self.nullPV = None
        self.checkNull = False
        self.useNull = False
        self.nullColor = None
        self.colorPalette = ()
        self.lastColor = None

    def __repr__(self):
        return f"<reColorInfo {self.widget} {self.colorRule}>"

    def debug(self, *args, **kw):
        self.widget.debug(*args, **kw)

    def edmCleanup(self):
        try:
            self.alarmpv.del_callback(self)
            self.alarmpv = None
        except: pass
        try:
            self.colorPV.del_callback(self)
            self.colorPV = None
        except: pass
        self.widget = None      # break circular reference
        self.colorRule = None

    def addAlarmStatus(self, alarmPV, widget):
        ''' addAlarmStatus(alarmPV, widget) - called for an alarm sensitive color '''
        self.debug(1,mesg=f"addAlarmStatus {alarmPV}")
        self.alarmSensitive = True
        self.alarmpv = alarmPV
        alarmPV.add_callback( self.onAlarmUpdate, self)

    def addColorPV(self, colorPV):
        self.debug(mesg=f"addColorPV {self}, {colorPV}")
        self.colorPV = colorPV
        colorPV.add_callback( self.onColorUpdate, self)

    def addNullPV(self, *, nullPV, nullColor, nullTest):
        '''addNullPV(nullPV=pv, nullColor=colorRule, nullTest=callable(testThis) )'''
        self.debug(mesg=f"addNullPV {self}, {nullPV}")
        self.useNull = False
        self.nullPV = nullPV
        self.nullColor = nullColor
        self.nullTest = nullTest
        nullPV.add_callback( self.onNullUpdate, self)

    def onAlarmUpdate(self, widget, **kw):
        self.debug(1, mesg=f'onAlarmUpdate {self}, {kw}')
        if not self.alarmSensitive or "severity" not in kw:
            print("Useless onAlarmUpdate call!", self.alarmSensitive)
            return
        self.alarmStatus = kw["severity"]
        edmApp.redisplay(self.widget)
    
    def onColorUpdate(self, widget, **kw):
        self.debug(mesg=f"onColorUpdate, {self}, {kw}")
        if "value" in kw:
            self.colorValue = kw["value"]
            edmApp.redisplay(self.widget)

    def onNullUpdate(self, widget, **kw):
        self.debug(mesg=f"onNullUpdate, {self}, {kw}")
        if "value" not in kw:
            return

        self.useNull = self.nullTest(kw["value"])
        edmApp.redisplay(self.widget)

    # The force flag disables an optimization that keeps a colorinfo from resetting the last color.
    # This fails for controlbutton.py because the same palette is controlled by two different colorinfo
    # variables.
    def setColor(self, force=False):
        if self.widget == None: return  # true if edmCleanup in progress
        self.debug(mesg=f'setColor, {self} {self.alarmSensitive} {self.alarmStatus}')
        if self.widget.transparent:
            col = edmColors.colorRule.invisible
        elif self.alarmSensitive and (self.alarmStatus > 0 or not self.alarmpv.isValid):
            col = edmColors.getAlarmColor(self.alarmStatus, self.alarmpv.isValid )
        else:
            if self.colorRule == None:
                self.debug(mesg=f"colorInfo: no color rule!")
                return None
            if self.useNull:
                col = self.nullColor.getColor(self.colorValue)
            else:
                col = self.colorRule.getColor( self.colorValue)
        if col != self.lastColor or force:
            self.debug(mesg=f"Changing {self.widget} palette {col} {self.colorPalette} {self.colorValue} {self.alarmStatus} {self.alarmSensitive}")
            self.lastColor = col
            if len(self.colorPalette) > 0:
                setupPalette(self.widget, col, self.colorPalette)
        return col

@dataclass
class pvItemClass:
    '''
    manage potential PVs for an item
        attributeName - if creating this PV, widget.attributeName is the reference to the PV name (pre macro expansion!)
        attributePV - if creating this PV, widget.attributePV is the reference to the PV
        redisplay - hint that updates to this PV should force a redisplay call
        dataCallback - if set, on updates to this PV, call this function
        dataCallbackArg - pass this as an argument to a PV dataCallback
        conCallback - if set, on connection to this PV, call this function
        conCallbackArg - pass this as an argument to a PV conCallback
    '''
    attributeName: str
    attributePV: str
    redisplay: bool = False
    dataCallback: Callable[..., Any] = None
    dataCallbackArg: Any = None
    conCallback: Callable[..., Any] = None
    conCallbackArg: Any = None

class edmWidget(edmWidgetSupport):
    ''' edmWidget - base class for all edm-style widgets.
            edmparent - containing widget
            DebugFlag - non-zero to print values to stdout
            visible - edm visibility flag (visPv, visMin, visMax edm fields used in calculation)
            lastVisible - previous state of the visibility flag
            transparent - True if this widget is active without being displayed
            pvItem - dictionary of PVs for a widget; edmWidget's list contains most common PVs
                    if a subclass of edmWidget wants to add PVs, this should be done before calling edmWidget.buildFromObject()
            objectDesc [defined in buildObject] - list of edm properties for this class read from a .edl file
            fgColorInfo [defined in findFgColor] - foreground color used for this widget
            bgColorInfo [defined in findBgColor] - background color used for this widget
                    NOTE that EDM distinguishes between a background color and a fill color, and how 'fill' is used with some text displays is not obvious.
            
            Some edmWidget instance attributes are set indirectly from values in pvItem. In derived classes, class-specific attributes are set indirectly
            from values in the pvItem property.
    '''
    edmBaseFields = [ 
        edmField("Class", edmEdit.Class, defaultValue="Unknown", readonly=True),
        edmField("major", edmEdit.Int, defaultValue=4, hidden=True),
        edmField("minor", edmEdit.Int, defaultValue=0, hidden=True),
        edmField("release", edmEdit.Int, defaultValue=0, hidden=True),
        edmField("", edmEdit.HList, group= [
            edmField("x", edmEdit.Int, defaultValue=20),
            edmField("y", edmEdit.Int, defaultValue=60),
            edmField("z", edmEdit.Int, defaultValue=0, hidden=True)
            ] ),
        edmField("", edmEdit.HList, group= [
            edmField("w", edmEdit.Int, defaultValue=110),
            edmField("h", edmEdit.Int, defaultValue=85)
            ] )
        ]
    edmColorFields = [
        edmField("fgColor", edmEdit.Color, defaultValue=14),
        edmField("fgAlarm", edmEdit.Bool, defaultValue=False),
        edmField("bgColor", edmEdit.Color, defaultValue=0),
        edmField("bgAlarm", edmEdit.Bool, defaultValue=False),
        edmField("colorPv", edmEdit.PV),
        edmField("useDisplayBg", edmEdit.Bool, defaultValue=False)
        ]
    edmFontFields = [
            edmField("font", edmEdit.FontInfo, defaultValue="helvetica-medium-r-18.0"),
            edmField("fontAlign", edmEdit.FontAlign, enumList=fontAlignEnum, defaultValue=0)
        ]
    edmVisFields = [
            edmField("visPv", edmEdit.PV, defaultValue=None),
            edmField("visMin", edmEdit.Int, defaultValue=0),
            edmField("visMax", edmEdit.Int, defaultValue=1),
            edmField("visInvert", edmEdit.Bool, defaultValue=False)
        ]

    def __init__(self, parent=None, **kw):
        if edmApp.debug() :
            print("edmWidget __init__", self, parent, self.parent(), kw)
            traceback.print_stack()
        super().__init__(**kw)
        if parent == None:
            self.edmParent = self.parent()
        self.DebugFlag = edmApp.DebugFlag
        self.visible = True
        self.lastVisible = True
        self.transparent = False
        self.defaultFontTag = "textFont"
        self.defaultAlignTag = "textAlign"
        self.showEditWindow = None
        # The 4 most common PV's. These can be over-ridden, and are not mandatory
        self.pvItem = {
                "controlPv" : pvItemClass("controlName", "controlPV", redisplay=True) ,
                "visPv" : pvItemClass( "visName", "visPV", dataCallback=self.onCheckVisible),
                "alarmPv" : pvItemClass( "alarmName", "alarmPV" ),
                "colorPv" : pvItemClass( "colorName", "colorPV" )
                    }
        self.destroyed.connect(self.destructNotification)
        self.setStyle (edmApp.commonstyle)

    def __repr__(self):
        return f"<edmWidget {self.__class__}>"

    def destructNotification(self, me):
        if self.debug() : print("destroying", me, "self:", self)
        self.edmCleanup()

    def edmCleanup(self):
        '''remove callbacks and references to other objects'''
        # import sip
        # if self.debug() :print("edmCleanup", self, sip.dump(self))
        # Not true errors - fgColorInfo, bgColorInfo might not exist with custom coloring information
        try:
            self.fgColorInfo.edmCleanup()
        except AttributeError:
            pass
        try:
            self.bgColorInfo.edmCleanup()
        except AttributeError:
            pass
        # if there is no valid Qt C++ component, quietly fail.
        try:
            for ch in self.children():
                if hasattr(ch, "edmCleanup") : ch.edmCleanup()
        except: pass

        # remove all known PV references
        for pvinfo in self.pvItem:
            self.delPV(pvRef=self.pvItem[pvinfo].attributePV, attrName=self.pvItem[pvinfo].attributeName)

        self.edmParent = None
        try:
            self.objectDesc.edmCleanup()
            self.objectDesc = None
        except AttributeError:
            pass

    def delPV(self, *, pv=None, pvRef, attrName=None):
        '''delPV(pvname) - pvname is the attribute referencing a PV
        clean up callbacks, remove reference to the PV.
        Optionally removes the reference to the PV name if attrName set.
        Assumes that all referenced PV's are in the pvItem list
        '''
        try:
            if pv == None:
                pv = getattr(self, pvRef, None)
        except RuntimeError:
            return

        if pv != None:
            pv.edmCleanup()

        if hasattr(self, pvRef):
            delattr(self, pvRef)

        if attrName != None and hasattr(self,attrName):
            delattr(self, attrName)


    @classmethod
    def buildFieldListClass(cls, *attributeList):
        ''' build an edm field list for this class.
            the optional arguments list additional edmField lists to be inserted
        '''
        try:
            if len(attributeList) == 0:
                attributeList = ("edmEntityFields",)
            fields = cls.edmBaseFields + cls.edmColorFields
            for attr in attributeList:
                fields = fields + getattr(cls, attr)
            fields = fields + cls.edmVisFields
        except AttributeError:
            fields = cls.edmBaseFields + cls.edmColorFields + cls.edmVisFields
            print(f"built edmFieldList for {cls} with generic fields")
        cls.edmFieldList = fields

    def buildFieldList(self, obj=None):
        '''
            buildFieldList - take edmEntityFields, insert the default prefix and suffix items.
            note that edmFontFields is not added at this level - each widget must provide
            that, even though there is a common list available from the edmWidget class.
            Part 2: provide a link from 'tags' to 'fields'.
        '''
        if not hasattr(self, "edmFieldList"):
            self.buildFieldListClass()

        if obj == None:
            obj = self.objectDesc

        obj.edmFields = self.edmFieldList

        for item in self.edmFieldList:
            if item.tag in obj.tags:
                obj.tags[item.tag].field = item
            for subitem in item.group:
                if subitem.tag in obj.tags:
                    obj.tags[subitem.tag].field = subitem

    # C++ EDM often draws borders and such outside the specified widget geometries.
    # items often need some adjustment. Although there was an attempt here to have a
    # generic resize that worked for all widgets, it works equally bad for all
    # widgets. It has been removed.
    def setObjectGeometry(self):
        '''setObjectGeometry: adapt object geometry to Qt geometry'''
        x = int(self.objectDesc.getProperty("x")*edmApp.rescale)-self.edmParent.parentx
        y = int(self.objectDesc.getProperty("y")*edmApp.rescale)-self.edmParent.parenty
        w = int(self.objectDesc.getProperty("w")*edmApp.rescale)
        h = int(self.objectDesc.getProperty("h")*edmApp.rescale)

        self.setGeometry(x,y,w,h)

        if self.edmParent.rubberband != None:
            if self.edmParent.rubberband.edmWidget == self:
                self.edmParent.rubberband.setGeometry(x,y,w,h)


    def buildFromObject(self, objectDesc, *, attr=Qt.WA_TransparentForMouseEvents, rebuild=False, **kw):
        '''
            buildFromObject() - set Qt Widget fields based on attributes gathered
            from an edm description list.
         Generic object creation.
         Note that this is almost always over-ridden, and almost always the right
         thing to do first. Most inheriting classes will over-ride, and then
         make an immediate call to 'edmWidget.buildFromObject()' (or super()).
        '''
        if self.debug(): print("buildFromObject", objectDesc)
        self.objectDesc = objectDesc
        self.setObjectGeometry()
        if attr != None:
            self.setAttribute(attr)
            self.setAttribute(Qt.WA_NoMousePropagation)
        #
        # Manage object visibility rules
        # do this before setting the visibility PV
        if objectDesc.checkProperty("visPv"):
            self.visMin = objectDesc.getProperty("visMin", 0.0)
            self.visMax = objectDesc.getProperty("visMax", 1.0)
            self.visInvert = objectDesc.getProperty("visInvert")
            if self.visMin > self.visMax:
                self.visMin, self.visMax = self.visMax, self.visMin
            self.visible = True
            self.lastVisible = False
            self.setVisible(self.visible)

        self.setEdmFont()
        #
        # Make generic PV connections
        #
        for tag in self.pvItem:
            self.pvSet(tag=tag, checkChanged=rebuild)
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
            print('note: no V3 table for', classRef, "index", idx)
            return standard
        return pt

    @classmethod
    def setV3PropertyList(classRef, propValue, obj):
        propName = classRef.getV3PropertyList(obj.tags['major'].value, obj.tags['minor'].value, obj.tags['release'].value)
        if len(propValue) != len(propName):
            print("warning: mismatched property list", "class", obj.tags['Class'], obj.tags['major'].value, obj.tags['minor'].value, len(propName), len(propValue))
            print(propName)
            print(propValue)

        for n,v in zip(propName, propValue):
            obj.tags[n] = edmTag(n,v)

    def checkVisible(self):
        '''visibility check to be done before redisplay'''
        if self.lastVisible != self.visible:
            self.lastVisible = self.visible
            self.setVisible(self.visible)

    def redisplay(self):
        if self.debug() :print('redisplay', self)
        self.checkVisible()
        self.fgColorInfo.setColor()
        self.bgColorInfo.setColor()
        self.update()       # QT call to request a redraw.

    # default setting of font for a widget.
    # recommend against over-riding this method, and instead update the
    # defaultFontTag and defaultAlignTag.
    def setEdmFont(self, fontTag="font"):
        # Manage display fonts
        # Do this before setting a PV that may cause a redisplay
        # if there is a default font, then need to change how the test is done here.
        if self.checkProperty(fontTag):
            self.edmFont = self.getProperty(fontTag)
        else:
            self.edmFont = self.getScreenProperty(self.defaultFontTag)
        if self.debug() : print(f"font: {self.edmFont}")
        # if this widget supports setting alignment, interpret the fontAlign tag
        if getattr(self, "setAlignment", None) != None:
            self.setAlignment( self.findAlignment())
        if self.edmFont != None:
            self.setFont(self.edmFont)

    # find the alignment for a widget
    def findAlignment(self, defValue=Qt.AlignLeft):
        if self.objectDesc.checkProperty("fontAlign"):
            align = self.objectDesc.getProperty("fontAlign")
        else:
            align = self.getScreenProperty(self.defaultAlignTag)
        if align != None:
            if align.value == 0:
                return Qt.AlignLeft
            if align.value == 1:
                return Qt.AlignHCenter
            if align.value == 2:
                return Qt.AlignRight
        return defValue

    # Generic selection of foreground and background rules
    def findFgColor(self, fgcolor="fgColor", palette=(QPalette.WindowText,),
            fgalarm="fgAlarm"):
        self.fgColorInfo = self.findColor( fgcolor, palette, alarmName=fgalarm)
        self.fgColorInfo.setColor()

    def findBgColor(self, bgcolor="bgColor", palette=(QPalette.Window,),
            bgalarm="bgAlarm", fillName="useDisplayBg", fillTest=True):
        self.bgColorInfo = self.findColor( bgcolor, palette, alarmName=bgalarm, fillName=fillName, fillTest=fillTest)
        self.bgColorInfo.setColor()

    # Generic selection of a palette entry. the Name pv's are the edm object
    # field names.
    # if fillName set, then this is the Field that, if equal to fillTest, fill
    # with color, otherwise make transparent. This isn't exactly what EDM does.
    # NOTE: mostly called by findFgColor and findBgColor
    # if alarmName != 0, flag to look for alarm sensitivity.
    # if alarmPV != None, alternative name to check for alarm.
    def findColor( self, colorName, palette, *, alarmName=None, alarmPV="alarmPV", fillName=None, fillTest=True):
        if self.debug(1):
            print('findColor(', self, colorName, palette, alarmPV, alarmName, fillName, fillTest, ')')
            if alarmName != None:
                print(f'... {alarmName} alarmName=', self.objectDesc.getProperty(alarmName))

        # if there is a PV that we'll alarm against, list it here.
        alarmid = self.getAlarmPv(alarmName, alarmPV)

        # should only be set for backgrounds - a fill name to use against fillTest
        # and the colorName to use to fill the background
        if fillName != None and self.objectDesc.getProperty(fillName) == fillTest:
            colorRule = edmColors.findColorRule("builtin:transparent")
        else:
            colorRule = self.objectDesc.getProperty(colorName)
        if self.debug() : print(f"findColor {colorName}-> CR {colorRule} isRule: {colorRule.isRule()}")
        rcinfo = reColorInfo(self, colorRule)
        rcinfo.colorPalette = palette
        if colorRule != None and colorRule.isRule():
            self.setColorPV(rcinfo, colorName)
        if alarmid != None:
            rcinfo.addAlarmStatus(alarmid,self)
        return rcinfo

    def getAlarmPv(self, alarmName, alarmPV):
        ''' getAlarmPv(self, alarmName, alarmPV)
            if alarmName exists and has a not False value, then
                widget is alarm sensitive.
            if alarmPV set, use this PV, otherwise use controlPV,
                otherwise colorPV.
        '''
        # check if alarm sensitive: is so, find a PV to use
        if self.objectDesc.checkProperty(alarmName) == False:
            return None
        if self.objectDesc.getProperty(alarmName) == False:
            return None
        for pvname in [ alarmPV, "indicatorPV", "controlPV", "colorPV" ]:
            pv = getattr(self, pvname, None)
            if pv != None:
                return pv
        return None

    # Priority for using a color PV: "colorPV", "controlPV", "alarmPV"
    # individual widgets that don't agree with this list can over-ride the function.
    # colorName is available to select which PV's may be of interest.
    def setColorPV(self, rcinfo, colorName):
        if self.debug() : print('setColorPV(', rcinfo, colorName, ')')
        if getattr(self, "colorPV", None) != None:
            rcinfo.addColorPV( self.colorPV)
        elif getattr( self, "indicatorPV", None) != None:
            rcinfo.addColorPV( self.indicatorPV)
        elif getattr( self, "controlPV", None) != None:
            rcinfo.addColorPV( self.controlPV)
        elif getattr( self, "alarmPV", None) != None:
            rcinfo.addColorPV(self.alarmPV)

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
        
        item = self.pvItem[tag]
        pvName = self.getName(pvName, tag)
        if pvName == None or pvName == "":
            if checkChanged:
                oldPV = getattr(self, item.attributePV, None)
                if oldPV != None:
                    self.delPV(pvRef=item.attributePV, attrName=item.attributeName)
            return None

        mt = self.findMacroTable()
        # Usually only True when rebuilding a widget.
        if checkChanged:
            if edmApp.debug(): print("checkchanged:", pvName)
            oldPV = getattr(self, item.attributePV, None)
            if oldPV != None:
                pref, newName = expandPVname(pvName, mt)
                if pref.upper() == oldPV.prefix and newName == oldPV.name:
                    # no change
                    return oldPV
            # get rid of the old PV
            self.delPV(pvRef=item.attributePV, attrName=item.attributeName)

        setattr(self, item.attributeName, pvName)

        pv = buildPV(pvName, macroTable=mt,
            connectCallback=item.conCallback, connectCallbackArg=item.conCallbackArg)
        setattr(self, item.attributePV, pv)
        if item.redisplay:
            pv.add_redisplay(self)
        if item.dataCallback:
            pv.add_callback(item.dataCallback, self, item.dataCallbackArg)
        return pv

    # determine the name to use for a PV. 'None' is a valid return, indicating
    # that this tag doesn't have a valid value
    def getName(self, pvname, tag):
        if pvname != None and pvname != "":
            return pvname
        if self.objectDesc.checkProperty(tag):
            return self.objectDesc.getProperty(tag, None)
        return None

    # change the visibility of a PV
    # only called if the corresponding keywords are set
    def onCheckVisible(self,  widget, value=None, **kw):
        self.lastVisible = self.visible
        try:
            value = float(value)
            self.visible = (value >= self.visMin and value < self.visMax)
            if self.visInvert : self.visible = not self.visible
        except:
            # failures should force visibility
            print("onCheckVisible failure. Make it visible '%s'" % ( str(value),))
            self.visible = True

        if self.lastVisible != self.visible:
            edmApp.redisplay(self)

    def getProperty(self, *args, **kw):
        ''' convenience function - objectDesc.getProperty called
        '''
        try:
            return self.objectDesc.getProperty(*args, **kw)
        except AttributeError as exc:
            print(f"widget {self} getProperty failure {exc}")

    def checkProperty(self, tag):
        return self.objectDesc.checkProperty(tag)

    def getScreenProperty(self, tag):
        ''' getScreenProperty(self, tag) - find the parent that has screen parameters
            and get the property value of 'tag'
            Returns None on failure
        '''
        try:
            return self.getParentScreen().getProperty(tag)
        except AttributeError:
            return None

    def getParentScreen(self):
        parent = self
        while(True):
            if not hasattr(parent, "edmParent") or parent.edmParent == None:
                return parent
            if parent.checkProperty("Filename"):
                return parent
            parent = parent.edmParent

    #
    #
    # METHODS AND PROPERTIES TO SUPPORT WIDGET EDITING
    #
    #

    def editMode(self, *args, **kw):
        if self.debug() : print(f"editMode {self} {kw}")
        try:
            return self.edmParent.editMode(*args, **kw)
        except AttributeError:
            return False

    def getEditPropertiesList(self):
        '''
            getEditPropertiesList
            alternative to set edmFieldList for an instance,
            as opposed to a class.

            if the widget defines edmEntityFields, then return
            a list that includes the prefix and suffix Fields.
            Note that edmFontFields is only included if "font" is
            included in tags.
        '''
        if hasattr(self, "edmFieldList"):
            return self.edmFieldList
        #
        eef = getattr(self, "edmEntityFields", None)
        if eef:
            if hasattr(self.objectDesc.tags, "font"):
                return self.edmBaseFields + eef + self.edmFontFields + self.edmVisFields
            else:
                return self.edmBaseFields + eef + self.edmVisFields
        return self.objectDesc.tags

    def updateTags(self, taglist):
        '''
            update the common tags
        '''
        objDesc = self.objectDesc
        rebuild = False
        for tag in taglist.values():
            current = objDesc.tags.get(tag.tag)
            if current:
                if current.value == tag.value:
                    # no change
                    next
                tag.field = current.field
            elif not self.setTagField(tag):
                print(f"updateTags: Tag field not found for {tag.tag}")
                rebuild = True
                continue

            if tag.tag not in [ "x", "y", "w", "h" ] :
                rebuild = True

            objDesc.tags[tag.tag] = tag

        if rebuild == True:
            self.buildFromObject(objDesc, rebuild=True)
        else:
            self.setObjectGeometry()

    def setTagField(self, tag):
        return self.setTagFieldItem(tag, self.edmFieldList)

    @classmethod
    def setTagFieldItem(cls, tag, fieldList):
        for field in fieldList:
            if field.tag == tag.tag:
                tag.field = field
                return True
            if len(field.group) > 0:
                if cls.setTagFieldItem(tag, field.group):
                    return True
        return False

def buildNewWidget(parent, source, widgetClassRef=None, position=None, startEdit=True):
    '''
        addWidget(source) add a new widget onto the parent screen.
        if 'source' is an edmObject, creates a widget
        if 'source' is a str, generate a list of tags and default values
            for an 'edmWidget', and then create the specified class.
        if 'source' looks like a list of edmTag, then create an
            edmObject, assign the tags, then create the widget.
        if 'source' looks like a json input, convert it to tag objects,
            and then create a widget
        if 'position' (in global units) is defined, modify the x,y to match.
        if 'startEdit' is true, start an edit window and a rubberband widget for this widget.
    '''
    objParent = getattr(parent, "edmScreenRef", None)
    if type(source) == dict:
        obj = edmObject(objParent)
        edmScreen.buildJSONobject(source, obj)
        source = obj
    if type(source) == list:
        obj = edmObject(objParent)
        obj.tags.update(source)
        source = obj
    if type(source) == str:
        obj = edmObject(objParent)
        for field in edmWidget.edmBaseFields:
            if field.group:
                for f2 in field.group:
                    obj.addTag(f2.tag, f2.defaultValue)
            else:
                obj.addTag(field.tag, field.defaultValue)
        obj.addTag("Class", source)
        source = obj

    if not isinstance(source, edmObject):
        raise TypeError(f"buildNewWidget unable to interpret {source} type {type(source)}")

    if widgetClassRef == None:
        otype =  obj.tags["Class"].value
        if edmApp.debug() :  print("checking object type", otype)
        try:
            widgetClassRef = edmApp.edmClasses[otype]
        except:
            raise TypeError(f"buildNewWidget: Unknown object type {otype}")
    widget = widgetClassRef(parent)
    if position != None:
        pos = widget.edmParent.mapFromGlobal(position)
        obj.addTag("x", pos.x())
        obj.addTag("y", pos.y())
    widget.buildFieldList(obj)
    widget.buildFromObject(obj)
    if startEdit:
        # start editor, create rubberband
        parent.rubberband = edmRubberband(widget=widget)
        parent.selectedWidget = widget
        parent.edmShowEdit(parent.selectedWidget)
        parent.editMode(value="move")
    widget.show()
    return widget

####
#### over-write edmApp placeholders
####
edmApp.edmWidget = edmWidget
