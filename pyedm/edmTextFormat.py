# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Routines to convert a value for display. Note that these are designed to be
# called indirectly through a lookup table
#

# Convert Default: if charValue is set, then make the simplistic assumption
# that that is what is wanted
from builtins import str
def convDefault(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    if precision==-1 and charValue != None:
        return charValue
    try: return "%.*f%s" %(precision, float(value),addUnits(units,showUnits))
    except: return str(value)+addUnits(units,showUnits)

def convDecimal(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    if type(value) == int:
        return "%d%s"%(value, addUnits(units,showUnits))
    try: return "%.*f%s" %(precision, float(value),addUnits(units,showUnits))
    except ValueError:
        pass
    try: return "%*d%s"%(precision, int(value),addUnits(units,showUnits))
    except: return str(value)

def convHex(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    try: return "%x%s"%(int(value), addUnits(units,showUnits))
    except: return str(value)+addUnits(units,showUnits)

def convEngineer(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    try: return "%.*g%s" %(precision, float(value),addUnits(units,showUnits))
    except: return str(value)

def convExp(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    try: return "%.*e%s" %(precision, float(value),addUnits(units,showUnits))
    except: return str(value)

def convString(value, charValue=None, pv=None, precision=-1, units=None, showUnits=1):
    if charValue != None:
        return charValue
    return str(value)

def addUnits(units, showUnits):
    if units and units != "" and showUnits:
        return " "+units
    return ""
