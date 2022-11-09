# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: base
#
# This is a base-level module, and must not call any other pyedm modules
'''
edmField - hold the definition of a single user field for an edmWidget.
    tag - field name used in .edl files (and .jsonedl?)
    editClass - class reference for building a widget
    enumlist = if this field is an enum, then the list of values.
    readonly - for fields that are maintained in another manner
'''
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

#
# What's the difference between edmField and edmEditField?
# an edmField list is defined once for each class of objects.
# an edmEditField list is created when an instance of a class
# is going to be edited, and edmField is used to create that list.
#
@dataclass
class edmField:
    '''
        edmField
        static definition of characteristics of a single property of an edm widget
        each widget type must have a list of definitions of field types.
        mandatory fields: tag - .edl/json identifier
            editClass - edmEditField class definition
            defaultValue - to be used when no value available.
    '''
    tag : str                       # .edl (and json) identifier
    editClass : object              # class reference for building edmEditField
    defaultValue: Any = None        # should be of the correct type for the field
    editKeywords : dict = field(default_factory=dict)
                                    # additional keywords to pass to editClass
    readonly : bool = False         # if True, don't allow modification
    hidden : bool = False           # if True, don't display, just record
    array : bool = False            # if True, then expect a list of values
    enumList : Any = None           # for edmEditEnum, must be type Enum
    group : list[object] = field(default_factory=list)
                                    # intended to contain edmField references.

@dataclass
class edmTag:
    '''
        edmTag
        values for the edm widget characteristics
            tag - .edl/json identifier
            value - value for this field - often left as a string to be converted as needed
            field - edmField reference for this widget and tag
            changed - internally used to indicate field has been edited.
    '''

    tag: str                        # index key
    value: Any                      # subset of [string, int, list, font, edmColor]
    field: object = None            # edmField for this tag
    changed: bool = False           # when a widget is edited, this indicates an update
