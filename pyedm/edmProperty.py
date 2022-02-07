#
# Copyright 2017 Canadian Light Source, Inc.
#
#

from builtins import object
class edmPropertyType(object):
    ''' generic class for managing the different types of edm widget properties.
        in a model/view environment, this is the model.
    '''
    def __init__(name=None, label=None, objectID=None, edit=None):
        self.name, self.label, self.objectID, self.edit = name, label, objectID, edit

class edmProperty(object):
    class Int(edmPropertyType):
         pass

    class Real(edmPropertyType):
         pass

    class String(edmPropertyType):
         pass

    class Enum(edmPropertyType):
         pass

    class Color(edmPropertyType):
         pass

    class Font(edmPropertyType):
         pass

    class TextBox(edmPropertyType):
         pass

