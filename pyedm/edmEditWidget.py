from __future__ import print_function
from __future__ import absolute_import
#
# Classes to manage EDM-style edit field for widgets
#

from PyQt5 import QtWidgets
# from . import edmWidget

class edmEditField:
    ''' base class for the edit fields. Derived classes
        handle generating a specific widget set to display,
    '''
    def __init__(self, label=None, objectDesc=None, field=None):
        ''' label is the displayed label on the edit screen
            objectDesc is the keyword indexed in edmObject
            field is the field in the defined class to be edited.
        '''
        self.label = label
        self.objectDesc = objectDesc
        self.field = field

    def showEditWidget(self):
        ''' return a Qt widget that contains the correct fields
            with the values for this edm widget
        '''
        return QWidget()

    def setObject(self):
        ''' at the end of the edit, save the values
        '''
        pass


class edmEditInt(edmEditField):
    pass

class edmEditEnum(edmEditField):
    pass

class edmEditCheckButton(edmEditField):
    pass

class edmEditColor(edmEditField):
    pass

class edmEditStringPV(edmEditField):
    pass

class edmEditReal(edmEditField):
    pass

class edmEditTextBox(edmEditField):
    pass

class edmEditSubScreen(edmEditField):
    pass

class edmEditFontInfo(edmEditField):
    pass

class edmEditFilename(edmEditField):
    pass

class edmEditStripchartCurve(edmEditField):
    pass

class edmEditSymbolItem(edmEditField):
    pass

class edmEditSymbolItemSelect(edmEditField):
    pass

#
#
#

#
# Class to display a window containing the editable fields of an edm widget.
#
#
class edmShowEdit(QtWidgets.QWidget):
    def __init__(self, widget):
        super().__init__()
        props = widget.getEditPropertiesList()
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom, parent=self)
        for oneprop in props:
            try:
                layout.addWidget( oneprop.showEditWidget() )
            except:
                print("unable to add edit element", oneprop)

        buttons = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        buttons.addWidget( MakeButton("Apply", self.onApply) )
        buttons.addWidget( MakeButton("Save", self.onDone) )
        buttons.addWidget( MakeButton("Cancel", self.onCancel)  )

    def onApply(self):
        self.setObject()

    def onDone(self):
        self.setObject()
        self.destroy()

    def onCancel(self):
        pass


def MakeButton(label, callback):
    button = QtWidgets.QPushButton(label)
    #button.connect(button, SIGNAL("released()"), callback)
    button.released.connect(callback)
    return button
