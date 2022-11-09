# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: mid
#
# This is a mid level module. It is referenced from 
#   edmObject.py and edmScreen.py, and must not
#   import those modules either directly or indirectly.
#
# conversion routines to change input strings to appropriate types.
#

from PyQt5.QtGui import QFont

from . import edmEditWidget
from . import edmColors
from . import edmFont
from .edmPVfactory import edmPVbase
from .edmField import edmTag


def decode( tagRef, fieldRef=None, count=-1, defValue=None):
# Decode a { ... } sequence, stripping the numeric 0st column and returning a
# list of second columns. A missing tag, or missing entries, are filled in
# with the default value.
    values = tagRef.value
    if fieldRef == None:
        fieldRef = tagRef.field

    if count <= 0:
        count = len(values)

    fakeTag = edmTag(tagRef.tag, None, fieldRef)
    if fieldRef != None:
        if defValue is None and fieldRef.defaultValue is not None:
            defValue = fieldRef.defaultValue
        if fieldRef.enumList:
            fakeTag.value = defValue
            defValue = converter(fakeTag, fieldRef, defValue)
            rval = [defValue]*count
        else:
            rval = [defValue]*count
    else:
        rval = [defValue] * count
    idx = -1
    for val in values:
        if type(val) != str:
            idx = idx+1
            fakeTag.value = val
            rval[idx] = converter(fakeTag, fieldRef, defValue)
        else:
            # check if a string.
            if val[0] == "\"":
                strVal = val
                idx = idx + 1
            else:
                # determine if we're decoding an unindexed (single value) or indexed (two value) entry on the line
                strVal = val.split(" ", 1)
                if len(strVal) == 2:
                    try:
                        idx = int(strVal[0])
                        strVal = strVal[1]
                    except ValueError:
                        strVal = val
                        idx = idx + 1

                    while idx >= len(rval):     # this can happen when decoding an unknown length.
                        rval.append(defValue)
                        count += 1
                else:
                    strVal = val
                    idx = idx + 1
            if strVal[0] == "\"":
                strVal = strVal.strip("\"")
            fakeTag.value = strVal

        if idx < 0 or idx >= count:
            print(f"decode: index out of range: {idx} of {count}, value:{val} for tag {fakeTag.tag}")
            continue
        rval[idx] = converter(fakeTag, fieldRef, defValue)
    return rval

def getIntProperty(tagRef, fieldRef, defValue=None):
    if type(tagRef.value) is int:
        return tagRef.value
    try:
        w = tagRef.value.split(" ", 1)
        if len(w) == 2 and w[1] != "0":
            return defValue
    except AttributeError:  # tagRef.value not a string?
        if tagRef.value is None:
            if defValue is None:
                return 0
            return defValue
        w = [tagRef.value]
    if w[0] == '"':
        w[0] = w[0].strip('"')
    try:
        val = int(w[0])
    except ValueError:
        val = defValue
    return val

def getDoubleProperty(tagRef, fieldRef, defValue=None):
    if type(tagRef.value) is float:
        return tagRef.value
    try:
        w = tagRef.value.split(" ", 1)
    except AttributeError:
        if defValue == None:
            return 0.0
        return defValue
    if len(w) == 2 and w[1] != "0":
        return defValue
    try:
        val = float(w[0])
    except ValueError:
        val = defValue
    return val

def getBoolProperty( tagRef, fieldRef, defValue=None):
    if type(tagRef.value) == bool:
        return tagRef.value
    val = getIntProperty( tagRef, fieldRef, defValue)
    return val != 0

def getStringProperty( tagRef, fieldRef, defValue=""):
    value = tagRef.value
    try:
        if value[0] == "\"" and value[-1] == "\"":
            return value[1:-1]
    except IndexError:
        return defValue
    except TypeError:
        return defValue
    return value

def getColorProperty( tagRef, fieldRef, defValue=None):
    if isinstance(tagRef.value, edmColors.colorRule):
        return tagRef.value
    if tagRef:
        value = tagRef.value
    elif fieldRef:
        value = fieldRef.defaultValue
    else:
        value = defValue
    return edmColors.findColorRule(value)

def getFontProperty( tagRef, fieldRef, defValue=None):
    if isinstance(tagRef.value,QFont):
        return tagRef.value
    if tagRef:
        value = tagRef.value
    elif fieldRef:
        value = fieldRef.defaultValue
    else:
        value = defValue
    if type(value) in [ str, dict ]:
        return edmFont.getFont(tagRef.value)

    return value

def getPVProperty( tagRef, fieldRef, defValue=None):
    if isinstance(tagRef.value,edmPVbase):
        return tagRef.value
    value = tagRef.value
    try:
        if value[0] == "\"" and value[-1] == "\"":
            return value[1:-1]
    except IndexError:
        value = defValue
    except TypeError:
        value = defValue
    if value == None:
        return ""
    return value

def getEnumProperty(  tagRef, fieldRef, defValue=None):
    ''' getEnumProperty(...)
        this returns a type 'Enum'
    '''
    try:
        val = toEnum(fieldRef, tagRef.value)
    except ValueError:
        print(f"getEnumProperty tagRef.value failed: {tagRef.value}")
        val = toEnum(fieldRef, defValue)      # if this fails, indicates a configuration error
    return val

def toEnum(fieldRef, value):
    if value == None:
        return None
    if type(value) == int:
        return fieldRef.enumList(value)
    if type(value) == str:
        return fieldRef.enumList[value]
    try:
        if value in fieldRef.enumList:
            return value
    except TypeError:
        pass
    return None

def converter(tag, fieldRef, defValue):
    if fieldRef == None:
        return tag.value
    if fieldRef.editClass not in conversionTable:
        return getStringProperty(tag, fieldRef, defValue)
    return conversionTable[fieldRef.editClass](tag, fieldRef, defValue)

# conversionTable is a local list of conversion function to be called depending on the
# type of edit widget.
conversionTable = {}
conversionTable[edmEditWidget.edmEditInt                ] = getIntProperty
conversionTable[edmEditWidget.edmEditString             ] = getStringProperty
conversionTable[edmEditWidget.edmEditEnum               ] = getEnumProperty
conversionTable[edmEditWidget.edmEditCheckButton        ] = getBoolProperty
conversionTable[edmEditWidget.edmEditBool               ] = getBoolProperty
conversionTable[edmEditWidget.edmEditColor              ] = getColorProperty
conversionTable[edmEditWidget.edmEditPV                 ] = getPVProperty
conversionTable[edmEditWidget.edmEditReal               ] = getDoubleProperty
conversionTable[edmEditWidget.edmEditTextBox            ] = getStringProperty
conversionTable[edmEditWidget.edmEditSubScreen          ] = getStringProperty
conversionTable[edmEditWidget.edmEditFontInfo           ] = getFontProperty
conversionTable[edmEditWidget.edmEditFontAlign          ] = getEnumProperty
conversionTable[edmEditWidget.edmEditFilename           ] = getStringProperty
conversionTable[edmEditWidget.edmEditStripchartCurve    ] = getStringProperty
conversionTable[edmEditWidget.edmEditSymbolItem         ] = getStringProperty
conversionTable[edmEditWidget.edmEditSymbolItemSelect   ] = getStringProperty
