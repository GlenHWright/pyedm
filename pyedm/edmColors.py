# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
# Support reading of an edm Colors file for defining widget colors.
# provides colorRule which will contain and interpret a color rule.
#
# MODULE LEVEL: base
# This is a base-level file for importing, it must not include any other pyedm modules either directly or indirectly
#
# Recommended way to use this file:
# from edmColors import findColorRule, colorRule
# widget.someColor = findColorRule(my_Name_Or_Index)
# something_that_needs_a_QColor( widget.someColor.getColor( ColorPV value, default Color))

from os import getenv
import re
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# define one part of a rule
class oneRule:
    NO_OP, LT, LE, GT, GE, EQ, NE, AND, OR, DEFAULT = list(range(0, 10))

    opTable = { "<" : LT, "<=" : LE, ">" : GT, ">=" : GE, "=" : EQ, "==" : EQ,
    "!=" : NE, "&&" : AND, "||" : OR, "default" : DEFAULT, "DEFAULT" : DEFAULT}
    def __init__(self, value=0.0, op=NO_OP, color=None, blinkColor=None, left=None, right=None):
        self.val, self.op, self.color, self.blinkColor = value, op, color, blinkColor
        self.left, self.right = left, right
        self.blinking = (self.blinkColor != None)

    def truthTest( self, value=0.0):
        if self.op == self.NO_OP:       return 1
        if self.op == self.DEFAULT:     return 1
        if self.op == self.LT:          return (value < self.val)
        if self.op == self.LE:          return (value <= self.val)
        if self.op == self.GT:          return value > self.val
        if self.op == self.GE:          return value >= self.val
        if self.op == self.EQ:          return (value == self.val)
        if self.op == self.NE:          return value != self.val
        if self.op == self.AND:         return self.left.truthTest( value) and self.right.truthTest(value)
        if self.op == self.OR:          return self.left.truthTest(value) or self.right.truthTest(value)
        return 0

    def printRule(self, indent=0):
        print("  "*indent, self.op, self.val)
        if self.left != None:
            self.left.printRule(indent+1)
        if self.right != None:
            self.right.printRule(indent+1)
        
class colorRule:
    invisible = QColor(0,0,0,0)
    def __init__(self, name="", numeric=-1):
        self.ruleList = []
        self.name = name
        self.numeric = numeric

    def __str__(self):
        return f"{self.numeric}: {self.name}"

    # add a rule for this color name
    def addRule(self, value=0.0, op=oneRule.NO_OP, color = None, blinkColor=None, left=None, right=None):
        self.ruleList.append( oneRule(value, op, color, blinkColor, left, right) )
        return self.ruleList[-1]

    def isRule(self):
        '''isRule - returns False if a static rule, True otherwise'''
        return self.ruleList[0].op != oneRule.DEFAULT

    # return the color for this rule
    def getColor( self, value=0.0, defColor=Qt.black):
        try:
            value = float(value)
        except:
            print(f"unable to convert {value} to float for {self.numeric} aka {self.name}")
            return defColor
        for rule in self.ruleList:
            if rule.truthTest(value):
                if rule.color == None:
                    print(f"...using default color (none set). value={value} color name={self.name} index={self.numeric}")
                    return defColor
                return rule.color
        print(f"...using default color (no match), value={value} color name={self.name} index={self.numeric}")
        return defColor

class edmColor:
    '''edmColor - loads and manages an edm Color file.'''
    # This pattern element looks weird - what it does is fails the match if
    # it immediately followed by "=" followed by a non-identifier character
    #    | [a-zA-Z0-9\.-]*(?=[^\.a-zA-Z0-9-])
    pat = "\\s+"\
        "|#.*"\
        "|[{}:?*]"\
        "|>=|>|<=|<|=|!=|\\&\\&|\\|\\|"\
        "|\"[^\"]*\""\
        "|[a-zA-Z][a-zA-Z0-9]*=.+"\
        "|[a-zA-Z0-9\\.-]+(?=[^\\.a-zA-Z0-9-])"
    pat_r = re.compile(pat)
    debug = 0

    # dictionary of names for colors
    colorNames = {}
    # index of names for index
    colorIndex = {}
    # aliases
    aliasList = {}
    # builtin Rules
    builtin = {}
    # alarm colors
    alarms = {}

    def __init__(self):
        self.wordlist = []
        # self.loadColor( colorfile)

    def loadColor(self, colorfile=None):
        if colorfile == None:
            colorfile = getenv("EDMCOLORFILE")
            if colorfile == None:
                colorfile = getenv("EDMFILES")
                if colorfile == None:
                    colorfile = "/etc/edm"
                colorfile = colorfile + "/colors.list"
        self.readColorFile(colorfile)
        self.addBuiltin( "builtin:transparent", 0, 0, 0, 0)

    def addBuiltin(self, name, r, g, b, a=255):
        self.builtin[name] = colorRule(name=name)
        self.builtin[name].addRule( 0.0, oneRule.DEFAULT, QColor( r, g, b, a) )

    def buildRule(self, buildList, rule, start):
        op, value = oneRule.NO_OP, 0.0
        while start < len(buildList):
            if buildList[start] == ":" :
                rule.op = op
                rule.val = value
                return start
            if buildList[start] in oneRule.opTable:
                op = oneRule.opTable[buildList[start]]
            else:
                op = oneRule.NO_OP
            if op == oneRule.AND or op == oneRule.OR:
                rule.op = op
                rule.left = oneRule(op=prevOp, value=value)
                rule.right = oneRule()
                start = self.buildRule(buildList, rule.right, start+1)
                return start
            prevOp = op
            if op != oneRule.DEFAULT:
                start = start+1
                value = float(buildList[start])
            start = start+1
        print('buildRule dropped out the bottom!')
        return start

    def readColorFile(self, colorfile):
        if self.debug > 0 : print(f"colorFile {colorfile}")
        try: fp = open(colorfile, "r")
        except:
            print("Unable to open Color File '%s'" % (colorfile,))
            return

        inBlock = 0
        needWords = 0
        needBlock = 0
        capture = 0
        words = []

        while True:
            word = self.getNextWord(fp)
            if word == None:
                fp.close()
                return
            if self.debug>0 : print(word, self.wordlist, inBlock, capture, needWords, needBlock)
            if inBlock:
                if word != "}":
                    blockList.append( word)
                    continue
                inBlock = 0
                if words[0] == "static" and len(words) > 2:
                    #
                    # build a new color
                    #
                    # print "Build static color ", words, blockList, int(words[1])
                    self.myRule = self.findRule( words[2],
                            numeric=int(words[1]), create=1)
                    blinkColor = None
                    if words[2] == "invisible":  # EDM Magic Value
                        color = QColor(0,0,0,0)
                    else:
                        color = QColor( int(blockList[0])>>8, int(blockList[1])>>8, int(blockList[2])>>8) 
                        if len(blockList) > 5:
                            blinkColor = QColor( int(blockList[3])>>8, int(blockList[4])>>8, int(blockList[5])>>8) 
                    words = []
                    self.myRule.addRule( 0.0, oneRule.DEFAULT, color, blinkColor)
                    continue

                # build the alarm colors
                if words[0] == "alarm":
                    for w in range(0,len(blockList), 3):
                        if blockList[w+2] != '*':
                            edmColor.alarms[blockList[w]] = self.findRule(blockList[w+2])
                    words = []
                    continue

                if words[0] == "rule" and len(words) > 2:
                    #
                    # build a new rule
                    #
                    # print "Build color rule ", words, blockList
                    self.myRule = self.findRule( words[2], numeric=int(words[1]), create=1)
                    words = []
                    idx = 0
                    inProgress = oneRule()
                    if self.debug > 0: print("building rules list", blockList)
                    while idx < len(blockList):
                        idx = self.buildRule(blockList, inProgress, idx)
                        if blockList[idx] != ":":
                            print("Warning: blocklist[", idx, "] != ':'")
                            break
                        idx = idx+1
                        staticRule = self.findRule( blockList[idx])
                        col = Qt.black
                        blinkColor = None
                        if staticRule and staticRule.ruleList[0].color != None:
                            col = staticRule.ruleList[0].color
                            blinkColor = staticRule.ruleList[0].blinkColor
                        if blockList[idx] == "*" : col = None
                        if inProgress.op == oneRule.AND or inProgress.op == oneRule.OR:
                            self.myRule.addRule( op=inProgress.op, color=col, blinkColor=blinkColor, left=inProgress.left, right=inProgress.right)
                        else:
                            self.myRule.addRule( value=inProgress.val, op=inProgress.op, color=col)
                        idx = idx+1
                    if self.debug > 0:
                        for rt in self.myRule.ruleList:
                            rt.printRule()
                    continue

                # hit the end of a block without knowing what's going on
                print(f"Ignoring {words} {blockList}")
                words = []
                continue

            if word == "{":
                inBlock = 1
                blockList = []
                continue

            if needWords > 0:
                words.append(word)
                if needBlock == 0 and len(words) >= needWords:
                    # build an alias
                    # print "Alias", words[1], words[2]
                    self.aliasList[words[1]] = words[2]
                    words = []
                    needWords = 0
                continue

            needBlock = 0
            words = [word]
            if word == "alias":
                needWords = 3
            if word == "static" or word == "rule":
                needBlock, needWords = 1,3
            if word == "alarm" or word == "menumap":
                needBlock, needWords = 1,1


    def findColor(self, name):
        pass

    def findRule(self, index, numeric=None, create=0):
        if isinstance(index, colorRule):
            return index
        if index in self.builtin:
            return self.builtin[index]
        idx = None
        if type(index) == int:
            name = self.colorIndex[index]
        else:
            try:
                idx = int(index)
            except:
                name = index
            else:
                if idx in self.colorIndex:
                    name = self.colorIndex[idx]
                else:
                    name = None
            finally:
                pass
        if name != None:
            if name in self.colorNames:
                return self.colorNames[name]

        if create == 0:
            # when doing a lookup, try the alias table
            maxRetry=10
            while maxRetry > 0 and name in self.aliasList:
                name = self.aliasList[name]
                maxRetry = maxRetry-1
            if name in self.colorNames:
                return self.colorNames[name]
            return None
        if numeric == None:     # want to create, but no numeric value given
            return None
        cr = colorRule(name=name,numeric=numeric)
        self.colorNames[name] = cr
        self.colorIndex[numeric] = name
        return cr

    def getNextWord(self, fp):
        while self.wordlist == []:
            line = self.getNextLine(fp)
            if line == None:
                return None
            self.wordlist = self.pat_r.findall(line)
            if self.debug : print("Wordlist is ", self.wordlist)
            if self.wordlist == []:
                return None

        word = self.wordlist[0]
        if word[0] == '"':
            word = word[1:-1]
        self.wordlist = self.wordlist[1:]
        # if a comment or whitespace, recurse
        if word == "" or word[0] == "#" or re.match(r"\s", word):
            return self.getNextWord(fp)

        return word

    def getNextLine(self,fp):
        line = fp.readline()
        if self.debug > 0 : print("Read Line:", line)
        return line

# Wrappers for 'edmColor'
# colorName is a numeric color
def loadColorFile(filename):
    colorTable.loadColor(filename)

def findColorRule(colorName):
    try:
        if colorName.startswith("index "):
            colorName = colorName.split(" ")[1]
    except AttributeError:
        pass
    return colorTable.findRule(colorName)

# Stub - return generic colors. This should use the alarm colors defined in the
# file.
def getAlarmColor(status,valid):
    if valid == 0:
        return edmColor.alarms["disconnected"].getColor()
    if status == 1:
        return edmColor.alarms["minor"].getColor()
    if status == 2:
        return edmColor.alarms["major"].getColor()
    if status == 3:
        return edmColor.alarms["invalid"].getColor()
    return Qt.black

# Load the color table
colorTable = edmColor()

