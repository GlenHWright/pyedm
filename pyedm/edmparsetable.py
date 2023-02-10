# Copyright 2022 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.

from dataclasses import dataclass
from enum import Enum
from typing import Any

# MODULE LEVEL: base
# base level module
# only used by parsecalc

# Types of elements being parsed
elementTypeEnum = Enum("elementType", [
        "OPERAND", "LITERAL_OPERAND", "STORE_OPERATOR", "UNARY_OPERATOR", "VARARG_OPERATOR", "BINARY_OPERATOR", "SEPERATOR",
        "OPEN_PAREN", "CLOSE_PAREN", "CONDITIONAL", "EXPR_TERMINATOR"
        ] )


# op codes being parsed
opCodeEnum = Enum("opCode", [
        "END_EXPRESSION",
    # /* Operands */
	"LITERAL_DOUBLE", "LITERAL_INT", "FETCH_VAL",
	"FETCH_A", "FETCH_B", "FETCH_C", "FETCH_D", "FETCH_E", "FETCH_F",
	"FETCH_G", "FETCH_H", "FETCH_I", "FETCH_J", "FETCH_K", "FETCH_L",
    # /* Assignment */
	"STORE_A", "STORE_B", "STORE_C", "STORE_D", "STORE_E", "STORE_F",
	"STORE_G", "STORE_H", "STORE_I", "STORE_J", "STORE_K", "STORE_L",
    # /* Trigonometry Constants */
	"CONST_PI",
	"CONST_D2R",
	"CONST_R2D",
    # /* Arithmetic */
	"UNARY_NEG",
	"ADD",
	"SUB",
	"MULT",
	"DIV",
	"MODULO",
	"POWER",
    # /* Algebraic */
	"ABS_VAL",
	"EXP",
	"LOG_10",
	"LOG_E",
	"MAX",
	"MIN",
	"SQU_RT",
    # /* Trigonometric */
	"ACOS",
	"ASIN",
	"ATAN",
	"ATAN2",
	"COS",
	"COSH",
	"SIN",
	"SINH",
	"TAN",
	"TANH",
    # /* Numeric */
	"CEIL",
	"FLOOR",
	"FINITE",
	"ISINF",
	"ISNAN",
	"NINT",
	"RANDOM",
    # /* Boolean */
	"REL_OR",
	"REL_AND",
	"REL_NOT",
    # /* Bitwise */
	"BIT_OR",
	"BIT_AND",
	"BIT_EXCL_OR",
	"BIT_NOT",
	"RIGHT_SHIFT",
	"LEFT_SHIFT",
    # /* Relationals */
	"NOT_EQ",
	"LESS_THAN",
	"LESS_OR_EQ",
	"EQUAL",
	"GR_OR_EQ",
	"GR_THAN",
    # /* Conditional */
	"COND_IF",
	"COND_ELSE",
	"COND_END",
    # /* Misc */
	"NOT_GENERATED" 
    ]
)
# structure of an element
#    char *name;      /* character representation of an element */
#    char in_stack_pri;     /* priority on translation stack */
#    char in_coming_pri;  /* priority in input string */
#    signed char runtime_effect; /* stack change, positive means push */
#    element_type e_type;     /* element type */
#    rpn_opcode code;     /* postfix opcode */
@dataclass
class element:
    stack_pri : int
    input_pri : int
    stack_effect : int
    e_type : Any        # enum entry
    opcode : Any        # enum entry

# abbreviation follows:
ete = elementTypeEnum
oce = opCodeEnum
operands = {
    # name             prio's    stack    element type    opcode 
    "!"    : element(   7, 8,    0,    ete.UNARY_OPERATOR, oce.REL_NOT ),
    "("    : element(   0, 8,    0,    ete.OPEN_PAREN,    oce.NOT_GENERATED ),
    "-"    : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.UNARY_NEG ),
    "."    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "0"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "1"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "2"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "3"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "4"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "5"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "6"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "7"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "8"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "9"    : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "A"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_A ),
    "ABS"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.ABS_VAL ),
    "ACOS" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.ACOS ),
    "ASIN" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.ASIN ),
    "ATAN" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.ATAN ),
    "ATAN2": element(   7, 8,    -1,   ete.UNARY_OPERATOR,    oce.ATAN2 ),
    "B"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_B ),
    "C"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_C ),
    "CEIL" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.CEIL ),
    "COS"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.COS ),
    "COSH" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.COSH ),
    "D"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_D ),
    "D2R"  : element(   0, 0,    1,    ete.OPERAND,    oce.CONST_D2R ),
    "E"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_E ),
    "EXP"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.EXP ),
    "F"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_F ),
    "FINITE": element(   7, 8,    0,   ete.VARARG_OPERATOR,    oce.FINITE ),
    "FLOOR": element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.FLOOR ),
    "G"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_G ),
    "H"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_H ),
    "I"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_I ),
    "INF"  : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "ISINF": element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.ISINF ),
    "ISNAN": element(   7, 8,    0,    ete.VARARG_OPERATOR,    oce.ISNAN ),
    "J"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_J ),
    "K"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_K ),
    "L"    : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_L ),
    "LN"   : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.LOG_E ),
    "LOG"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.LOG_10 ),
    "LOGE" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.LOG_E ),
    "MAX"  : element(   7, 8,    -1,   ete.VARARG_OPERATOR,    oce.MAX ),
    "MIN"  : element(   7, 8,    -1,   ete.VARARG_OPERATOR,    oce.MIN ),
    "NINT" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.NINT ),
    "NAN"  : element(   0, 0,    1,    ete.LITERAL_OPERAND,oce.LITERAL_DOUBLE ),
    "NOT"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.BIT_NOT ),
    "PI"   : element(   0, 0,    1,    ete.OPERAND,    oce.CONST_PI ),
    "R2D"  : element(   0, 0,    1,    ete.OPERAND,    oce.CONST_R2D ),
    "RNDM" : element(   0, 0,    1,    ete.OPERAND,    oce.RANDOM ),
    "SIN"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.SIN ),
    "SINH" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.SINH ),
    "SQR"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.SQU_RT ),
    "SQRT" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.SQU_RT ),
    "TAN"  : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.TAN ),
    "TANH" : element(   7, 8,    0,    ete.UNARY_OPERATOR,    oce.TANH ),
    "VAL"  : element(   0, 0,    1,    ete.OPERAND,    oce.FETCH_VAL ),
    "~"    : element(   7, 8,    0,    ete.UNARY_OPERATOR, oce.BIT_NOT )
    }

operators = {
    "!="   : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.NOT_EQ  ) ,
    "#"    : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.NOT_EQ  ) ,
    "%"    : element( 5, 5,    -1,    ete.BINARY_OPERATOR,oce.MODULO  ) ,
    "&"    : element( 2, 2,    -1,    ete.BINARY_OPERATOR,oce.BIT_AND  ) ,
    "&&"   : element( 2, 2,    -1,    ete.BINARY_OPERATOR,oce.REL_AND  ) ,
    ")"    : element( 0, 0,    0,     ete.CLOSE_PAREN,    oce.NOT_GENERATED  ) ,
    "*"    : element( 5, 5,    -1,    ete.BINARY_OPERATOR,oce.MULT  ) ,
    "**"   : element( 6, 6,    -1,    ete.BINARY_OPERATOR,oce.POWER  ) ,
    "+"    : element( 4, 4,    -1,    ete.BINARY_OPERATOR,oce.ADD  ) ,
    ","    : element( 0, 0,    0,     ete.SEPERATOR,    oce.NOT_GENERATED  ) ,
    "-"    : element( 4, 4,    -1,    ete.BINARY_OPERATOR,oce.SUB  ) ,
    "/"    : element( 5, 5,    -1,    ete.BINARY_OPERATOR,oce.DIV  ) ,
    ":"    : element( 0, 0,    -1,    ete.CONDITIONAL,    oce.COND_ELSE  ) ,
    "cond-end"    : element( 0, 0,    0, ete.CONDITIONAL,    oce.COND_END  ) ,
    ":="   : element( 0, 0,    -1,    ete.STORE_OPERATOR, oce.STORE_A  ) ,
    ";"    : element( 0, 0,    0,     ete.EXPR_TERMINATOR,oce.NOT_GENERATED  ) ,
    "<"    : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.LESS_THAN  ) ,
    "<<"   : element( 2, 2,    -1,    ete.BINARY_OPERATOR,oce.LEFT_SHIFT  ) ,
    "<="   : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.LESS_OR_EQ  ) ,
    "="    : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.EQUAL  ) ,
    "=="   : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.EQUAL  ) ,
    ">"    : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.GR_THAN  ) ,
    ">="   : element( 3, 3,    -1,    ete.BINARY_OPERATOR,oce.GR_OR_EQ  ) ,
    ">>"   : element( 2, 2,    -1,    ete.BINARY_OPERATOR,oce.RIGHT_SHIFT  ) ,
    "?"    : element( 0, 0,    -1,    ete.CONDITIONAL,    oce.COND_IF  ) ,
    "AND"  : element( 2, 2,    -1,    ete.BINARY_OPERATOR,oce.BIT_AND  ) ,
    "OR"   : element( 1, 1,    -1,    ete.BINARY_OPERATOR,oce.BIT_OR  ) ,
    "XOR"  : element( 1, 1,    -1,    ete.BINARY_OPERATOR,oce.BIT_EXCL_OR  ) ,
    "^"    : element( 6, 6,    -1,    ete.BINARY_OPERATOR,oce.POWER  ) ,
    "|"    : element( 1, 1,    -1,    ete.BINARY_OPERATOR,oce.BIT_OR  ) ,
    "||"   : element( 1, 1,    -1,    ete.BINARY_OPERATOR,oce.REL_OR  ) 
    }
