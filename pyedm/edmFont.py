# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: base
# This is a base-level module, and must not call any other pyedm modules
#
# Manage the font names used by EDM
#
# EDM uses a "family-weight-italic-pointsize" naming scheme
# convert this for use with QFontDatabase lookup

from PyQt5.QtGui import QFontDatabase,QFont,QFontInfo

mapPointSize = [ 0,  1,  2,  3,  4,  5,  6,  6,  7,  8,
                 8,  9,  9, 11, 11, 12, 13, 14, 15, 15,
                16, 17, 18, 19, 19, 20, 21, 22, 23, 24,
                25, 26, 27, 28, 29, 30, 30, 31, 32, 33 ]

# experimental - should be configurable by instance or site
# to improve font displays
mapFontName = {
        "helvetica" : "utopia",
        "courier"   : "courier-new",
        }

def GenericGetFont(fontName, rescale=1.0, squeeze=90.0):
    if type(fontName) == str:
        if fontName in edmFontTable:
            return edmFontTable[fontName]
        parts = fontName.split("-")
        if len(parts) < 4:
            raise ValueError(f"GenericGetFont bad font name {fontName}")
        fn = parts[0]
        '''
        if fn in mapFontName:
            fn = mapFontName[fn]
            '''
        weight = QFont.Normal if parts[1] == "medium" else QFont.Bold
        italic = (parts[2] != "r")
        pointsize = float(parts[3])
        try:
            pointsize = mapPointSize[int(pointsize)]
        except:
            pointsize = int(pointsize)
    elif type(fontName) == dict:
        fn = fontName["family"]
        weight = QFont.Normal if fontName["bold"] == False else QFont.Bold
        italic = fontName["italic"]
        pointsize = fontName["pointSize"]
        fontName = f"json:{fn}-{weight}-{italic}-{pointsize}"
        if fontName in edmFontTable:
            return edmFontTable[fontName]
    else:
        raise ValueError(f"GenericGetFont illegal fontName type {type(fontName)} must be dict or str")

    pointsize = int(pointsize*rescale)
    font = QFont(fn, pointsize, weight, italic)
    font.setStyleStrategy(QFont.PreferDevice+QFont.PreferMatch)
    # font.setWordSpacing(-1)
    if pointsize > 11:
        font.setLetterSpacing(QFont.PercentageSpacing, squeeze)

    fi = QFontInfo(font)
    print(f"request {fontName}, use {fi.family()} {fi.weight()} {fi.italic()} {fi.pointSize()}")

    edmFontTable[fontName] = font
    return font

def X11GetFont(fontName, rescale=1.0):
    ''' X11GetFont - unused -preference is for a consistent compatible lookup
    '''
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


def toHTML(font, text):
    if isinstance(font, QFont):
        family = font.family()
        pointsize = font.pointSize()
        bold = font.weight()
        italic = font.italic()
    elif type(font) == dict:
        family = fontName["family"]
        bold = int( fontName["bold"] )
        italic = fontName["italic"]
        pointsize = fontName["pointSize"]
    else:
        print(f"unable to determine {font} - return {text}")
        return text
    rval= f'<span style="font-size: {pointsize}px">{text}</span>'
    return rval


import os
#if os.name == "posix":
#    getFont = X11GetFont
#else:
#    getFont = GenericGetFont
    
getFont = GenericGetFont
edmFontTable = {}
