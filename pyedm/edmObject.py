# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
# This is a low level module, and must only import base level modules

from enum import Enum

from PyQt5.QtGui import QFont

from .edmApp import edmApp
from .edmProperty import converter, toEnum, decode
from . import edmColors
from . import edmFont
from .edmField import edmTag

#
# A class that defines a generic EDM object. (A single widget)
# tags{} - dictionary indexed by tag name - see edmField.edmTag
class edmObject:
    ''' edmObject - manages the properties that define an edmWidget
    '''
    def __init__(self, parent=None):
        self.tags = {}
        self.edmFields = None
        self.debug(setDebug=edmApp.DebugFlag)
        self.edmParent = parent
        if parent != None:
            parent.objectList.append(self)

    def edmCleanup(self):
        self.tags = None
        self.edmFields = None
        self.edmParent = None

    def debug(self, level=1, *, mesg=None, setDebug=None):
        if setDebug != None:
            self.DebugLevel = setDebug
        try:
            flag = self.DebugLevel >= level
        except AttributeError:
            flag = edmApp.DebugLevel >= level
        if flag and (mesg != None):
            print(mesg)
        return flag

    def addTag(self, field, value):
        if edmApp.debug(1) : print(f"add tag {field} value *{value}*")
        self.tags[field] = edmTag(field, value)

    # Return properties of a converted type. There must be a more pythonesque
    # way of doing this.
    def getProperty(self, field, defValue=None, arrayCount=None):
        '''
        return a property entry (aka field tag), attempting to convert to the correct type.
        if edmFields not configured, return tag value or default value (no conversion)
        if edmFields and tags and tags.field != None, convert the selected entry
        according to the conversion table.
        '''
        # if there wasn't a supplied value for this tag, return a default value. 
        if field not in self.tags:
            fieldRef = self.findField(field)
            # print(f"field {field} fieldRef {fieldRef} defValue {defValue} arrayCount {arrayCount}")
            # attempt to return a generic default value
            if fieldRef == None:
                if defValue != None:
                    return defValue
                print(f"no tag, no edmField for {field}!")
                print([v.tag for v in self.edmFields])
            else:
                defValue = fieldRef.defaultValue
                # test for Enum
                if fieldRef.enumList != None:
                    defValue = toEnum(fieldRef, defValue)
                else:
                    fakeTag = edmTag(field, defValue, fieldRef)
                    defValue = converter( fakeTag, fieldRef, defValue)
            if arrayCount == None:
                return defValue
            return [defValue] * arrayCount

        tagRef = self.tags[field]
        if tagRef.field == None:
            tagRef.field = self.findField(tagRef.tag)
            if tagRef.field == None:
                print(f"missing fieldRef for {field} {tagRef.tag}")
                if arrayCount == None:
                    return tagRef.value
                return decode( tagRef, None, arrayCount, defValue)

        # at this point - we have valid tagRef and tagRef.field.
        # check whether creating an array or a single value
        if arrayCount == None and tagRef.field.array == False:
            val = converter( tagRef, tagRef.field, defValue)
        elif arrayCount == None:
            val = decode( tagRef, tagRef.field, -1, defValue)
        else:
            val = decode( tagRef, tagRef.field, arrayCount, defValue)
        return val

    def findField(self, field):
        ''' find a field entry with a tag matching 'field'
        '''
        for fieldEntry in self.edmFields:
            if fieldEntry.tag == field:
                return fieldEntry
            for subfield in fieldEntry.group:
                if subfield.tag == field:
                    return subfield
        print(f"Can't find entry for field {field} Class {self.tags['Class'].value}")
        return None

    def checkProperty(self, field):
        ''' simple test to see if 'field' is listed in the list of tags entered '''
        return field in self.tags

    def show(self):
        if self.debug():
            if hasattr(self, "edmParent"):
                print("edmParent", self.edmParent.tags["Class"].value)
            for idx, val in self.tags.items():
                print(f"Key:{idx}  Value:{val.value} type:{val.field}")
            print("- - - - - - - - -")
