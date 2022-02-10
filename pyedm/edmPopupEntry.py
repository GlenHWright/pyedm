from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# create a popup window which allows data entry as either text entry (keyboard) or
# calculator entry (keyboard or mouse)
# Note that Popup fails if called directly: makeKeypad and makeButtons are methods
# defined by inheriting classes

from builtins import str
from PyQt5 import QtGui, Qt, QtCore
from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QButtonGroup, QPushButton, QLineEdit
from PyQt5.QtCore import QSize
import pyedm.edmFont as edmFont

class Popup(QWidget):
    '''Generic popup base class. Must be inherited by a class that defines makeKeypad and makeButtons'''
    buttonSize = QSize(20,18)
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | self.windowType())
        self.setAttribute(QtCore.Qt.WA_QuitOnClose, False)
        self.setFont(edmFont.getFont("helvetica-medium-r-10.0") )
        self.layout = QVBoxLayout()
        self.layout.setSpacing(2)
        self.textWidget = QLineEdit(self)
        self.keypad = self.makeKeypad()
        self.buttons = self.makeButtons()
        self.layout.addWidget(self.textWidget)
        if self.keypad != None:
            self.layout.addWidget(self.keypad)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)
        self.resize(self.minimumSize())
        QWidget.show(self)

    def show(self):
        self.textWidget.setText("")
        QWidget.show(self)

    def onCancel(self):
        if self.cancelCallback != None:
            self.cancelCallback()
        self.hide()

    def onAccept(self):
        self.acceptCallback(self.textWidget.text())
        self.hide()

class PopupNumeric(Popup):
    '''Popup window for numeric data entry'''
    keys = [ [ "7", "8", "9"], ["4", "5", "6"], [ "1", "2", "3" ], [ "0", ".", "+/-"] ]
    
    def __init__(self, acceptCallback, cancelCallback=None, value=None):
        super().__init__()
        if value != None:
            self.textWidget.setText( str(value))
        self.acceptCallback = acceptCallback
        self.cancelCallback = cancelCallback

    def makeKeypad(self):
        keypad = QWidget(self)
        layout = QGridLayout()
        self.group = QButtonGroup(self)
        #self.group.connect(self.group, SIGNAL("buttonClicked(int)"), self.onKeypad)
        self.group.buttonClicked.connect(self.onKeypad)
        for ri,rv in enumerate(self.keys):
            for ci, cv in enumerate(rv):
                b = QPushButton(cv)
                b.setMinimumSize(self.buttonSize)
                b.resize(self.buttonSize)
                layout.addWidget(b, ri, ci)
                self.group.addButton(b, ri*3+ci)
        keypad.setLayout(layout)
        return keypad

    def onKeypad(self, idx):
        if idx <= 11:
            ri = idx//3
            ci = idx%3
            self.textWidget.setText( self.textWidget.text() + self.keys[ri][ci])

    def makeButtons(self):
        buttons = QWidget(self)
        ok = QPushButton("OK")
        ok.setMinimumSize(self.buttonSize)
        ok.resize(self.buttonSize)
        bs = QPushButton("bs")
        bs.setMinimumSize(self.buttonSize)
        bs.resize(self.buttonSize)
        cancel = QPushButton("Cancel")
        cancel.setMinimumSize(QSize(40,18))
        cancel.resize(self.minimumSize())
        layout = QHBoxLayout()
        layout.addWidget(cancel)
        layout.addWidget(bs)
        layout.addWidget(ok)
        buttons.setLayout(layout)
        ok.connect(ok, SIGNAL("clicked(bool)"), self.onAccept)
        cancel.connect(cancel, SIGNAL("clicked(bool)"), self.onCancel)
        bs.connect(bs, SIGNAL("clicked(bool)"), self.backspace)

        return buttons

    def backspace(self):
        txt = self.textWidget.text()
        if len(txt) <= 0:
            return
        self.textWidget.setText(txt[:-1])
        
class PopupText(Popup):
    '''popup window for text data entry'''
    def __init__(self, acceptCallback, cancelCallback=None, value=None):
        super().__init__()
        if value != None:
            self.textWidget.setText(value)
        self.acceptCallback = acceptCallback
        self.cancelCallback = cancelCallback

    def makeKeypad(self):
        return None

    def makeButtons(self):
        buttons = QWidget(self)
        ok = QPushButton("OK")
        ok.setMinimumSize(self.buttonSize)
        ok.resize(self.buttonSize)
        accept = QPushButton("Accept")
        accept.setMinimumSize(QSize(40,18))
        accept.resize(self.minimumSize())
        cancel = QPushButton("Cancel")
        cancel.setMinimumSize(QSize(40,18))
        cancel.resize(self.minimumSize())
        layout = QHBoxLayout()
        layout.addWidget(ok)
        layout.addWidget(accept)
        layout.addWidget(cancel)
        buttons.setLayout(layout)
        ok.connect(ok, SIGNAL("clicked(bool)"), self.onAccept)
        cancel.connect(cancel, SIGNAL("clicked(bool)"), self.onCancel)
        accept.connect(accept, SIGNAL("clicked(bool)"), self.onSend)

        return buttons

    def onSend(self, value):
        self.acceptCallback(self.textWidget.text() )

if __name__ == "__main__":
    import sys

    def callback(arg):
        print("Accept:", arg)
        sys.exit(0)

    def cancel():
        print("Cancel")
        sys.exit(0)

    app = QtGui.QApplication(sys.argv)
    n = PopupNumeric(callback, cancelCallback=cancel)
    n.show()
    n.resize(n.minimumSize())
    print("Final size n:", n.geometry(), n.minimumSize())
    t = PopupText(callback, cancel)
    t.show()
    t.resize(t.minimumSize())
    print("Final size t:", t.geometry(), t.minimumSize())
    app.exec_()
