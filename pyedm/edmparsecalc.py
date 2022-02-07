from __future__ import division
from __future__ import print_function
# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# Majority of the code taken from EPICS libCom/calc/calcPerform.c,
# libCom/calc/postfix.c, and libCom/calc/postfix.h
# Those files are Copyright 2002 The University of Chicago and The Regents of the University of California
# A class to interpret strings as formulas.
# Strings are turned into an intermediate tree, and evaluated on request.
#

from builtins import range
from builtins import object
from past.utils import old_div
from pyedm.edmparsetable import *
import re
import math
# from __future__ import print_function

opchars = "(!=|#|%|&&|&|\)|\*\*|\*|\+|,|-|/|:|:=|;|<<|<=|<|==|=|>=|>>|>|\?|\^|\|\||\||\()"

class Postfix(object):
    def __init__(self, expr=None):
        self.DebugFlag = False
        if expr != None:
            self.parseExpression(expr)

    def __get_element__(self, need_operand, symbol):
        if self.DebugFlag : print("__get_element__", need_operand, symbol)
        symbol = symbol.strip()
        if need_operand == False:
            if symbol in operators:
                return operators[symbol]
            return None
        if symbol in operands:
                return operands[symbol]
        try:
            val = float(symbol)
            return operands["0"]
        except:
            return None

    def __parseWords__(self, words, idx=0):
        need_operand = True
        self.cond_count = 0
        depth = 0
        stack = []
        postfix = []
        while idx < len(words):
            elem = self.__get_element__(need_operand, words[idx])
            if elem == None:
                print("Unexpected: '%s'" % (words[idx], ))
                return None
            if self.DebugFlag > 0: print("parsed as", elem.opcode)
            if elem.stack_effect > 0:       # OPERAND
                postfix.append(elem.opcode)
                depth = depth+elem.stack_effect
                if elem.opcode == LITERAL_DOUBLE:
                    try:
                        lit_d = float(words[idx])
                    except:
                        print("Bad double", words[idx])
                        return None
                    lit_i = int(lit_d)
                    if float(lit_i) == lit_d:
                        postfix[-1] = LITERAL_INT
                        postfix.append(lit_i)
                    else:
                        postfix.append(lit_d)
                need_operand = False

            elif elem.type == OPEN_PAREN or elem.type == UNARY_OPERATOR or elem.type == BINARY_OPERATOR or elem.type == VARARG_OPERATOR:
                while len(stack) > 0 and stack[-1][0].stack_pri >= elem.input_pri:
                    e, effect = stack.pop()
                    depth = depth + effect
                    postfix.append(e.opcode)
                    if e.type == VARARG_OPERATOR:
                        postfix.append(1 - effect)
                stack.append( [elem, elem.stack_effect] )
                if elem.type == BINARY_OPERATOR:
                    need_operand = True

            elif elem.type == SEPERATOR:
                while stack[-1][0].type != OPEN_PAREN:
                    if len(stack) <= 1:
                        print("Bad comma placement")
                        return None
                    e, effect = stack.pop()
                    postfix.append(e.opcode)
                    if e.type == VARARG_OPERATOR:
                        postfix.append(1 - effect)
                    depth = depth + effect
                need_operand = True
                stack[-1][1] -= 1

            elif elem.type == CLOSE_PAREN:
                while stack[-1][0].type != OPEN_PAREN:
                    if len(stack) <= 1:
                        print("Parenthesis error")
                        return None
                    e, effect = stack.pop()
                    postfix.append(e.opcode)
                    if e.type == VARARG_OPERATOR:
                        postfix.append(1 - effect)
                    depth = depth + effect
                e, effect = stack.pop()
                if len(stack) > 0:
                    stack[-1][1] = effect
                    if effect > 0:
                        print("no args?")

            elif elem.type == CONDITIONAL:
                while len(stack) > 0 and stack[-1][0].stack_pri > elem.input_pri:
                    e, effect = stack.pop()
                    depth = depth + effect
                    postfix.append(e.opcode)
                    if e.type == VARARG_OPERATOR:
                        postfix.append(1-effect)
                postfix.append(elem.opcode)
                depth = depth + elem.stack_effect
                if elem.opcode == COND_ELSE:
                    self.cond_count = self.cond_count-1
                    stack.append( [self.__get_element__(False, "cond-end"), 0] )
                else:
                    self.cond_count = self.cond_count+1
                need_operand = True

            elif elem.type == EXPR_TERMINATOR:
                while len(stack) > 0:
                    e, effect = stack.pop()
                    if e.type == OPEN_PAREN:
                        print("Missing closing parenthesis")
                        return None
                    postfix.append(e.opcode)
                    if e.type == VARARG_OPERATOR:
                        postfix.append(1 - effect)
                    depth = depth + effect

                if self.cond_count != 0:
                    print("Bad conditional")
                    return None
                if depth > 1:
                    print("Too many results returned")
                need_operand = True

            elif elem.type == STORE_OPERATOR:
                pass

            else:
                print("How did I get here?")
                return None

            idx = idx + 1

        while len(stack) > 0:
            e, effect = stack.pop()
            postfix.append(e.opcode)
            if e.type == VARARG_OPERATOR:
                postfix.append(1 - effect)
            depth = depth + effect

        postfix.append(END_EXPRESSION)

        if self.cond_count != 0:
            pass
        if need_operand or depth != 1:
            pass
        return postfix

    def parseExpression(self, expression):
        ex = re.split( opchars, expression)
        ex = [ item for item in ex if item != '' ]
        self.postfix =  self.__parseWords__(ex)

    def nextop(self, opiter):
        try:
            op = next(opiter)
            return op
        except StopIteration:
            print("request for next op failed")
            return None

    def calculate(self, variables=None):
        stack = []
        idx = 0
        opiter = iter(self.postfix)
        while True:
            try:
                op = next(opiter)
            except StopIteration:
                break

            if op == LITERAL_INT or op == LITERAL_DOUBLE:
                stack.append(self.nextop(opiter) )
            elif op >= FETCH_A and op <= FETCH_L:
                v_idx = op-FETCH_A
                stack.append(variables[v_idx])
            elif op == CONST_PI:
                stack.append(math.pi)
            elif op == CONST_D2R:
                stack.append(old_div(math.pi,180.0))
            elif op == CONST_R2D:
                stack.append(old_div(180.0,math.pi))
            elif op == UNARY_NEG:
                stack[-1] = -stack[-1]
            elif op == ADD:
                top = stack.pop()
                stack[-1] = stack[-1] + top
            elif op == SUB:
                top = stack.pop()
                stack[-1] = stack[-1] - top
            elif op == MULT:
                top = stack.pop()
                stack[-1] = stack[-1] * top
            elif op == DIV:
                top = stack.pop()
                stack[-1] = old_div(stack[-1], top)
            elif op == MODULO:
                top = stack.pop()
                stack[-1] = math.fmod(stack[-1] , top)
            elif op == POWER:
                top = stack.pop()
                stack[-1] = math.pow(stack[-1], top)
            elif op == ABS_VAL:
                if stack[-1] < 0.0:
                    stack[-1] = - stack[-1]
            elif op == EXP:
                stack[-1] = math.exp(stack[-1])
            elif op == LOG_10:
                stack[-1] = math.log10(stack[-1])
            elif op == LOG_E:
                stack[-1] = math.log(stack[-1])
            elif op == MAX:
                nargs = next(opiter)
                print("nargs=", nargs)
                for idx in range(nargs-1):
                    top = stack.pop()
                    if stack[-1] < top or math.isnan(top):
                        stack[-1] = top
            elif op == MIN:
                nargs = next(opiter)
                print("nargs=", nargs)
                for idx in range(nargs-1):
                    top = stack.pop()
                    if stack[-1] > top or math.isnan(top):
                        stack[-1] = top
            elif op == SQU_RT:
                stack[-1] = math.sqrt(stack[-1])
            elif op == ACOS:
                stack[-1] = math.acos(stack[-1])
            elif op == ASIN:
                stack[-1] = math.asin(stack[-1])
            elif op == ATAN:
                stack[-1] = math.atan(stack[-1])
            elif op == ATAN2:
                top = stack.pop()
                stack[-1] = math.atan2(top, stack[-1])
            elif op == COS:
                stack[-1] = math.cos(stack[-1])
            elif op == SIN:
                stack[-1] = math.sin(stack[-1])
            elif op == TAN:
                stack[-1] = math.tan(stack[-1])
            elif op == COSH:
                stack[-1] = math.cosh(stack[-1])
            elif op == SINH:
                stack[-1] = math.sinh(stack[-1])
            elif op == TANH:
                stack[-1] = math.tanh(stack[-1])
            elif op == CEIL:
                stack[-1] = math.ceil(stack[-1])
            elif op == FLOOR:
                stack[-1] = math.floor(stack[-1])
            elif op == FINITE:
                stack[-1] = not math.isinf(stack[-1]) and not math.isnan(stack[-1])
            elif op == ISINF:
                stack[-1] = math.isinf(stack[-1])
            elif op == ISNAN:
                stack[-1] = math.isnan(stack[-1])
            elif op == NINT:
                top = stack[-1]
                top = top+0.5 if top >= 0 else top-0.5
                stack[-1] = float(int(top))
            elif op == RANDOM:
                stack.append(random.random())
            elif op == REL_OR:
                top = stack.pop()
                stack[-1] = stack[-1] or top
            elif op == REL_AND:
                top = stack.pop()
                stack[-1] = stack[-1] and top
            elif op == REL_NOT:
                stack[-1] = not stack[-1]
            elif op == BIT_OR:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) | top
            elif op == BIT_AND:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) & top
            elif op == BIT_EXCL_OR:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) ^ top
            elif op == BIT_NOT:
                stack[-1] = -1 ^ int(stack[-1])
            elif op == RIGHT_SHIFT:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) >> top
            elif op == LEFT_SHIFT:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) << top
            elif op == NOT_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] != top)
            elif op == LESS_THAN:
                top = stack.pop()
                stack[-1] = (stack[-1] < top)
            elif op == LESS_OR_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] <= top)
            elif op == EQUAL:
                top = stack.pop()
                stack[-1] = (stack[-1] == top)
            elif op == GR_OR_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] >= top)
            elif op == GR_THAN: 
                top = stack.pop()
                stack[-1] = (stack[-1] > top)
            elif op == COND_IF:
                val = stack.pop()
                if val == 0:
                    self.cond_search( opiter, COND_ELSE)
            elif op == COND_ELSE:
                self.cond_search(opiter, COND_END)
            elif op == COND_END:
                pass
            elif op == END_EXPRESSION:
                pass
            else:
                print("Bad opcode:", op)
                return None

        if len(stack) != 1:
            print("poorly formed expression list", stack, self.postfix)
            return None
        return stack[0]

    def cond_search(self, opiter, match):
        nest = 0
        op = self.nextop(opiter)
        while op != None:
            if op == match:
                if nest <= 0: return
                nest -= 1
            elif op == COND_IF:
                nest += 1
            # TO DO: skip literals, variable list functions
            elif op == LITERAL_DOUBLE or op == LITERAL_INT:
                next(opiter)
            elif op in (MIN, MAX, FINITE, ISNAN):
                next(opiter)
            op = next(opiter)

if __name__ == "__main__":
    import sys
    tree = Postfix()
    tree.DebugFlag = 1
    tree.parseExpression(sys.argv[1])
    print(tree.postfix)
    print(tree.calculate( [1,2,3,4,5,6,7,8,9,10,11,12] ))
