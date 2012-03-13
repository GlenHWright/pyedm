#
# Classes to manage EDM-style edit field for widgets
#

from PyQt4.QtGui import QWidget, QBoxLayout, QAbstractButton, QPushButton, QGridLayout, QLineEdit, QLabel, QCheckBox, QMenu, QFrame, QPainter, QTextEdit, QScrollArea, QFont, QListWidget
from PyQt4.QtCore import Qt, SIGNAL
from edmColors import colorTable, findColorRule
# from __future__ import print_function

class edmEditField:
    ''' base class for the edit fields. Derived classes
        handle generating a specific widget set to display,
    '''
    def __init__(self, label=None, object=None, setter=None, defValue=None, getter=None, **kw):
        ''' label is the displayed label on the edit screen
            object is the property or method within the class to retrieve the value
            getter is a method used when a simple reference is insufficient
            setter is the property or method within the class to save the value
        '''
        self.label = label
        self.objectID = object
        self.getter = getter
        self.setter = setter
        self.defValue = defValue

    def showEditWidget(self, widget, index=None):
        ''' returns the label to be applied to this field and
            a Qt widget that contains the correct fields
            with the values for this edm widget
        '''
        return self.label, QLabel("unimplemented")

    def getval(self, widget, index=None, **kw):
        defValue = kw.get("defValue", self.defValue)
        property = kw.get("object", self.objectID)
        if property == None:
            try:
                getter = kw.get("getter", self.getter)
                prop = getter(widget, index, defValue=defValue)
                return prop

            except:
                print "getval property fail", getter, index, defValue
                return defValue

        # parse a widget property: "a[.b[.c]]"
        try:
            if widget.DebugFlag > 0 : print "getval look for", property, index
            prop = widget
            items = property.split(".")
            for ps in items[:-1] :
                prop = getattr(prop, ps)
            prop = getattr(prop, items[-1], defValue)
            if callable(prop):
                prop = prop()
            if index != None:
                prop = prop[index]
            if widget.DebugFlag > 0 : print "getval return", prop
        except:
            #
            if widget.DebugFlag > 0: print "getval fail: prop, return", property, defValue
            return defValue
        return prop

    def getSval(self, widget, **kw):
        return str(self.getval(widget, **kw))

    def getIval(self, widget, **kw):
        val = self.getval(widget, **kw)
        if val != None:
            val = int(val)
        return val

    def setval(self, widget, value, index=None):
        pass


    def setObject(self):
        ''' at the end of the edit, save the values
        '''
        pass

def __makeMenuButton__(name, items):
    button = QPushButton(name)
    menu = QMenu()
    button.setMenu(menu)
    for label in items: menu.addAction(label)
    return button, menu

class edmEdit:
    '''container for related class instances
    '''
    class String(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getSval(widget, index=index)
            text = QLineEdit( val )
            return self.label, text

    class Int(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getIval(widget, index=index)
            if val == None:
                val = ""
            else:
                val = str(val)
            text = QLineEdit( val )
            return self.label, text

    class Enum(edmEditField):
        def __init__(self, **kw):
            edmEditField.__init__(self, **kw)
            self.enumList = kw.get("enumList", [])
            
        def showEditWidget(self, widget, index=None):
            val = self.getSval(widget, index=index, defValue=self.enumList[0])
            # widget.object.getStringProperty(self.objectID, self.enumList[0])
            button, menu = __makeMenuButton__(val, self.enumList)
            button.edmTrigger = lambda action: button.setText(action.text())
            menu.connect(menu,SIGNAL("triggered(QAction*)"), button.edmTrigger)
            return self.label, button

    class LineThick(Enum):
        def __init__(self, label="Line Thk", object="lineWidth", **kw):
            edmEdit.Enum.__init__(self, label=label, object=object, enumList=[str(x) for x in range(0,11)], **kw)

    class CheckButton(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getIval(widget, index=index)
            cb = QCheckBox( self.label)
            if val:
                cb.setCheckState(1)
            return "", cb

    class Color(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getSval(widget, index=index)
            self.colorRect = colorRectangle(val, self.clickedGridCallback)
            self.button = QPushButton(val)
            self.button.connect(self.button, SIGNAL("clicked()"), self.clickedListCallback)
            layout = QBoxLayout(QBoxLayout.LeftToRight)
            layout.addWidget(self.colorRect)
            layout.addWidget(self.button)
            newwidget = QWidget()
            newwidget.setLayout(layout)
            return self.label, newwidget

        def clickedGridCallback(self, ignore=None):
            ColorGrid.getColorTable(callback=self.colorSelect)

        def clickedListCallback(self, ignore=None):
            ColorList.getColorList(callback=self.colorSelect)

        def colorSelect(self, newColor):
            ''' called when the color grid or list has a new color selected'''
            self.colorRect.recolor(newColor)
            self.button.setText(newColor)

    class FgColor(Color):
        def __init__(self, label="FG Color", object="fgColorInfo.getName", defValue="black-14", **kw):
            edmEdit.Color.__init__(self, label=label, object=object, defValue=defValue, **kw)
        
    class BgColor(Color):
        def __init__(self, label="BG Color", object="bgColorInfo.getName", defValue="Disconn/Invalid", **kw):
            edmEdit.Color.__init__(self, label=label, object=object, defValue=defValue, **kw)
        
    class StringPV(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getSval(widget, defValue="")
            text = QLineEdit( val )
            return self.label, text

    class Real(edmEditField):
        pass

    class TextBox(edmEditField):
        def showEditWidget(self, widget, index=None):
            val = self.getval(widget, defValue="")
            try:
                val = '\n'.join(val)
            except:
                pass
            newwidget = QTextEdit()
            newwidget.setPlainText(val)
            return self.label, newwidget

    class SubScreen(edmEditField):
        def __init__(self, label=None, buildEntry=None, count=1, **kw):
            edmEditField.__init__(self, label, **kw)
            self.buildEntry = buildEntry
            self.count = count

        def showEditWidget(self, widget, index=None):
            self.subWindow = buildSubWindow(widget, self.buildEntry, self.count)
            self.subWindow.hide()
            button = QPushButton("...")
            button.connect(button, SIGNAL("clicked()"), lambda: self.subWindow.show() )
            return self.label, button

    class Font(edmEditField):
        convAlign = { "left":"L", "0":"L", 0:"L", "None": "L",
                        "center": "C", "1":"C", 1:"C",
                        "right": "R", "2":"R", 2:"R" }
        def __init__(self, label="Font", object="font", **kw):
            edmEditField.__init__(self, label=label, object=object, **kw)

        def showEditWidget(self, widget, index=None):
            font = self.getval(widget)
            layout = QGridLayout()
            button, menu = __makeMenuButton__(font.family(), [ "utopia", "courier", "helvetica", "new century schoolbook", "times" ] )
            layout.addWidget(button, 0, 0, 1, 4)
            button, menu = __makeMenuButton__( str(font.pointSizeF()), [ "8.0", "10.0", "12.0", "14.0", "18.0", "72.0" ] )
            layout.addWidget(button, 1, 0)
            checkbox = QCheckBox( "B")
            checkbox.setCheckState( font.weight() == QFont.Bold)
            layout.addWidget( checkbox , 1, 1)
            checkbox = QCheckBox( "I")
            checkbox.setCheckState( font.italic())
            layout.addWidget( checkbox , 1, 2)
            # the top-level widget that contains the font contains the alignment in a different property.
            #
            # WOW DOES THIS VERSION OF PYQT4 SEEM FUBAR!
            # The "alignment" set for text is only returned as a class that doesn't have any way to decode what
            # the alignment is except for possibly creating new alignment objects of each type and doing
            # a comparison. Ouch.
            button, menu = __makeMenuButton__(edmEdit.Font.convAlign[widget.align], [ "L", "C", "R"] )
            layout.addWidget(button, 1, 3)
            newwidget = QWidget()
            newwidget.setLayout(layout)
            return self.label, newwidget

    class Filename(edmEditField):
        pass

    class StripchartCurve(edmEditField):
        pass

    class SymbolItem(edmEditField):
        pass

    class SymbolItemSelect(edmEditField):
        pass

    visibleList = [
        StringPV("Visibility PV", object="visPV.getTrueName"),
        Enum( object="visInvert", enumList=[ "Not Visible if", "Visible if" ] ),
        Int(">=", "visMin"),
        Int("and <", "visMax")
        ]

#
#
#

#
# Class to display a window containing the editable fields of an edm widget.
#
#
class edmEditWidget(QWidget):
    def __init__(self, widget):
        QWidget.__init__(self)
        grid = QGridLayout()
        row = 0
        for oneprop in widget.edmEditPre + widget.edmEditList + widget.edmEditPost:
            #try:
                name, subwidget = oneprop.showEditWidget(widget)
                grid.addWidget( QLabel(name), row, 0)
                grid.addWidget( subwidget, row, 1)
                row += 1
            #except:
                #print "unable to add edit element", oneprop

        buttons = QBoxLayout(QBoxLayout.LeftToRight)
        buttons.addWidget( MakeButton("Apply", self.onApply) )
        buttons.addWidget( MakeButton("Save", self.onDone) )
        buttons.addWidget( MakeButton("Cancel", self.onCancel)  )
        grid.addLayout(buttons, row, 0, 1, 2)
        self.setLayout(grid)

    def onApply(self):
        pass

    def onDone(self):
        self.close()

    def onCancel(self):
        self.close()

class buildSubWindow(QScrollArea):
    '''builds a window callable from an edit widget window. "entry" is the prototype for
        building a single entry from multiple widgets, and "count" is the number of elements
        of "entry" to build.
        '''
    def __init__(self, widget, entry, count):
        QScrollArea.__init__(self)
        self.scrollable = QWidget()
        grid = QGridLayout()
        row = 0
        for num in range(0,count):  # build a set of widgets for each repeated entry
            for calls in entry:     # for each row of a single entry
                col = 0
                for single in calls:
                    builder = single()
                    label, w = builder.showEditWidget(widget, index=num)
                    grid.addWidget(QLabel(label), row, col)
                    grid.addWidget(w, row, col+1)
                    col = col + 2
                row = row+1
        self.scrollable.setLayout(grid)
        self.setWidget(self.scrollable)

def MakeButton(label, callback):
    button = QPushButton(label)
    button.connect(button, SIGNAL("clicked()"), callback)
    return button


class colorRectangle(QAbstractButton):
    def __init__(self, colorName, callback=None):
        QAbstractButton.__init__(self)
        self.setGeometry(0,0, 20, 20)
        self.setMinimumSize(25,25)

        self.color = findColorRule(colorName)
        self.callback = callback
        self.connect(self, SIGNAL("clicked()"), self.onClicked)

    def recolor(self, colorName):
        self.color = findColorRule(str(colorName) )

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.fillRect(0,0,20,20, self.color.getColor() )

    def onClicked(self):
        self.callback(self.color.getName() )

class ColorList:
    myColorList = None
    myCallback = None
    def __init__(self):
        pass

    @classmethod
    def getColorList(cls, callback=None):
        cls.myCallback = callback
        if cls.myColorList == None:
            cl = QListWidget()
            cls.myColorList = cl
            for color in colorTable.colorIndex:
                if color != None:
                    cl.addItem(color)
            cls.myColorList.connect(cls.myColorList, SIGNAL("itemActivated(QListWidgetItem*)"), cls.onAction)
        cls.myColorList.show()

    @classmethod
    def onAction(cls, item):
        try: cls.myCallback(item.text())
        except: pass
        cls.myColorList.hide()
        
class ColorGrid:
    myColorTable = None
    myCallback = None
    def __init__(self):
        pass

    @classmethod
    def getColorTable(cls, callback=None):
        cls.myCallback = callback
        if cls.myColorTable == None:
            cg = QWidget()
            cls.myColorTable = cg
            grid = QGridLayout()
            grid.setSpacing(0)
            for num, color in enumerate(colorTable.colorIndex):
                if color != None:
                    grid.addWidget( colorRectangle(color, cls.onNewColor), int(num/5), int(num%5) )
            cg.setLayout(grid)

        cls.myColorTable.show()


    @classmethod
    def onNewColor(cls, newColor):
        try: cls.myCallback(newColor)
        except: pass
        cls.myColorTable.hide()
