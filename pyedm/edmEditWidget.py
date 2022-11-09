# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Classes to manage EDM-style edit field for widgets
#
# MODULE LEVEL: low
# This is a low-level module, and must only call base level pyedm modules
#

from typing import Any
from dataclasses import dataclass
from enum import Enum

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFontDatabase,QFont,QFontInfo,QPalette

from .edmField import edmField, edmTag
from .edmApp import redisplay, edmApp
from .edmColors import edmColor


fontAlignEnum = Enum("align", "left center right", start=0)

class ColorWindow(QtWidgets.QWidget):
    '''
        draw a window with a grid of colors,
        Different from edm, this is a pop-up window at
        the point of button push, and disappears when
        used or  focus is lost (?)
    '''
    def __init__(self,*args, callback=None, **kw):
        super().__init__(*args, **kw)

        self.callback = callback
        layout = QtWidgets.QGridLayout()
        ncol = 5
        self.group = QtWidgets.QButtonGroup(self)
        for idx,cr in enumerate(edmColor.colorNames.values()):
            row, col = divmod(idx, ncol)
            color = QColorButton(mycolor=cr)
            self.group.addButton(color)
            layout.addWidget(color, row, col)
        self.setLayout(layout)
        self.group.buttonClicked.connect(self.notify)

    def notify(self, colorButton):
        print(f"ColorWindow notify {colorButton} color {colorButton.buttonColor}")
        self.callback(colorButton.buttonColor)



# a simple widget that adds a label to anything.
class edmTagWidget:
    def __init__(self, label, valueWidget):
        super().__init__()
        self.label = label
        self.valueWidget = valueWidget

    def build(self):
        '''
        construct a widget with a label and a widget
        '''
        if self.label == None:
            return self.valueWidget
        self.widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        labelwidget = QtWidgets.QLabel(self.label)
        labelwidget.setContentsMargins(0,0,10,0)
        layout.addWidget(labelwidget)
        layout.setAlignment(labelwidget, Qt.AlignRight)
        layout.addWidget(self.valueWidget)
        layout.setSpacing(1)
        layout.setContentsMargins( 1, 4, 1, 4)
        self.widget.setLayout(layout)
        size = self.widget.sizeHint()
        self.widget.setFixedHeight(size.height())
        return self.widget

    def nolabel(self):
        return self.valueWidget

# a class for displaying an unlabeled color box
#
class QColorButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, mycolor=None):
        super().__init__(parent)
        self.buttonColor = mycolor
        self.setFlat(True)
        self.newColor(mycolor)

    def newColor(self, newcolor):
        self.buttonColor = newcolor
        color = newcolor.getColor()
        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        palette.setColor(QPalette.Window, color)
        palette.setColor(QPalette.WindowText, color)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

class edmEditField(QObject):
    ''' base class for the edit fields. Derived classes
        handle generating a specific widget set to display,
    '''
    newValue = pyqtSignal(str, 'PyQt_PyObject')
    def __init__(self, label, edmfield, widget):
        ''' label is the displayed label on the edit screen
            field is the field in the defined class to be edited.
        '''
        super().__init__()
        self.label = label
        self.edmfield = edmfield
        self.widget = widget

    def showEditWidget(self, displayValue):
        ''' return a Qt widget that contains
            a label and a widget as returned from buildOneEditWidget.
            the correct fields with the values for this edm widget.
            Inheriting classes can over-ride buildOneEditWidget to
            use the label or over-ride showEditWidget to display
            the label in a different manner.
        '''
        editWidget = self.buildOneEditWidget(displayValue)
        return edmTagWidget(self.label, editWidget)

    def buildOneEditWidget(self, displayValue):
        lineedit = QtWidgets.QLineEdit(str(displayValue))
        lineedit.editingFinished.connect( lambda widget=lineedit: self.onNewValue(widget) )
        return lineedit

    def onNewValue(self, widget):
        print(f"onNewValue({self}, {widget})")
        self.onValueUpdate(widget.text())

    def onValueUpdate(self, newValue):
        self.newValue.emit(self.edmfield.tag, newValue)

class edmEditInt(edmEditField):
    '''
        widget to edit an integer field
    '''
    def buildOneEditWidget(self, displayValue):
        if displayValue == None:
            displayValue = ""
        intedit = edmEditField.buildOneEditWidget(self, displayValue)
        # TO DO - add validity checking on input
        return intedit

class edmEditClass(edmEditField):
    '''
        displays the class name as a read-only title.
    '''
    def showEditWidget(self, displayValue):
        return edmTagWidget(None, QtWidgets.QLabel(displayValue))

class edmEditString(edmEditField):
    '''
        widget to edit a string field.
        this currently is no different than the base class.
    '''
    def buildOneEditWidget(self, displayValue):
        if displayValue == None:
            displayValue = ""
        return edmEditField.buildOneEditWidget(self, displayValue)

class edmEditEnum(edmEditField):
    ''' edmEditEnum
        make a button with a menu of all choices. If there's a potentially large list (e.g. fonts)
        recommend finding a smarter way.
    '''
    def buildOneEditWidget(self, value):
        ''' expectation is that value will be of type Enum'''
        menu = QtWidgets.QMenu()
        for item in self.edmfield.enumList:
            action = menu.addAction(item.name, lambda select=item,notify=self: self.onNewValue(select))
        self.button = QtWidgets.QPushButton()
        self.setLabel(value)
        self.button.setMenu(menu)
        return self.button

    def setLabel(self, value):
        try:
            value = value.name
        except AttributeError:
            value = ""
        self.button.setText(f"{value}")

    def onNewValue(self, value):
        print(f"edmEditEnum: value {value}")
        self.setLabel(value)
        self.onValueUpdate(value)

class edmEditCheckButton(edmEditField):
    def buildOneEditWidget(self, displayValue):
        checkbox = QtWidgets.QCheckBox()
        checkbox.setChecked( displayValue in ["1", "True", True, 1 ])
        checkbox.stateChanged.connect(lambda state,widget=checkbox: self.onNewValue(widget, state))
        return checkbox

    def onNewValue(self, widget, state):
        self.newValue.emit(self.edmfield.tag, state!=0)

class edmEditBool(edmEditCheckButton):
    pass

class edmEditColor(edmEditField):
    '''
        edmEditColor - change the color rule being used
        display a clickable color button, and the text description of the color rule
    '''
    def buildOneEditWidget(self, displayValue):
        self.colorScreen = None
        try:
            name = displayValue.name
            numeric = displayValue.numeric
        except AttributeError as exc:
            print(f"edmEditColor not displaying color rule {displayValue}")
            name = "Not Found"
            numeric = -1

        self.button = QColorButton(mycolor=displayValue)
        self.name = QtWidgets.QLabel(name)
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        layout.setSpacing(0)
        layout.setContentsMargins(0,4,0,4)
        fm = self.name.fontMetrics()
        self.button.setFixedWidth(fm.height())
        layout.addWidget(self.button)
        layout.addWidget(self.name)
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(layout)
        self.button.clicked.connect(self.showColorScreen)
        return self.widget

    def showColorScreen(self):
        if self.colorScreen:
            self.colorScreen.show()
            return
        self.colorScreen = ColorWindow(callback=self.onNewValue)
        self.colorScreen.show()

    def onNewValue(self, colorRule):
        self.colorScreen = None
        self.button.newColor(colorRule)
        self.onValueUpdate(colorRule)

class edmEditPV(edmEditString):
    pass

class edmEditReal(edmEditField):
    ''' edmEditReal - returns a widget for editing a floating point number
    '''
    def builddOneEditWidget(self, displayValue):
        if displayValue == None:
            displayValue = ""
        floatedit = edmEditField.buildOneEditWidget(self, displayValue)
        # TO DO - add validity checking on input string
        return floatedit
    pass

class edmEditTextBox(edmEditField):
    pass

#
# Unusual entry - build a button that activates a sub-screen. The sub-screen is built
# using "group" attribute of edmEditField, which lists the fields to be displayed.
# Best use is to inherit this for a custom screen for the widget being edited.
class edmEditSubScreen(edmEditField):
    def showEditWidget(self, *unused, buttonLabel=None):
        self.subwindow = None
        self.arraysize = 1
        if buttonLabel is None:
            buttonLabel = self.label
        button = QtWidgets.QPushButton(buttonLabel)
        button.clicked.connect(self.buildSubWindow)
        return edmTagWidget(None, button)

    def buildSubWindow(self, *args, **kw):
        print(f"buildSubWindow {self} arraysize {self.arraysize} {args} {kw}")
        self.editlist = []
        if self.subwindow:
            self.subwindow.show()
            return

        layout = self.buildLayout()

        self.subwindow = QtWidgets.QWidget()
        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setLayout(layout)
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(scrollWidget)

        # build the top level of scroll area and buttons.
        topLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        topLayout.addWidget(scrollArea)

        buttons = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        buttons.addWidget( MakeButton("Apply", self.onApply) )
        buttons.addWidget( MakeButton("Save", self.onDone) )
        buttons.addWidget( MakeButton("Cancel", self.onCancel)  )

        buttonWidget = QtWidgets.QWidget()
        buttonWidget.setLayout(buttons)

        topLayout.addWidget(buttonWidget)

        self.subwindow.setLayout(topLayout)
        self.subwindow.show()

    def buildLayout(self):
        return buildVerticalLayout( self, self.widget, self.edmfield.group, self.onNewValue)

    def onNewValue(self, tag, value):
        print(f"buildSubWindow.onNewValue({tag} {value})")
        self.newValue.emit(tag, value)

    def onApply(self):
        pass

    def onDone(self):
        self.subwindow.hide()
        self.subwindow = None

    def onCancel(self):
        self.subwindow.hide()
        self.subwindow = None


class edmEditFontInfo(edmEditField):
    '''
        display a drop-down menu for the font family,
        a drop-down menu for the allowed point sizes,
        a check box for bold, and a check box for italic.
    '''
    def buildOneEditWidget(self, displayValue):
        font = displayValue
        self.font = font
        self.fontInfo = QFontInfo(font)
        print(f"buildOneEditWidget {font}, use {self.fontInfo.family()} {self.fontInfo.pointSize()} {self.fontInfo.weight()} {self.fontInfo.bold()}")
        self.fontDB = QFontDatabase()
        self.family = QtWidgets.QComboBox()
        self.family.addItems(self.fontDB.families())
        toplayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        self.pointsize = QtWidgets.QComboBox()
        self.bold = QtWidgets.QCheckBox("B")
        self.italic = QtWidgets.QCheckBox("I")
        layout.addWidget(self.pointsize)
        layout.addWidget(self.bold)
        layout.addWidget(self.italic)
        margin = layout.contentsMargins()
        margin.setTop(margin.top()//3)
        margin.setBottom(margin.bottom()//3)
        layout.setContentsMargins(margin)
        toplayout.addWidget(self.family)
        toplayout.addLayout(layout)
        toplayout.setContentsMargins(0, 0, 0, 0)
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(toplayout)
        self.saveInfo = { "family": self.fontInfo.family(), "pointSize": self.fontInfo.pointSize(),
                "bold":self.fontInfo.bold(), "italic":self.fontInfo.italic() }
        self.changeFamily()
        # Add connect AFTER setting values
        self.bold.clicked.connect( lambda newstate: self.onNewValue(bold=newstate))
        self.italic.clicked.connect( lambda newstate: self.onNewValue(italic=newstate))
        self.pointsize.currentTextChanged.connect(lambda newPS: self.onNewValue(pointSize=newPS))
        self.family.currentTextChanged.connect( lambda newFamily: self.onNewValue( family=newFamily))

        return self.widget

    def changeFamily(self):
        def safeInt(x):
            try: v = int(x)
            except: v = 0
            return v
        self.busy = True
        self.family.setCurrentText(self.saveInfo["family"])
        self.font = QFont(  self.saveInfo["family"],
                            safeInt(self.saveInfo["pointSize"]),
                            self.saveInfo["bold"],
                            self.saveInfo["italic"])
        self.fontInfo = QFontInfo(self.font)
        style = self.fontDB.styleString(self.fontInfo)
        ps = self.fontDB.pointSizes(self.saveInfo["family"], style)
        while self.pointsize.count() > 0:
            self.pointsize.removeItem(0)
        for point in ps:
            self.pointsize.addItem(str(point))
        self.changePointSize(self.fontInfo.pointSize())
        self.bold.setChecked( self.fontInfo.bold())
        self.italic.setChecked( self.fontInfo.italic())
        self.busy = False

    def changePointSize(self, pointSize):
        ps = self.fontDB.pointSizes(self.family.currentText(), self.fontDB.styleString(self.fontInfo))
        if pointSize not in ps:
            pointSize = min(ps, key=lambda val: abs(val - pointSize))
        self.pointsize.setCurrentText(str(pointSize))

    def onNewValue(self, **kw):
        if self.busy: return
        changed = False
        for w in kw:
            if kw[w] != self.saveInfo[w]:
                changed = True
        if not changed:
            return
        self.saveInfo.update(kw)
        self.changeFamily()
        self.onValueUpdate(self.font)

class edmEditFontAlign(edmEditEnum):
    pass

class edmEditFilename(edmEditField):
    pass

class edmEditStripchartCurve(edmEditField):
    pass

class edmEditSymbolItem(edmEditField):
    pass

class edmEditSymbolItemSelect(edmEditField):
    pass

# special class: ignore the displayValue, and build a horizontal layout widget
# containing the other widgets.

class edmEditHList(edmEditField):

    def showEditWidget(self, *unused):
        return edmTagWidget(None, self.buildOneEditWidget())

    def buildOneEditWidget(self, *unused):
        self.editlist = []
        layout = buildHorizontalLayout( self, self.widget, self.edmfield.group, self.onNewValue)
        layout.setSpacing(15)
        margin = layout.contentsMargins()
        margin.setTop(margin.top()//2)
        margin.setBottom(margin.bottom()//2)
        layout.setContentsMargins(margin)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def onNewValue(self, tag, value):
        self.newValue.emit(tag, value)

    def edmCleanup(self):
        '''
            called when planning to delete an object, and need to
            undo the __init__ and buildOneEditWidget
        '''
        self.editlist = None

class edmEdit:
    # class for simplifying importing this module
    Class = edmEditClass
    Int = edmEditInt
    String = edmEditString
    Enum = edmEditEnum
    CheckButton = edmEditCheckButton
    Bool = edmEditBool
    Color = edmEditColor
    PV = edmEditPV
    Real = edmEditReal
    TextBox = edmEditTextBox
    SubScreen = edmEditSubScreen
    FontInfo = edmEditFontInfo
    FontAlign = edmEditFontAlign
    Filename = edmEditFilename
    HList = edmEditHList

#
# Class to display a window containing the editable fields of an edm widget.
# Objective:
# Parent widget.
#   part 1: Scrollable area
#       list of widgets built by the edmField entries for the widget, as
#       returned by getEditPropertiesList()
#       There is support here for tagval/tagtype lists being returned for
#       widgets not yet updated to current code, but they will only be able
#       to edit the fields that were loaded from the .edl file.
#   part 2: Cancel/Apply/OK buttons
#
#
class edmShowEdit(QtWidgets.QWidget):
    def __init__(self, widget, parent):
        super().__init__()
        print(f"editing {widget} in {parent}")
        self.editWidget = widget
        self.parentWindow = parent
        self.scrollWidget = QtWidgets.QWidget()
        self.editlist = []
        props = widget.getEditPropertiesList()
        # Set the layout for the scrolling area
        layout = buildVerticalLayout(self, self.editWidget, props, self.onNewValue)
        self.scrollWidget.setLayout(layout)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidget(self.scrollWidget)
        # build the top level of scroll area and buttons.
        topLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        topLayout.addWidget(self.scrollArea)
        buttons = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        buttons.addWidget( MakeButton("Apply", self.onApply) )
        buttons.addWidget( MakeButton("Save", self.onDone) )
        buttons.addWidget( MakeButton("Cancel", self.onCancel)  )
        buttonWidget = QtWidgets.QWidget()
        buttonWidget.setLayout(buttons)
        topLayout.addWidget(buttonWidget)
        self.setLayout(topLayout)

        self.tags = {}
        self.show()

    def setTagValue(self):
        self.editWidget.updateTags(self.tags)

    def onNewValue(self, key, value):
        if edmApp.debug(0) : print(f"Saving {value} to {key}")
        self.tags[key] = edmTag(key, value)

    def onApply(self):
        self.setTagValue()

    def onDone(self):
        self.setTagValue()
        self.parentWindow.edmHideEdit(self.editWidget)
        self.parentWindow = None
        self.editWidget = None
        self.destroy()

    def onCancel(self):
        self.parentWindow.edmHideEdit(self.editWidget)
        self.parentWindow = None
        self.editWidget = None
        self.destroy()

    def closeEvent(self, event):
        self.onCancel()
        event.accept()

def MakeButton(label, callback):
    button = QtWidgets.QPushButton(label)
    button.released.connect(callback)
    return button

class edmRubberband(QtWidgets.QRubberBand):
    '''
        edmRubberband = manage a widget overlay that allows moving and resizing.
    '''
    def __init__(self, *args, widget, **kw):
        super().__init__(QtWidgets.QRubberBand.Rectangle, widget.edmParent, *args, **kw)
        self.active(widget)

    def edmCleanup(self):
        self.edmWidget = None
        self.destroy()

    def active(self, widget=None):
        print(f"edmRubberband.active({self},{widget}")
        self.movemode = False       # True - moving, False - resizing
        self.edges = 0              # bits 0x01 left, 0x02 top, 0x04 right, 0x08 bottom
        if widget == None:
            return self.edmWidget != None
        self.setGeometry(widget.geometry())
        self.edmWidget = widget
        self.show()
        return True

    def inactive(self):
        print(f"edmRubberband.inactive({self},{self.edmWidget}")
        if self.edmWidget:
            geom = self.geometry()
            self.edmWidget.updateTags( {
                "x" : edmTag("x", geom.x()),
                "y" : edmTag("y", geom.y()),
                "w" : edmTag("w", geom.width()),
                "h" : edmTag("h", geom.height()),
                } )
            self.edmWidget = None
        self.hide()
    
    def mousePressEvent(self, event):
        print(f"edmRubberband.mousePress {self}")
        if not self.geometry().contains(event.pos()):
            print(f"event pos{event.pos()} pos {self.geometry()}")
            self.inactive()
            return False
        # decide if we're in a corner(resize) or not (move)
        width = self.width()
        height = self.height()
        self.location = event.pos()
        self.startat = self.geometry()
        where = self.location - self.startat.topLeft()
        self.movemode = (where.x() > width/5 and where.x() < width*4/5) or \
                    (where.y() > height/5 and where.y() < height*4/5)

        self.edges = 0
        if not self.movemode:
            if where.x() <= width/5:
                self.edges = self.edges | 1
            else:
                self.edges = self.edges | 4
            if where.y() <= height/5:
                self.edges = self.edges | 2
            else:
                self.edges = self.edges | 8
        
        return True

    def mouseMoveEvent(self, event):
        print(f"mouseMove({self} {event}")
        pos = event.pos() - self.location
        if self.movemode:
            self.move(self.startat.topLeft() + pos)
        else:
            newgeom = self.geometry()
            if self.edges & 1:
                newgeom.setX(self.startat.x() + pos.x())
                newgeom.setWidth(self.startat.width() - pos.x())
            if self.edges & 2:
                newgeom.setY(self.startat.y() + pos.y())
                newgeom.setHeight(self.startat.height() - pos.y())
            if self.edges & 4:
                newgeom.setWidth(self.startat.width() + pos.x())
            if self.edges & 8:
                newgeom.setHeight(self.startat.height() + pos.y())
            self.setGeometry(newgeom)

        
    def mouseReleaseEvent(self, event):
        print(f"mouseReleaseEvent {self} {event} {self.edmWidget}")
        if self.edmWidget == None:
            return
        geom = self.geometry()
        self.edmWidget.setGeometry(geom)

'''
General support for layout of widgets
'''
def buildVerticalLayout(displayWidget, editWidget, proplist, callback):
    return buildLayout(displayWidget, editWidget, proplist, callback, direction=QtWidgets.QBoxLayout.TopToBottom)

def buildHorizontalLayout(displayWidget, editWidget, proplist, callback):
    return buildLayout(displayWidget, editWidget, proplist, callback, direction=QtWidgets.QBoxLayout.LeftToRight)

def buildLayout(displayWidget, editWidget, proplist, callback, direction):
        layout = QtWidgets.QBoxLayout(direction)

        layout.setSpacing(1)
        # build the list of widgets for the layout area
        if isinstance(proplist[0], edmField):
            for oneprop in proplist:
                if oneprop.hidden is True or oneprop.array:
                    continue
                if oneprop.tag != "":
                    tagval = editWidget.getProperty(oneprop.tag)
                else:
                    tagval = ""
                tagw = oneprop.editClass(oneprop.tag, oneprop, editWidget, **oneprop.editKeywords)
                w = tagw.showEditWidget(tagval).build()
                layout.addWidget( w )
                displayWidget.editlist.append(tagw)
                tagw.newValue.connect(callback)
        else:
            tagval, tagtype = proplist
            fakeProp = edmField("", "", "")
            for tagkey, val in tagval.items():
                fakeProp.tag = tagkey
                tagw = edmEditField(tagkey, fakeProp, editWidget)
                w = tagw.showEditWidget(val).build()
                layout.addWidget( w)
                displayWidget.editlist.append(tagw)
                tagw.newValue.connect(callback)
        return layout
