# Copyright 2011 Canadian Light Source, Inc. See The file COPYRIGHT in this distribution for further information.
#/* element types */
(OPERAND, LITERAL_OPERAND, STORE_OPERATOR, UNARY_OPERATOR, VARARG_OPERATOR, BINARY_OPERATOR, SEPERATOR,
    OPEN_PAREN, CLOSE_PAREN, CONDITIONAL, EXPR_TERMINATOR) = range(1,12)


(	END_EXPRESSION,
    # /* Operands */
	LITERAL_DOUBLE, LITERAL_INT, FETCH_VAL,
	FETCH_A, FETCH_B, FETCH_C, FETCH_D, FETCH_E, FETCH_F,
	FETCH_G, FETCH_H, FETCH_I, FETCH_J, FETCH_K, FETCH_L,
    # /* Assignment */
	STORE_A, STORE_B, STORE_C, STORE_D, STORE_E, STORE_F,
	STORE_G, STORE_H, STORE_I, STORE_J, STORE_K, STORE_L,
    # /* Trigonometry Constants */
	CONST_PI,
	CONST_D2R,
	CONST_R2D,
    # /* Arithmetic */
	UNARY_NEG,
	ADD,
	SUB,
	MULT,
	DIV,
	MODULO,
	POWER,
    # /* Algebraic */
	ABS_VAL,
	EXP,
	LOG_10,
	LOG_E,
	MAX,
	MIN,
	SQU_RT,
    # /* Trigonometric */
	ACOS,
	ASIN,
	ATAN,
	ATAN2,
	COS,
	COSH,
	SIN,
	SINH,
	TAN,
	TANH,
    # /* Numeric */
	CEIL,
	FLOOR,
	FINITE,
	ISINF,
	ISNAN,
	NINT,
	RANDOM,
    # /* Boolean */
	REL_OR,
	REL_AND,
	REL_NOT,
    # /* Bitwise */
	BIT_OR,
	BIT_AND,
	BIT_EXCL_OR,
	BIT_NOT,
	RIGHT_SHIFT,
	LEFT_SHIFT,
    # /* Relationals */
	NOT_EQ,
	LESS_THAN,
	LESS_OR_EQ,
	EQUAL,
	GR_OR_EQ,
	GR_THAN,
    # /* Conditional */
	COND_IF,
	COND_ELSE,
	COND_END,
    # /* Misc */
	NOT_GENERATED ) = range(0,81)
# structure of an element
#    char *name;      /* character representation of an element */
#    char in_stack_pri;     /* priority on translation stack */
#    char in_coming_pri;  /* priority in input string */
#    signed char runtime_effect; /* stack change, positive means push */
#    element_type type;     /* element type */
#    rpn_opcode code;     /* postfix opcode */
class element:
    def __init__(self, stack_pri, input_pri, stack_effect, type, opcode):
        self.stack_pri = stack_pri
        self.input_pri = input_pri
        self.stack_effect = stack_effect
        self.type = type
        self.opcode = opcode

operands = {
    # name     prio's    stack    element type    opcode 
    "!"    : element(   7, 8,    0,    UNARY_OPERATOR, REL_NOT ),
    "("    : element(   0, 8,    0,    OPEN_PAREN,    NOT_GENERATED ),
    "-"    : element(   7, 8,    0,    UNARY_OPERATOR,    UNARY_NEG ),
    "."    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "0"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "1"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "2"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "3"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "4"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "5"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "6"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "7"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "8"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "9"    : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "A"    : element(   0, 0,    1,    OPERAND,    FETCH_A ),
    "ABS"  : element(   7, 8,    0,    UNARY_OPERATOR,    ABS_VAL ),
    "ACOS" : element(   7, 8,    0,    UNARY_OPERATOR,    ACOS ),
    "ASIN" : element(   7, 8,    0,    UNARY_OPERATOR,    ASIN ),
    "ATAN" : element(   7, 8,    0,    UNARY_OPERATOR,    ATAN ),
    "ATAN2": element(   7, 8,    -1,   UNARY_OPERATOR,    ATAN2 ),
    "B"    : element(   0, 0,    1,    OPERAND,    FETCH_B ),
    "C"    : element(   0, 0,    1,    OPERAND,    FETCH_C ),
    "CEIL" : element(   7, 8,    0,    UNARY_OPERATOR,    CEIL ),
    "COS"  : element(   7, 8,    0,    UNARY_OPERATOR,    COS ),
    "COSH" : element(   7, 8,    0,    UNARY_OPERATOR,    COSH ),
    "D"    : element(   0, 0,    1,    OPERAND,    FETCH_D ),
    "D2R"  : element(   0, 0,    1,    OPERAND,    CONST_D2R ),
    "E"    : element(   0, 0,    1,    OPERAND,    FETCH_E ),
    "EXP"  : element(   7, 8,    0,    UNARY_OPERATOR,    EXP ),
    "F"    : element(   0, 0,    1,    OPERAND,    FETCH_F ),
    "FINITE": element(   7, 8,    0,   VARARG_OPERATOR,    FINITE ),
    "FLOOR": element(   7, 8,    0,    UNARY_OPERATOR,    FLOOR ),
    "G"    : element(   0, 0,    1,    OPERAND,    FETCH_G ),
    "H"    : element(   0, 0,    1,    OPERAND,    FETCH_H ),
    "I"    : element(   0, 0,    1,    OPERAND,    FETCH_I ),
    "INF"  : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "ISINF": element(   7, 8,    0,    UNARY_OPERATOR,    ISINF ),
    "ISNAN": element(   7, 8,    0,    VARARG_OPERATOR,    ISNAN ),
    "J"    : element(   0, 0,    1,    OPERAND,    FETCH_J ),
    "K"    : element(   0, 0,    1,    OPERAND,    FETCH_K ),
    "L"    : element(   0, 0,    1,    OPERAND,    FETCH_L ),
    "LN"   : element(   7, 8,    0,    UNARY_OPERATOR,    LOG_E ),
    "LOG"  : element(   7, 8,    0,    UNARY_OPERATOR,    LOG_10 ),
    "LOGE" : element(   7, 8,    0,    UNARY_OPERATOR,    LOG_E ),
    "MAX"  : element(   7, 8,    -1,   VARARG_OPERATOR,    MAX ),
    "MIN"  : element(   7, 8,    -1,   VARARG_OPERATOR,    MIN ),
    "NINT" : element(   7, 8,    0,    UNARY_OPERATOR,    NINT ),
    "NAN"  : element(   0, 0,    1,    LITERAL_OPERAND,LITERAL_DOUBLE ),
    "NOT"  : element(   7, 8,    0,    UNARY_OPERATOR,    BIT_NOT ),
    "PI"   : element(   0, 0,    1,    OPERAND,    CONST_PI ),
    "R2D"  : element(   0, 0,    1,    OPERAND,    CONST_R2D ),
    "RNDM" : element(   0, 0,    1,    OPERAND,    RANDOM ),
    "SIN"  : element(   7, 8,    0,    UNARY_OPERATOR,    SIN ),
    "SINH" : element(   7, 8,    0,    UNARY_OPERATOR,    SINH ),
    "SQR"  : element(   7, 8,    0,    UNARY_OPERATOR,    SQU_RT ),
    "SQRT" : element(   7, 8,    0,    UNARY_OPERATOR,    SQU_RT ),
    "TAN"  : element(   7, 8,    0,    UNARY_OPERATOR,    TAN ),
    "TANH" : element(   7, 8,    0,    UNARY_OPERATOR,    TANH ),
    "VAL"  : element(   0, 0,    1,    OPERAND,    FETCH_VAL ),
    "~"    : element(   7, 8,    0,    UNARY_OPERATOR, BIT_NOT )
    }

operators = {
    "!="   : element( 3, 3,    -1,    BINARY_OPERATOR,NOT_EQ  ) ,
    "#"    : element( 3, 3,    -1,    BINARY_OPERATOR,NOT_EQ  ) ,
    "%"    : element( 5, 5,    -1,    BINARY_OPERATOR,MODULO  ) ,
    "&"    : element( 2, 2,    -1,    BINARY_OPERATOR,BIT_AND  ) ,
    "&&"   : element( 2, 2,    -1,    BINARY_OPERATOR,REL_AND  ) ,
    ")"    : element( 0, 0,    0,    CLOSE_PAREN,    NOT_GENERATED  ) ,
    "*"    : element( 5, 5,    -1,    BINARY_OPERATOR,MULT  ) ,
    "**"   : element( 6, 6,    -1,    BINARY_OPERATOR,POWER  ) ,
    "+"    : element( 4, 4,    -1,    BINARY_OPERATOR,ADD  ) ,
    ","    : element( 0, 0,    0,    SEPERATOR,    NOT_GENERATED  ) ,
    "-"    : element( 4, 4,    -1,    BINARY_OPERATOR,SUB  ) ,
    "/"    : element( 5, 5,    -1,    BINARY_OPERATOR,DIV  ) ,
    ":"    : element( 0, 0,    -1,    CONDITIONAL,    COND_ELSE  ) ,
    "cond-end"    : element( 0, 0,    0,    CONDITIONAL,    COND_END  ) ,
    ":="   : element( 0, 0,    -1,    STORE_OPERATOR, STORE_A  ) ,
    ";"    : element( 0, 0,    0,    EXPR_TERMINATOR,NOT_GENERATED  ) ,
    "<"    : element( 3, 3,    -1,    BINARY_OPERATOR,LESS_THAN  ) ,
    "<<"   : element( 2, 2,    -1,    BINARY_OPERATOR,LEFT_SHIFT  ) ,
    "<="   : element( 3, 3,    -1,    BINARY_OPERATOR,LESS_OR_EQ  ) ,
    "="    : element( 3, 3,    -1,    BINARY_OPERATOR,EQUAL  ) ,
    "=="   : element( 3, 3,    -1,    BINARY_OPERATOR,EQUAL  ) ,
    ">"    : element( 3, 3,    -1,    BINARY_OPERATOR,GR_THAN  ) ,
    ">="   : element( 3, 3,    -1,    BINARY_OPERATOR,GR_OR_EQ  ) ,
    ">>"   : element( 2, 2,    -1,    BINARY_OPERATOR,RIGHT_SHIFT  ) ,
    "?"    : element( 0, 0,    -1,    CONDITIONAL,    COND_IF  ) ,
    "AND"  : element( 2, 2,    -1,    BINARY_OPERATOR,BIT_AND  ) ,
    "OR"   : element( 1, 1,    -1,    BINARY_OPERATOR,BIT_OR  ) ,
    "XOR"  : element( 1, 1,    -1,    BINARY_OPERATOR,BIT_EXCL_OR  ) ,
    "^"    : element( 6, 6,    -1,    BINARY_OPERATOR,POWER  ) ,
    "|"    : element( 1, 1,    -1,    BINARY_OPERATOR,BIT_OR  ) ,
    "||"   : element( 1, 1,    -1,    BINARY_OPERATOR,REL_OR  ) 
    }
