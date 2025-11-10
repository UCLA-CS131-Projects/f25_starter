from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

generate_image = False


class Environment:
    def __init__(self):
        self.env = {}

    # define new variable at function scope
    def fdef(self, varname):
        if self.exists(varname):
            return False
        self.env[varname] = None
        return True

    def exists(self, varname):
        return varname in self.env

    def get(self, varname):
        if varname in self.env:
            return self.env[varname]
        return None

    def set(self, varname, value):
        if not self.exists(varname):
            return False
        self.env[varname] = value
        return True


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)

        self.funcs = {}  # {name:element,}
        self.env = Environment()
        self.ops = {"-", "+"}

    def run(self, program):
        ast = parse_program(program, generate_image)

        for func in ast.get("functions"):
            self.funcs[func.get("name")] = func

        if "main" not in self.funcs:
            super().error(ErrorType.NAME_ERROR, "main function not found")

        for statement in self.funcs["main"].get("statements"):
            kind = statement.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
            elif kind == "=":
                self.__run_assign(statement)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(statement)

    def __run_vardef(self, statement):
        name = statement.get("name")

        if not self.env.fdef(name):
            super().error(ErrorType.NAME_ERROR, "variable already defined")

    def __run_assign(self, statement):
        name = statement.get("var")

        value = self.__eval_expr(statement.get("expression"))
        if not self.env.set(name, value):
            super().error(ErrorType.NAME_ERROR, "variable not defined")

    def __run_fcall(self, statement):
        fcall_name, args = statement.get("name"), statement.get("args")

        if fcall_name == "inputi":
            if len(args) > 1:
                super().error(ErrorType.NAME_ERROR, "too many arguments for inputi")

            if args:
                super().output(str(self.__eval_expr(args[0])))

            return int(super().get_input())

        if fcall_name == "print":
            out = ""

            for arg in args:
                out += str(self.__eval_expr(arg))

            super().output(out)

            return 0  # undefined behavior

        super().error(ErrorType.NAME_ERROR, "unknown function")

    def __eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE or kind == self.STRING_NODE:
            return expr.get("val")

        elif kind == self.QUALIFIED_NAME_NODE:
            var_name = expr.get("name")

            value = self.env.get(var_name)
            if value is None:
                super().error(ErrorType.NAME_ERROR, "variable not defined")

            return value

        elif kind == self.FCALL_NODE:
            return self.__run_fcall(expr)

        elif kind in self.ops:
            l, r = self.__eval_expr(expr.get("op1")), self.__eval_expr(expr.get("op2"))

            if isinstance(l, str) or isinstance(r, str):
                super().error(
                    ErrorType.TYPE_ERROR, "invalid operand types for arithmetic"
                )

            if kind == "-":
                return l - r

            elif kind == "+":
                return l + r


def main():
    interpreter = Interpreter()

    # To test your own Brewin program, place it in `test.br` and run this main function.
    with open("./test.br", "r") as f:
        program = f.read()

    global generate_image
    generate_image = True
    interpreter.run(program)


if __name__ == "__main__":
    main()
