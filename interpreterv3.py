from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
from element import Element
from copy import copy, deepcopy
import enum


class Type(enum.Enum):
    INT = 1
    STRING = 2
    BOOL = 3
    OBJECT = 4
    VOID = 5
    ERROR = 6

    @staticmethod
    def get_type(var_name):
        if not var_name:
            return Type.ERROR
        last_letter = var_name[-1]
        if last_letter == "i":
            return Type.INT
        if last_letter == "s":
            return Type.STRING
        if last_letter == "b":
            return Type.BOOL
        if last_letter == "o":
            return Type.OBJECT
        if last_letter == "v":
            return Type.VOID  # only for functions
        return Type.ERROR


class Value:
    def __init__(self, t, v=None):
        if v is None:
            self.t = t
            self.v = self.__default_value_for_type(t)
        else:
            self.t = t
            self.v = v

    def set(self, other):
        self.t = other.t
        self.v = other.v

    def __default_value_for_type(self, t):
        if t == Type.INT:
            return 0
        if t == Type.STRING:
            return ""
        elif t == Type.BOOL:
            return False
        elif t == Type.OBJECT:
            return (
                None  # representing Nil as an object type value with None as its value
            )
        elif t == Type.VOID:
            return None

        raise Exception("invalid default value for type")


class Environment:
    def __init__(self):
        self.env = []

    def enter_block(self):
        self.env[-1].append({})

    def exit_block(self):
        self.env[-1].pop()

    def enter_func(self):
        self.env.append([{}])

    def exit_func(self):
        self.env.pop()

    # define new variable at function scope
    def fdef(self, varname, value):
        if self.exists(varname):
            return False
        top_env = self.env[-1]
        top_env[0][varname] = value
        return True

    # define new variable in top block
    def bdef(self, varname, value):
        if self.exists(varname):
            return False
        top_env = self.env[-1]
        top_env[-1][varname] = value
        return True

    def exists(self, varname):
        for block in self.env[-1]:
            if varname in block:
                return True
        return False

    def get(self, varname):
        top_env = self.env[-1]
        for block in top_env:
            if varname in block:
                return block[varname]
        return None

    def set(self, varname, value):
        if not self.exists(varname):
            return False
        top_env = self.env[-1]
        for block in top_env:
            if varname in block:
                block[varname] = value
        return True


class Function:
    def __init__(self, func_ast):
        self.return_type = self.__get_return_type(func_ast)
        # the args in the ast is a list of qualified name nodes
        self.formal_args = {a.get("name"): a.get("ref") for a in func_ast.get("args")}
        self.statements = func_ast.get("statements")

    def __get_return_type(self, func_ast):
        name = func_ast.get("name")
        if name == "main":
            return Type.VOID

        return Type.get_type(name)


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.funcs = {}
        self.env = Environment()
        self.bops = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    def run(self, program):
        ast = parse_program(program)
        self.__create_function_table(ast)
        call_element = Element(InterpreterBase.FCALL_NODE, name="main", args=[])
        self.__run_fcall(call_element)

    def __get_parameters_type_signature(self, formal_params):
        # a formal arg is an Element of type ARG_NODE
        param_type_sig = "".join(p.get("name")[-1] for p in formal_params)
        allowed = "bios"
        if not all(c in allowed for c in param_type_sig):
            super().error(ErrorType.TYPE_ERROR, "invalid type in formal parameter")
        return param_type_sig

    def __get_arguments_type_signature(self, actual_args):
        arg_sig = ""
        for arg in actual_args:
            if arg.t == Type.INT:
                arg_sig += "i"
            elif arg.t == Type.STRING:
                arg_sig += "s"
            elif arg.t == Type.BOOL:
                arg_sig += "b"
            elif arg.t == Type.OBJECT:
                arg_sig += "o"
            elif arg.t == Type.VOID:
                super().error(
                    ErrorType.TYPE_ERROR, "void type not allowed as parameter"
                )
            else:
                raise Exception("shouldn't reach this!")
        return arg_sig

    def __create_function_table(self, ast):
        self.funcs = {}
        valid_types = {"i", "s", "b", "o"}
        for func in ast.get("functions"):
            name = func.get("name")
            param_type_sig = self.__get_parameters_type_signature(func.get("args"))
            func_obj = Function(func)
            if func_obj.return_type == Type.ERROR:
                super().error(ErrorType.TYPE_ERROR)
            type_sig = (name, param_type_sig)
            if type_sig in self.funcs:
                super().error(ErrorType.NAME_ERROR, "function already defined")
            self.funcs[type_sig] = func_obj

    def __get_function(self, name, param_type_signature=""):
        if (name, param_type_signature) not in self.funcs:
            super().error(ErrorType.NAME_ERROR, "function not found")
        return self.funcs[(name, param_type_signature)]

    def __run_vardef(self, statement, block_def=False):
        name = statement.get("name")
        var_type = Type.get_type(name)
        if var_type == Type.ERROR or var_type == Type.VOID:
            super().error(ErrorType.TYPE_ERROR, "invalid variable type")

        default_value = Value(var_type)
        if block_def:
            if not self.env.bdef(name, default_value):
                super().error(ErrorType.NAME_ERROR, "variable already defined")
        else:
            if not self.env.fdef(name, default_value):
                super().error(ErrorType.NAME_ERROR, "variable already defined")

    def __run_assign(self, statement):
        name = statement.get("var")
        dotted_name = name.split(".")
        rvalue = self.eval_expr(statement.get("expression"))

        if not self.env.exists(dotted_name[0]):
            super().error(ErrorType.NAME_ERROR, "variable not defined")

        if Type.get_type(dotted_name[-1]) != rvalue.t:
            super().error(ErrorType.TYPE_ERROR, "type mismatch in assignment")

        if len(dotted_name) == 1:
            value = self.env.get(name)
            value.set(
                rvalue
            )  # update the value pointed to by the variable, not the mapping in the env
            return

        lvalue = self.env.get(dotted_name[0])
        if lvalue.t != Type.OBJECT:
            super().error(ErrorType.TYPE_ERROR, "cannot access member of non-object")
        if lvalue.v == None:
            super().error(ErrorType.FAULT_ERROR, "cannot dereference nil object")

        suffix_name = dotted_name[1:-1]
        # xo.yo.zi = 5;
        for sub in suffix_name:
            if sub not in lvalue.v:
                super().error(ErrorType.NAME_ERROR, "object member not found")
            # every inner item must be an object, ending in an o
            if sub[-1] != "o":
                super().error(ErrorType.TYPE_ERROR, "member must be an object")
            lvalue = lvalue.v[sub]
            # every inner object must be non-nil
            if lvalue.v == None:
                super().error(
                    ErrorType.FAULT_ERROR, "cannot dereference nil member object"
                )

        if rvalue.t == Type.OBJECT:
            lvalue.v[dotted_name[-1]] = rvalue
        else:
            lvalue.v[dotted_name[-1]] = Value(rvalue.t, rvalue.v)

    def __handle_input(self, fcall_name, args):
        """Handle inputi and inputs function calls"""
        if len(args) > 1:
            super().error(ErrorType.NAME_ERROR, "too many arguments for input function")

        if args:
            self.__handle_print(args)

        res = super().get_input()

        return (
            Value(Type.INT, int(res))
            if fcall_name == "inputi"
            else Value(Type.STRING, res)
        )

    def __handle_print(self, args):
        """Handle print function calls"""
        out = ""

        for arg in args:
            c_out = self.eval_expr(arg)
            if c_out.t == Type.VOID:
                super().error(
                    ErrorType.TYPE_ERROR, "cannot pass void argument to function"
                )
            if c_out.t == Type.BOOL:
                out += str(c_out.v).lower()
            else:
                out += str(c_out.v)

        super().output(out)

        return Value(Type.VOID, None)

    def __run_fcall(self, func_call_ast):
        fcall_name, args = func_call_ast.get("name"), func_call_ast.get("args")

        if fcall_name == "inputi" or fcall_name == "inputs":
            return self.__handle_input(fcall_name, args)

        if fcall_name == "print":
            return self.__handle_print(args)

        actual_args = [self.eval_expr(a) for a in args]
        args_type_sig = self.__get_arguments_type_signature(actual_args)
        func_def = self.__get_function(fcall_name, args_type_sig)

        self.env.enter_func()
        for formal, actual in zip(func_def.formal_args.keys(), actual_args):
            ref_param = func_def.formal_args[
                formal
            ]  # determine if it's a reference or not
            actual = self.__clone_for_passing(actual, ref_param)
            self.env.fdef(
                formal, actual
            )  # no need to check types since we used types for overloading to pick a compatible function already
        res, _ = self.__run_statements(func_def, func_def.statements)
        self.env.exit_func()

        return res

    def __clone_for_passing(self, arg, ref_param):
        if ref_param:
            return arg  # pass by reference - value is the original value from the calling function
        return copy(
            arg
        )  # perform a shallow copy of the value, but still point at the original Python value

    def __run_if(self, funcdef, statement):
        cond = self.eval_expr(statement.get("condition"))

        if cond.t != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

        self.env.enter_block()

        res, ret = Value(funcdef.return_type), False

        if cond.v:
            res, ret = self.__run_statements(funcdef, statement.get("statements"))
        elif statement.get("else_statements"):
            res, ret = self.__run_statements(funcdef, statement.get("else_statements"))

        self.env.exit_block()

        return res, ret

    def __run_while(self, funcdef, statement):
        res, ret = Value(funcdef.return_type), False

        while True:
            cond = self.eval_expr(statement.get("condition"))

            if cond.t != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

            if not cond.v:
                break

            self.env.enter_block()
            res, ret = self.__run_statements(funcdef, statement.get("statements"))
            self.env.exit_block()
            if ret:
                break

        return res, ret

    def __run_return(self, funcdef, statement):
        expr = statement.get("expression")
        if not expr:
            return (Value(funcdef.return_type), True)
        result_val = self.eval_expr(expr)
        if result_val.t != funcdef.return_type:
            super().error(ErrorType.TYPE_ERROR, "return type mismatch")
        return (result_val, True)

    def __run_statements(self, funcdef, statements):
        res, ret = Value(funcdef.return_type), False

        for statement in statements:
            kind = statement.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
            if kind == self.BVAR_DEF_NODE:
                self.__run_vardef(statement, True)
            elif kind == "=":
                self.__run_assign(statement)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(statement)
            elif kind == self.IF_NODE:
                res, ret = self.__run_if(funcdef, statement)
                if ret:
                    break
            elif kind == self.WHILE_NODE:
                res, ret = self.__run_while(funcdef, statement)
                if ret:
                    break
            elif kind == self.RETURN_NODE:
                res, ret = self.__run_return(funcdef, statement)
                break

        return res, ret

    def __eval_binary_op(self, kind, vl, vr):
        """Evaluate binary operations"""
        tl, tr = vl.t, vr.t
        vl_val, vr_val = vl.v, vr.v

        if kind == "==":
            if tl == Type.OBJECT and tr == Type.OBJECT:
                return Value(Type.BOOL, tl == tr and vl_val is vr_val)
            return Value(Type.BOOL, tl == tr and vl_val == vr_val)
        if kind == "!=":
            if tl == Type.OBJECT and tr == Type.OBJECT:
                return Value(Type.BOOL, not (tl == tr and vl_val is vr_val))
            return Value(Type.BOOL, not (tl == tr and vl_val == vr_val))

        if tl == Type.STRING and tr == Type.STRING:
            if kind == "+":
                return Value(Type.STRING, vl_val + vr_val)

        if tl == Type.INT and tr == Type.INT:
            if kind == "+":
                return Value(Type.INT, vl_val + vr_val)
            if kind == "-":
                return Value(Type.INT, vl_val - vr_val)
            if kind == "*":
                return Value(Type.INT, vl_val * vr_val)
            if kind == "/":
                return Value(Type.INT, vl_val // vr_val)
            if kind == "<":
                return Value(Type.BOOL, vl_val < vr_val)
            if kind == "<=":
                return Value(Type.BOOL, vl_val <= vr_val)
            if kind == ">":
                return Value(Type.BOOL, vl_val > vr_val)
            if kind == ">=":
                return Value(Type.BOOL, vl_val >= vr_val)

        if tl == Type.BOOL and tr == Type.BOOL:
            if kind == "&&":
                return Value(Type.BOOL, vl_val and vr_val)
            if kind == "||":
                return Value(Type.BOOL, vl_val or vr_val)

        super().error(ErrorType.TYPE_ERROR, "invalid binary operation")

    def __eval_convert(self, expr):
        """Evaluate type conversion operations"""
        val = self.eval_expr(expr.get("expr"))
        to_type = expr.get("to_type")

        if to_type == "int":
            if val.t == Type.INT:
                return val
            elif val.t == Type.STRING:
                try:
                    return Value(Type.INT, int(val.v))
                except ValueError:
                    super().error(ErrorType.TYPE_ERROR, "cannot convert string to int")
            elif val.t == Type.BOOL:
                return Value(Type.INT, 1 if val.v else 0)
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot convert object to int")

        elif to_type == "str":
            if val.t == Type.STRING:
                return val
            elif val.t == Type.INT:
                return Value(Type.STRING, str(val.v))
            elif val.t == Type.BOOL:
                return Value(Type.STRING, str(val.v).lower())
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot convert object to string")

        elif to_type == "bool":
            if val.t == Type.BOOL:
                return val
            elif val.t == Type.INT:
                return Value(Type.BOOL, val.v != 0)
            elif val.t == Type.STRING:
                return Value(Type.BOOL, val.v != "")
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot convert object to bool")
        else:
            super().error(ErrorType.TYPE_ERROR, "invalid conversion type")

    def __get_var_value(self, expr):
        dotted_name = expr.get("name").split(".")

        if not self.env.exists(dotted_name[0]):
            super().error(ErrorType.NAME_ERROR, "variable not defined")
        value = self.env.get(dotted_name[0])
        suffix_name = dotted_name[1:]
        if len(dotted_name) > 1 and dotted_name[0][-1] != "o":
            super().error(ErrorType.TYPE_ERROR, "cannot dereference a non-object")
        for i, sub in enumerate(suffix_name):
            if value.v == None:  # NIL
                super().error(ErrorType.FAULT_ERROR, "nil reference access")
            if sub not in value.v:
                super().error(ErrorType.NAME_ERROR, "object member not found")
            # every inner item must be an object, ending in an o
            if i < len(suffix_name) - 1 and sub[-1] != "o":
                super().error(ErrorType.TYPE_ERROR, "member must be an object")
            value = value.v[sub]
        return value

    def eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE:
            return Value(Type.INT, expr.get("val"))

        if kind == self.STRING_NODE:
            return Value(Type.STRING, expr.get("val"))

        if kind == self.BOOL_NODE:
            return Value(Type.BOOL, expr.get("val"))

        if kind == self.NIL_NODE:
            return Value(Type.OBJECT)

        if kind == self.EMPTY_OBJ_NODE:
            return Value(Type.OBJECT, {})

        if kind == self.QUALIFIED_NAME_NODE:
            return self.__get_var_value(expr)

        if kind == self.FCALL_NODE:
            return self.__run_fcall(expr)

        if kind in self.bops:
            l, r = self.eval_expr(expr.get("op1")), self.eval_expr(expr.get("op2"))
            return self.__eval_binary_op(kind, l, r)

        if kind == self.NEG_NODE:
            o = self.eval_expr(expr.get("op1"))
            if o.t == Type.INT:
                return Value(Type.INT, -o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot negate non-integer")

        if kind == self.NOT_NODE:
            o = self.eval_expr(expr.get("op1"))
            if o.t == Type.BOOL:
                return Value(Type.BOOL, not o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot apply NOT to non-boolean")

        if kind == self.CONVERT_NODE:
            return self.__eval_convert(expr)

        raise Exception("should not get here!")


def main():
    import sys

    interpreter = Interpreter()

    # Use command line argument if provided, otherwise default to test.br
    filename = sys.argv[1] if len(sys.argv) > 1 else "./test.br"

    with open(filename, "r") as f:
        program = f.read()

    interpreter.run(program)


if __name__ == "__main__":
    main()
