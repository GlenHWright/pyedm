# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Manage the font names used by EDM
#
# EDM uses a "family-weight-italic-pointsize" naming scheme
# convert this for use with QFontDatabase lookup

from builtins import str
from PyQt5.QtGui import QFontDatabase,QFont,QFontInfo
#from PyQt5.QtCore import str

mapPointSize = [ 0,  1,  2,  3,  4,  5,  6,  6,  7,  8,
                 8,  9,  9, 11, 11, 12, 13, 14, 15, 15,
                16, 17, 18, 19, 19, 20, 21, 22, 23, 24,
                25, 26, 27, 28, 29, 30, 30, 31, 32, 33 ]
def GenericGetFont(fontName):
    global mapPointSize
    if fontName in edmFontTable:
        return edmFontTable[fontName]
    parts = fontName.split("-")
    fn = parts[0]
    if fn == "courier":
        fn = "courier-new"
    weight = QFont.Normal if parts[1] == "medium" else QFont.Bold
    italic = (parts[2] != "r")
    pointsize = float(parts[3])
    try:
        pointsize = mapPointSize[int(pointsize)]
    except:
        pointsize = int(pointsize)
    font = QFont(fn, pointsize, weight, italic)
    font.setStyleStrategy(QFont.PreferDevice+QFont.PreferMatch)
    # font.setWordSpacing(-1)
    if pointsize > 11:
        font.setLetterSpacing(QFont.PercentageSpacing, 90.0)

    fi = QFontInfo(font)
    print(f"request {fontName}, use {fi.family()} {fi.pointSize()} {fi.weight()} {fi.bold()}")

    edmFontTable[fontName] = font
    return font

def X11GetFont(fontName):
    if fontName in edmFontTable:
        return edmFontTable[fontName]
    parts = fontName.split("-")
    height = parts[3].split(".")
    height = height[0]
    rawName = str("-*-%1-%2-%3-*-*-%4-*-*-*-*-*-iso8859-*").arg(parts[0], parts[1], parts[2], height )
    font = QFont()
    font.setRawName(rawName)
    edmFontTable[fontName] = font
    return font

import os
if os.name == "posix":
    getFont = X11GetFont
else:
    getFont = GenericGetFont
    
getFont = GenericGetFont
edmFontTable = {}
