from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
from builtins import object
from pyedm.edmApp import edmApp
import pyedm.edmColors as edmColors
import pyedm.edmFont as edmFont

#
# A class that defines a generic EDM object. (A single widget)
# All properties from the data file are stored in the dictionary 'self.tagValue'
# self.tagType can be used for special cases (edm does this, I'm not sure
# python needs it
class edmObject(object):
    def __init__(self, parent=None):
        self.tagValue = {}
        self.tagType = {}
        self.debugFlag = edmApp.DebugFlag
        self.edmParent = parent
        parent.objectList.append(self)


    # Return properties of a converted type. There must be a more pythonesque
    # way of doing this.
    def getIntProperty(self, field, defValue=None):
        if field in self.tagValue:
            return int(self.tagValue[field])
        return  defValue

    def getEfIntProperty(self, field, defValue=None):
        if field in self.tagValue:
            w = self.tagValue[field].split(" ")
            if len(w) == 1 or (len(w) > 1 and w[1] == "0"):
                return int(w[0])
        return defValue

    def getDoubleProperty(self, field, defValue=None):
        try:
            w = self.tagValue[field].split(" ")
            if len(w) == 1 or (len(w) > 1 and w[1] == "0"):
                return float(w[0])
        except:
            pass

        return defValue

    def getStringProperty(self, field, defValue=None):
        if field in self.tagValue:
            return self.tagValue[field]
        return defValue

    def getColorProperty(self, field, defValue=None):
        if field not in self.tagValue:
            return defValue
        return edmColors.findColorRule(self.tagValue[field])

    def getFontProperty(self, field, defValue=None):
        if field not in self.tagValue:
            return defValue
        return edmFont.getFont(self.tagValue[field])

    def getEnumProperty( self, field, enum, defValue=None):
        if field not in self.tagValue:
            return defValue
        return enum.index(self.tagValue[field])

    def checkProperty(self, field):
        return field in self.tagValue

    def show(self):
        if self.debugFlag > 0:
            if hasattr(self, "edmParent"):
                print("edmParent", self.edmParent.tagValue["Class"])
            for idx, val in self.tagValue.items():
                print("Key:", idx, " Value:", val)
            print("- - - - - - - - -")

    # Decode a { ... } sequence, stripping the numeric 1st column and returning a
    # list of second columns
    # Now, what should be the action when missing?
    def decode(self, tag,count=-1,defValue=None, isString=False):
        ''' decode single or double column of values
            if isString is true, always interpret the value column as a string
            '''
        if tag not in self.tagValue:
            return None
        if count <= 0:
            count = len(self.tagValue[tag])
        rval = [defValue]*count
        idx = -1
        for val in self.tagValue[tag]:
            if val[0] == "\"":
                str = val
                idx = idx + 1
            else:
                str = val.split(" ", 1)
                if len(str) == 1:
                    str = val
                    idx = idx + 1
                else:
                    try:
                        idx = int(str[0])
                        str = str[1]
                    except ValueError:
                        str = val
                        idx = idx + 1

            if idx < 0 or idx >= count:
                print(f"decode: index out of range: {idx} of {count}, string:{val}")
                continue
            # decide if we're decoding a color, a string, an int, or a double
            if str.startswith("index "):
                rval[idx] = edmColors.findColorRule(str)
            elif str[0] == "\"":
                rval[idx] = str.strip("\"")
            elif isString:
                rval[idx] = str
            else:
                try:
                    v = float(str)
                    if v == float(int(v)):
                        rval[idx] =  int(v)
                    else:
                        rval[idx] = v
                except:
                    rval[idx] = str
        return rval
