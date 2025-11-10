from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import enum


class Type(enum.Enum):
    NIL = 0
    INT = 1
    STRING = 2
    BOOL = 3


class Value:
    def __init__(self, t=None, v=None):
        if t is None:
            self.t = Type.NIL
            self.v = None
        else:
            self.t = t
            self.v = v


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
    def fdef(self, varname):
        if self.exists(varname):
            return False
        top_env = self.env[-1]
        top_env[0][varname] = Value()
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


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.funcs = {}
        self.env = Environment()
        self.bops = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    def run(self, program):
        ast = parse_program(program)
        self.__create_function_table(ast)
        self.__run_fcall(self.__get_function("main"))

    def __create_function_table(self, ast):
        self.funcs = {}
        for func in ast.get("functions"):
            self.funcs[(func.get("name"), len(func.get("args")))] = func

    def __get_function(self, name, num_params=0):
        if (name, num_params) not in self.funcs:
            super().error(ErrorType.NAME_ERROR, "function not found")
        return self.funcs[(name, num_params)]

    def __run_vardef(self, statement):
        name = statement.get("name")

        if not self.env.fdef(name):
            super().error(ErrorType.NAME_ERROR, "variable already defined")

    def __run_assign(self, statement):
        name = statement.get("var")

        value = self.__eval_expr(statement.get("expression"))
        if not self.env.set(name, value):
            super().error(ErrorType.NAME_ERROR, "variable not defined")

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
            c_out = self.__eval_expr(arg)
            if c_out.t == Type.BOOL:
                out += str(c_out.v).lower()
            else:
                out += str(c_out.v)

        super().output(out)

        return Value(Type.NIL, None)

    def __run_fcall(self, func_call_ast):
        fcall_name, args = func_call_ast.get("name"), func_call_ast.get("args")

        if fcall_name == "inputi" or fcall_name == "inputs":
            return self.__handle_input(fcall_name, args)

        if fcall_name == "print":
            return self.__handle_print(args)

        func_def = self.__get_function(fcall_name, len(args))

        formal_args = [a.get("name") for a in func_def.get("args")]
        actual_args = [self.__eval_expr(a) for a in args]

        self.env.enter_func()
        for formal, actual in zip(formal_args, actual_args):
            self.env.fdef(formal)
            self.env.set(formal, actual)
        res, _ = self.__run_statements(func_def.get("statements"))
        self.env.exit_func()

        return res

    def __run_if(self, statement):
        cond = self.__eval_expr(statement.get("condition"))

        if cond.t != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

        self.env.enter_block()

        res, ret = None, False

        if cond.v:
            res, ret = self.__run_statements(statement.get("statements"))
        elif statement.get("else_statements"):
            res, ret = self.__run_statements(statement.get("else_statements"))

        self.env.exit_block()

        return res, ret

    def __run_while(self, statement):
        res, ret = Value(), False

        while True:
            cond = self.__eval_expr(statement.get("condition"))

            if cond.t != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

            if not cond.v:
                break

            self.env.enter_block()
            res, ret = self.__run_statements(statement.get("statements"))
            self.env.exit_block()
            if ret:
                break

        return res, ret

    def __run_return(self, statement):
        expr = statement.get("expression")
        if expr:
            return (self.__eval_expr(expr), True)
        return (Value(), True)

    def __run_statements(self, statements):
        res, ret = Value(), False

        for statement in statements:
            kind = statement.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
            elif kind == "=":
                self.__run_assign(statement)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(statement)
            elif kind == self.IF_NODE:
                res, ret = self.__run_if(statement)
                if ret:
                    break
            elif kind == self.WHILE_NODE:
                res, ret = self.__run_while(statement)
                if ret:
                    break
            elif kind == self.RETURN_NODE:
                res, ret = self.__run_return(statement)
                break

        return res, ret

    def __eval_binary_op(self, kind, vl, vr):
        """Evaluate binary operations"""
        tl, tr = vl.t, vr.t
        vl_val, vr_val = vl.v, vr.v

        if kind == "==":
            return Value(Type.BOOL, tl == tr and vl_val == vr_val)
        if kind == "!=":
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

    def __eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE:
            return Value(Type.INT, expr.get("val"))

        if kind == self.STRING_NODE:
            return Value(Type.STRING, expr.get("val"))

        if kind == self.BOOL_NODE:
            return Value(Type.BOOL, expr.get("val"))

        if kind == self.NIL_NODE:
            return Value(Type.NIL, None)

        if kind == self.QUALIFIED_NAME_NODE:
            var_name = expr.get("name")

            if not self.env.exists(var_name):
                super().error(ErrorType.NAME_ERROR, "variable not defined")
            return self.env.get(var_name)

        if kind == self.FCALL_NODE:
            return self.__run_fcall(expr)

        if kind in self.bops:
            l, r = self.__eval_expr(expr.get("op1")), self.__eval_expr(expr.get("op2"))
            return self.__eval_binary_op(kind, l, r)

        if kind == self.NEG_NODE:
            o = self.__eval_expr(expr.get("op1"))
            if o.t == Type.INT:
                return Value(Type.INT, -o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot negate non-integer")

        if kind == self.NOT_NODE:
            o = self.__eval_expr(expr.get("op1"))
            if o.t == Type.BOOL:
                return Value(Type.BOOL, not o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot apply NOT to non-boolean")

        raise Exception("should not get here!")


def main():
    interpreter = Interpreter()

    # To test your own Brewin program, place it in `test.br` and run this main function.
    with open("./test.br", "r") as f:
        program = f.read()

    interpreter.run(program)


if __name__ == "__main__":
    main()
