# Copyright 2023 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
#
# class providing a CALC process variable for EDM

from pyedm.edmPVfactory import edmPVbase, pvClassDict, buildPV
from pyedm.edmparsecalc import Postfix

class calcPV(edmPVbase):
    def __init__(self, name=None, macroTable=None, **kw):
        super().__init__( name="CALC", macroTable=macroTable, **kw)
        self.name = name
        self.inInit = True      # flag to prevent early calls to onChange from processing
        expression = name.split("}", 1)
        self.setCalc(expression[0].strip("{}\\"))
        self.setPVargs(expression[1][1:-1], macroTable )
        self.pvType = edmPVbase.typeFloat
        self.precision = 4
        self.prefix = "CALC\\"
        #
        self.allValid = [ pv.isValid for pv in self.pvArgs ]
        self.inInit = False
        # There shouldn't be a race condition, here, but I'm not confident of the proof of that.
        if False not in self.allValid:
            self.isValid = True
            self.severity = 0
            self.value = self.calcValue()
            self.char_value = self.convText()
            for fn in self.callbackList:
                fn[0](fn[1], pvname=self.name, chid=0,pv=self,value=self.value,count=1,units=self.units,severity=0,userArgs=fn[2])

    # given a list of PV's, attach them and have them call back to record
    # changes
    def setPVargs(self,args,mt):
        pvlist = args.split(",")
        self.pvArgs = []
        self.pvValues = [ ]
        for idx, pv in enumerate(pvlist):
            thispv = buildPV(pv,macroTable=mt)
            self.pvArgs.append( thispv)
            self.pvValues.append( 0.0)
            thispv.add_callback(self.onChange, self, idx)

    def setCalc(self, calc):
        self.expr = Postfix(calc)

    def edmCleanup(self):
        super().edmCleanup()
        self.pvArgs, pvs = None, self.pvArgs

        for pv in pvs:
            pv.del_callback(self.onChange)

    def get(self):
        return self.calcValue()

    def onChange(self, item, **kw):
        # userArgs is the index into pvValues, allValid
        #
        if self.debug(): print("callback CALC onChange", item)
        if 'userArgs' not in kw:
            return

        idx = int(kw['userArgs'])

        self.pvValues[idx] = kw["value"]

        # if still initializing, don't perform the calculation
        if self.inInit:
            return

        self.allValid[idx] = True
        self.isValid = False not in self.allValid

        if not self.isValid:
            self.severity = 3
            return

        self.value = self.calcValue()
        self.char_value = self.convText()

        self.severity = 0
        if self.debug(): print("callback CALC", self.name, "value=", self.value, self.callbackList)
        for fn in self.callbackList:
            fn[0](fn[1], pvname=self.name, chid=0,pv=self,value=self.value,count=1,units=self.units,severity=0,userArgs=fn[2])
        if self.debug(): print("END callback CALC", self.name)

    # recalculate the value for the equation
    def calcValue(self):
        try:
            val = self.expr.calculate(self.pvValues)
            if val != None:
                return val
        except BaseException as exc:
            print("Calculation failed:", self.name, self.pvValues)
            print(exc)
        return 0.0

def buildCalcPV(**kw):
    return calcPV(**kw)

pvClassDict["CALC"] = buildCalcPV

