# Base class for our interpreter
from enum import Enum


class ErrorType(Enum):
    TYPE_ERROR = 1
    NAME_ERROR = 2  # if a variable or function name can't be found
    FAULT_ERROR = 3  # used if an object reference is null and used to make a call
    # Add others here


class InterpreterBase:
    # AST node types
    PROGRAM_NODE = "program"
    FUNC_NODE = "func"
    NIL_NODE = "nil"
    IF_NODE = "if"
    WHILE_NODE = "while"
    ARG_NODE = "arg"
    NEG_NODE = "neg"
    RETURN_NODE = "return"
    INT_NODE = "int"
    BOOL_NODE = "bool"
    STRING_NODE = "string"
    FCALL_NODE = "fcall"
    QUALIFIED_NAME_NODE = "qname"   # var_name, var1.var2.var3, funcname
    NOT_NODE = "!"
    VAR_DEF_NODE = "vardef"
    BVAR_DEF_NODE = "bvardef"
    CLONE_NODE = "clone"
    CLOSURE_NODE = "closure"
    CONVERT_NODE = "convert"
    EMPTY_OBJ_NODE = "@"
    INTERFACE_NODE = "interface"
    FIELD_FUNC_NODE = "field_func"
    FIELD_VAR_NODE = "field_var"

    # other constants
    TRUE_DEF = "true"
    FALSE_DEF = "false"
    NIL_DEF = "nil"
    
    # methods
    def __init__(self, console_output=True, inp=None):
        self.console_output = console_output
        self.inp = inp  # if not none, then read input from passed-in list
        self.reset()

    # Call to reset I/O for another run of the program
    def reset(self):
        self.output_log = []
        self.input_cursor = 0
        self.error_type = None
        self.error_line = None

    # Students must implement this in their derived class
    def run(self, program):
        pass

    def get_input(self):
        if not self.inp:
            return input()  # Get input from keyboard if not input list provided

        if self.input_cursor < len(self.inp):
            cur_input = self.inp[self.input_cursor]
            self.input_cursor += 1
            return cur_input
        return None

    # students must call this for any errors that they run into
    def error(self, error_type, description=None, line_num=None):
        # log the error before we throw
        self.error_line = line_num
        self.error_type = error_type

        if description:
            description = ": " + description
        else:
            description = ""
        if not line_num:
            raise Exception(f"{error_type}{description}")
        raise Exception(f"{error_type} on line {line_num}{description}")

    def output(self, v):
        if self.console_output:
            print(v)
        self.output_log.append(v)

    def get_output(self):
        return self.output_log

    def get_error_type_and_line(self):
        return self.error_type, self.error_line
