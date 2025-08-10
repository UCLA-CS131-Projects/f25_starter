from element import Element
from brewlex import *
from intbase import InterpreterBase
from ply import yacc

# Parsing rules

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("left", "GREATER_EQ", "GREATER", "LESS_EQ", "LESS", "EQ", "NOT_EQ"),
    ("left", "PLUS", "MINUS"),
    ("left", "MULTIPLY", "DIVIDE"),
    ("right", "UMINUS", "NOT"),
)


def collapse_items(p, group_index, singleton_index):
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[group_index]
        p[0].append(p[singleton_index])


def p_program(p):
    """program : interfaces funcs
    | funcs"""
    if len(p) == 3:
        p[0] = Element(InterpreterBase.PROGRAM_NODE, interfaces=p[1], functions=p[2])
    else:
        p[0] = Element(InterpreterBase.PROGRAM_NODE, functions=p[1])

def p_interfaces(p):
    """interfaces : interfaces interface
    | interface"""
    collapse_items(p,1,2) #2 -> interface

def p_interface(p):
    "interface : INTERFACE NAME LBRACE fields RBRACE"
    p[0] = Element(InterpreterBase.INTERFACE_NODE, name=p[2], fields=p[4])

def p_fields(p):
    """fields : fields field
    | field"""
    collapse_items(p, 1, 2)  # 2 -> field

def p_field(p):
    """field : field_function
    | field_variable"""
    p[0] = p[1]

def p_field_function(p):
    """field_function : NAME LPAREN formal_args RPAREN SEMI
    | NAME LPAREN RPAREN SEMI"""
    if len(p) == 6:  # with parameters
        p[0] = Element(InterpreterBase.FIELD_FUNC_NODE, name=p[1], params=p[3])
    else:  # no parameters
        p[0] = Element(InterpreterBase.FIELD_FUNC_NODE, name=p[1], params=[])

def p_field_variable(p):
    "field_variable : NAME SEMI"
    p[0] = Element(InterpreterBase.FIELD_VAR_NODE, name=p[1])


def p_funcs(p):
    """funcs : funcs func
    | func"""
    collapse_items(p, 1, 2)  # 2 -> func

def p_func(p):
    """func : DEF NAME LPAREN formal_args RPAREN LBRACE statements RBRACE
    | DEF NAME LPAREN RPAREN LBRACE statements RBRACE"""
    if len(p) == 9:  # handle with 1+ formal args
        p[0] = Element(InterpreterBase.FUNC_NODE, name=p[2], args=p[4], statements=p[7])
    else:  # handle no formal args
        p[0] = Element(InterpreterBase.FUNC_NODE, name=p[2], args=[], statements=p[6])

def p_formal_args(p):
    """formal_args : formal_args COMMA formal_arg
    | formal_arg"""
    collapse_items(p, 1, 3)  # 3 -> formal_arg

def p_formal_arg(p):
    """formal_arg : NAME
    | AMP NAME"""
    if len(p) == 2:  # NAME only
        p[0] = Element(InterpreterBase.ARG_NODE, name=p[1], ref=False)
    else:  # AMP NAME
        p[0] = Element(InterpreterBase.ARG_NODE, name=p[2], ref=True)

def p_statements(p):
    """statements : statements statement
    | statement"""
    collapse_items(p, 1, 2)  # 3 -> formal_arg


def p_statement___assign(p):
    "statement : assign SEMI"
    p[0] = p[1]

def p_assign(p):
    "assign : qualified_name ASSIGN expression"
    p[0] = Element("=", var=p[1], expression=p[3])

def p_statement___fvar(p):
    "statement : VAR qualified_name_no_dot SEMI" 
    p[0] = Element(InterpreterBase.VAR_DEF_NODE, name=p[2])

def p_statement___bvar(p):
    "statement : BVAR qualified_name_no_dot SEMI"    
    p[0] = Element(InterpreterBase.BVAR_DEF_NODE, name=p[2])

def p_qualified_name(p):
    """qualified_name : qualified_name DOT NAME
    | NAME"""
    if len(p) == 4:
        p[0] = p[1] + "." + p[3]
    else:
        p[0] = p[1]

def p_qualified_name_no_dot(p):
    """qualified_name_no_dot : NAME"""
    p[0] = p[1] 

def p_statement_if(p):
    """statement : IF LPAREN expression RPAREN LBRACE statements RBRACE
    | IF LPAREN expression RPAREN LBRACE statements RBRACE ELSE LBRACE statements RBRACE
    """
    if len(p) == 8:
        p[0] = Element(
            InterpreterBase.IF_NODE,
            condition=p[3],
            statements=p[6],
            else_statements=None,
        )
    else:
        p[0] = Element(
            InterpreterBase.IF_NODE,
            condition=p[3],
            statements=p[6],
            else_statements=p[10],
        )

def p_statement_while(p):
    "statement : WHILE LPAREN expression RPAREN LBRACE statements RBRACE"
    p[0] = Element(InterpreterBase.WHILE_NODE, condition=p[3], statements=p[6])


def p_statement_expr(p):
    "statement : expression SEMI"
    p[0] = p[1]


def p_statement_return(p):
    """statement : RETURN expression SEMI
    | RETURN SEMI"""
    if len(p) == 4:
        expr = p[2]
    else:
        expr = None
    p[0] = Element(InterpreterBase.RETURN_NODE, expression=expr)


def p_expression_not(p):
    "expression : NOT expression"
    p[0] = Element(InterpreterBase.NOT_NODE, op1=p[2])


def p_expression_uminus(p):
    "expression : MINUS expression %prec UMINUS"
    p[0] = Element(InterpreterBase.NEG_NODE, op1=p[2])


def p_expression_int(p):
    "expression : INT LPAREN expression RPAREN"
    p[0] = Element(InterpreterBase.CONVERT_NODE, to_type = "int", expr=p[3])

def p_expression_string(p):
    "expression : STR LPAREN expression RPAREN"
    p[0] = Element(InterpreterBase.CONVERT_NODE, to_type = "str", expr=p[3])

def p_expression_bool(p):
    "expression : BOOL LPAREN expression RPAREN"
    p[0] = Element(InterpreterBase.CONVERT_NODE, to_type = "bool", expr=p[3])

def p_arith_expression_binop(p):
    """expression : expression EQ expression
    | expression GREATER expression
    | expression LESS expression
    | expression NOT_EQ expression
    | expression GREATER_EQ expression
    | expression LESS_EQ expression
    | expression PLUS expression
    | expression MINUS expression
    | expression MULTIPLY expression
    | expression DIVIDE expression"""
    p[0] = Element(p[2], op1=p[1], op2=p[3])


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_and_or(p):
    """expression : expression OR expression
    | expression AND expression"""
    p[0] = Element(p[2], op1=p[1], op2=p[3])


def p_expression_number(p):
    "expression : NUMBER"
    p[0] = Element(InterpreterBase.INT_NODE, val=p[1])


def p_expression_bool_literal(p):
    """expression : TRUE
    | FALSE"""
    bool_val = p[1] == InterpreterBase.TRUE_DEF
    p[0] = Element(InterpreterBase.BOOL_NODE, val=bool_val)


def p_expression_string_literal(p):
    "expression : STRING"
    p[0] = Element(InterpreterBase.STRING_NODE, val=p[1])


def p_expression_closure(p):
    "expression : CLOSURE NAME"
    p[0] = Element(InterpreterBase.CLOSURE_NODE, args=p[2])

def p_expression_empty_obj(p):
    "expression : AT"
    p[0] = Element(InterpreterBase.EMPTY_OBJ_NODE)

def p_expression_nil(p):
    "expression : NIL"
    p[0] = Element(InterpreterBase.NIL_NODE)

def p_func_call(p):
    """expression : qualified_name LPAREN args RPAREN
    | qualified_name LPAREN RPAREN"""
    if len(p) == 5:
        p[0] = Element(InterpreterBase.FCALL_NODE, name=p[1], args=p[3])
    else:
        p[0] = Element(InterpreterBase.FCALL_NODE, name=p[1], args=[])


def p_expression_variable(p):
    "expression : qualified_name"
    p[0] = Element(InterpreterBase.QUALIFIED_NAME_NODE, name=p[1])


def p_expression_args(p):
    """args : args COMMA expression
    | expression"""
    collapse_items(p, 1, 3)

# lanbmdab, lambdai, lambdav, lamnbdaf, etc.
def p_expression_lambda(p):
    """expression : LAMBDA LPAREN formal_args RPAREN LBRACE statements RBRACE
    | LAMBDA LPAREN RPAREN LBRACE statements RBRACE"""
    if len(p) == 8:
         p[0] = Element(InterpreterBase.FUNC_NODE, name=p[1], args=p[3], statements=p[6])
    else:
        p[0] = Element(InterpreterBase.FUNC_NODE, name=p[1], args=[], statements=p[5])


def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' on line {p.lineno}")
    else:
        print("Syntax error at EOF")


# exported function
def parse_program(program, plot = False):
    reset_lineno()
    ast = yacc.parse(program)
    if ast is None:
        raise SyntaxError("Syntax error")
    
    # Plot the AST if requested
    if plot:
        from plot import plot_ast
        plot_ast(ast)
    
    return ast


# generate our parser
yacc.yacc() # yacc.yacc(debug=True, debuglog=open("parse.log", "w"))
