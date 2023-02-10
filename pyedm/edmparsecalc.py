# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#
# MODULE LEVEL: low
# This is a low level module
# Used by edmPVcalc to evaluate expressions

# Majority of the code taken from EPICS libCom/calc/calcPerform.c,
# libCom/calc/postfix.c, and libCom/calc/postfix.h
# Those files are Copyright 2002 The University of Chicago and The Regents of the University of California
# A class to interpret strings as formulas.
# Strings are turned into an intermediate tree, and evaluated on request.
#

from .edmparsetable import elementTypeEnum as ete, opCodeEnum as oce, operators, operands
import re
import math

opchars = "(!=|#|%|&&|&|\)|\*|\*\*|\+|,|-|/|:|:=|;|<<|<=|<|==|=|>=|>>|>|\?|\^|\|\||\||\()"

class Postfix:
    def __init__(self, expr=None):
        self.DebugFlag = False
        if expr != None:
            self.parseExpression(expr)

    def __get_element(self, need_operand, symbol):
        '''
          __get_element - return the enum matching the symbol, using
          the 'need_operand' flag to determine whether to look at
          the operators or operands table
          '''
        if self.DebugFlag : print("__get_element", need_operand, symbol)
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

    def __parseWords(self, words, idx=0):
        need_operand = True
        self.cond_count = 0
        depth = 0
        stack = []
        postfix = []
        while idx < len(words):
            elem = self.__get_element(need_operand, words[idx])
            if elem == None:
                print(f"Unexpected: '{words[idx]}'")
                return None
            if elem.stack_effect > 0:       # OPERAND
                postfix.append(elem.opcode)
                depth = depth+elem.stack_effect
                if elem.opcode == oce.LITERAL_DOUBLE:
                    try:
                        lit_d = float(words[idx])
                    except:
                        print("Bad double", words[idx])
                        return None
                    lit_i = int(lit_d)
                    if float(lit_i) == lit_d:
                        postfix[-1] = oce.LITERAL_INT
                        postfix.append(lit_i)
                    else:
                        postfix.append(lit_d)
                need_operand = False

            elif elem.e_type in [ ete.OPEN_PAREN, ete.UNARY_OPERATOR, ete.BINARY_OPERATOR, ete.VARARG_OPERATOR]:
                while len(stack) > 0 and stack[-1].stack_pri >= elem.input_pri:
                    e = stack.pop()
                    depth = depth + e.stack_effect
                    postfix.append(e.opcode)
                    if e.e_type == ete.VARARG_OPERATOR:
                        postfix.append(1 - e.stack_effect)
                stack.append(elem)
                if elem.e_type == ete.BINARY_OPERATOR:
                    need_operand = True

            elif elem.e_type == ete.SEPERATOR:
                while stack[-1].e_type != ete.OPEN_PAREN:
                    if len(stack) <= 1:
                        print("Bad comma placement")
                        return None
                    e = stack.pop()
                    postfix.append(e.opcode)
                    depth = depth + e.stack_effect
                need_operand = True
                stack[-1].stack_effect -= 1

            elif elem.e_type == ete.CLOSE_PAREN:
                while stack[-1].e_type != ete.OPEN_PAREN:
                    if len(stack) <= 1:
                        print("Parenthesis error")
                        return None
                    e = stack.pop()
                    postfix.append(e.opcode)
                    depth = depth + e.stack_effect
                stack.pop()

            elif elem.e_type == ete.CONDITIONAL:
                while len(stack) > 0 and stack[-1].stack_pri > elem.input_pri:
                    e = stack.pop()
                    depth = depth + e.stack_effect
                    postfix.append(e.opcode)
                postfix.append(elem.opcode)
                if elem.opcode == oce.COND_ELSE:
                    self.cond_count = self.cond_count-1
                    stack.append(self.__get_element(False, "cond-end"))
                else:
                    self.cond_count = self.cond_count+1
                need_operand = True

            elif elem.e_type == ete.EXPR_TERMINATOR:
                while len(stack) > 0:
                    e = stack.pop()
                    if e.e_type == ete.OPEN_PAREN:
                        print("Missing closing parenthesis")
                        return None
                    postfix.append(e.opcode)
                    if e.e_type == ete.VARARG_OPERATOR:
                        postfix.append(1 - e.stack_effect)
                    depth = depth + e.stack_effect

                if self.cond_count != 0:
                    print("Bad conditional")
                    return None
                if depth > 1:
                    print("Too many results returned")
                need_operand = True

            elif elem.e_type == ete.STORE_OPERATOR:
                pass

            else:
                print("How did I get here?")
                return None

            idx = idx + 1

        while len(stack) > 0:
            e = stack.pop()
            postfix.append(e.opcode)
            depth = depth + e.stack_effect

        postfix.append(oce.END_EXPRESSION)

        if self.cond_count != 0:
            pass
        if need_operand or depth != 1:
            pass
        return postfix

    def parseExpression(self, expression):
        ex = re.split( opchars, expression)
        ex = [ item for item in ex if item != '' ]
        self.postfix =  self.__parseWords(ex)

    def calculate(self, variables=None):
        stack = []
        idx = 0
        while idx < len(self.postfix):
            op = self.postfix[idx]
            if op == oce.LITERAL_INT or op == oce.LITERAL_DOUBLE:
                idx = idx+1
                stack.append(self.postfix[idx])
            elif op.value >= oce.FETCH_A.value and op.value <= oce.FETCH_L.value:
                v_idx = op.value-oce.FETCH_A.value
                stack.append(variables[v_idx])
            elif op == oce.CONST_PI:
                stack.append(math.pi)
            elif op == oce.CONST_D2R:
                stack.append(math.pi/180.0)
            elif op == oce.CONST_R2D:
                stack.append(180.0/math.pi)
            elif op == oce.UNARY_NEG:
                stack[-1] = -stack[-1]
            elif op == oce.ADD:
                top = stack.pop()
                stack[-1] = stack[-1] + top
            elif op == oce.SUB:
                top = stack.pop()
                stack[-1] = stack[-1] - top
            elif op == oce.MULT:
                top = stack.pop()
                stack[-1] = stack[-1] * top
            elif op == oce.DIV:
                top = stack.pop()
                stack[-1] = stack[-1]/ top
            elif op == oce.MODULO:
                top = stack.pop()
                stack[-1] = math.fmod(stack[-1] , top)
            elif op == oce.POWER:
                top = stack.pop()
                stack[-1] = math.pow(stack[-1], top)
            elif op == oce.ABS_VAL:
                if stack[-1] < 0.0:
                    stack[-1] = - stack[-1]
            elif op == oce.EXP:
                stack[-1] = math.exp(stack[-1])
            elif op == oce.LOG_10:
                stack[-1] = math.log10(stack[-1])
            elif op == oce.LOG_E:
                stack[-1] = math.log(stack[-1])
            elif op == oce.MAX:
                top = stack.pop()
                if stack[-1] < top or math.isnan(top):
                    stack[-1] = top
            elif op == oce.MIN:
                top = stack.pop()
                if stack[-1] > top or math.isnan(top):
                    stack[-1] = top
            elif op == oce.SQU_RT:
                stack[-1] = math.sqrt(stack[-1])
            elif op == oce.ACOS:
                stack[-1] = math.acos(stack[-1])
            elif op == oce.ASIN:
                stack[-1] = math.asin(stack[-1])
            elif op == oce.ATAN:
                stack[-1] = math.atan(stack[-1])
            elif op == oce.ATAN2:
                top = stack.pop()
                stack[-1] = math.atan2(top, stack[-1])
            elif op == oce.COS:
                stack[-1] = math.cos(stack[-1])
            elif op == oce.SIN:
                stack[-1] = math.sin(stack[-1])
            elif op == oce.TAN:
                stack[-1] = math.tan(stack[-1])
            elif op == oce.COSH:
                stack[-1] = math.cosh(stack[-1])
            elif op == oce.SINH:
                stack[-1] = math.sinh(stack[-1])
            elif op == oce.TANH:
                stack[-1] = math.tanh(stack[-1])
            elif op == oce.CEIL:
                stack[-1] = math.ceil(stack[-1])
            elif op == oce.FLOOR:
                stack[-1] = math.floor(stack[-1])
            elif op == oce.FINITE:
                stack[-1] = not math.isinf(stack[-1]) and not math.isnan(stack[-1])
            elif op == oce.ISINF:
                stack[-1] = math.isinf(stack[-1])
            elif op == oce.ISNAN:
                stack[-1] = math.isnan(stack[-1])
            elif op == oce.NINT:
                top = stack[-1]
                top = top+0.5 if top >= 0 else top-0.5
                stack[-1] = float(int(top))
            elif op == oce.RANDOM:
                stack.append(random.random())
            elif op == oce.REL_OR:
                top = stack.pop()
                stack[-1] = stack[-1] or top
            elif op == oce.REL_AND:
                top = stack.pop()
                stack[-1] = stack[-1] and top
            elif op == oce.REL_NOT:
                stack[-1] = not stack[-1]
            elif op == oce.BIT_OR:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) | top
            elif op == oce.BIT_AND:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) & top
            elif op == oce.BIT_EXCL_OR:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) ^ top
            elif op == oce.BIT_NOT:
                stack[-1] = -1 ^ int(stack[-1])
            elif op == oce.RIGHT_SHIFT:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) >> top
            elif op == oce.LEFT_SHIFT:
                top = int(stack.pop())
                stack[-1] = int(stack[-1]) << top
            elif op == oce.NOT_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] != top)
            elif op == oce.LESS_THAN:
                top = stack.pop()
                stack[-1] = (stack[-1] < top)
            elif op == oce.LESS_OR_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] <= top)
            elif op == oce.EQUAL:
                top = stack.pop()
                stack[-1] = (stack[-1] == top)
            elif op == oce.GR_OR_EQ:
                top = stack.pop()
                stack[-1] = (stack[-1] >= top)
            elif op == oce.GR_THAN: 
                top = stack.pop()
                stack[-1] = (stack[-1] > top)
            elif op == oce.COND_IF:
                val = stack.pop()
                if val == 0:
                    idx = self.cond_search( idx, oce.COND_ELSE)
            elif op == oce.COND_ELSE:
                idx = self.cond_search(idx, oce.COND_END)
            elif op == oce.COND_END:
                pass
            elif op == oce.END_EXPRESSION:
                pass
            else:
                print("Bad opcode:", op)
                return None
            idx = idx + 1
        if len(stack) != 1:
            print("poorly formed expression list", stack, self.postfix)
            return None
        return stack[0]

    def cond_search(self, idx, match):
        nest = 0
        for i in range(idx+1, len(self.postfix)):
            if self.postfix[i] == match and nest == 0:
                return i
            if self.postfix[i] == oce.COND_IF:
                nest = nest+1
            elif self.postfix[i] == oce.COND_END:
                nest = nest-1
        return idx
        
if __name__ == "__main__":
    import sys
    tree = Postfix()
    tree.DebugFlag = 1
    tree.parseExpression(sys.argv[1])
    print(tree.postfix)
    print(tree.calculate( [1,2,3,4,5,6,7,8,9,10,11,12] ))
