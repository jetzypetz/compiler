# --------------------------------------------------------------------
from typing import Optional as Opt

from .bxast import *
from .bxtac import *

# ====================================================================
# Maximal munch

class MM:
    def __init__(self):
        self._counter = -1
        self._tac     = []
        self._vars    = {}

    tac = property(lambda self: self._tac)

    @staticmethod
    def mm(prgm: Program):
        mm = MM(); mm.for_program(prgm)
        return mm._tac

    def fresh_temporary(self):
        self._counter += 1
        return f'%{self._counter}'

    def push(
            self,
            opcode     : str,
            *arguments : str | int,
            result     : Opt[str | int] = None,
    ):
        self._tac.append(TAC(opcode, list(arguments), result))

    def for_program(self, prgm: Program):
        for stmt in prgm:
            self.for_statement(stmt)

    def for_statement(self, stmt: Statement):
        match stmt:
            case VarDeclStatement(name, init):
                self._vars[name.value] = self.fresh_temporary()
                temp = self.for_expression(init)
                self.push('copy', temp, result = self._vars[name.value])

            case AssignStatement(lhs, rhs):
                temp = self.for_expression(rhs)
                self.push('copy', temp, result = self._vars[lhs.value])

            case PrintStatement(value):
                temp = self.for_expression(value)
                self.push('print', temp)

    def for_expression(self, expr: Expression) -> str:
        target = None

        match expr:
            case VarExpression(name):
                target = self._vars[name.value]

            case IntExpression(value):
                target = self.fresh_temporary()
                self.push('const', value, result = target)

            case OpAppExpression(operator, arguments):
                target    = self.fresh_temporary()
                arguments = [self.for_expression(e) for e in arguments]
                self.push(OPCODES[operator], *arguments, result = target)

        return target
