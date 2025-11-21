# TODO create type of each expression from bottom up, it might be error. to check, just check in each stmt if the top level expressions are errors.

import dataclasses as dc
import enum

from .ast       import AST
from .reporter  import Error

class Type(enum.Enum):
    VOID = 0
    BOOL = 1
    INT  = 2

    def pprint(self):
        match self:
            case self.VOID:
                return "void"
            case self.BOOL:
                return "bool"
            case self.INT:
                return "int"

### EXPRESSIONS ###

@dc.dataclass
class Expression(AST):

    def pprint(self):
        return "base statement"

    def tac(self, generator, declared):
        return Error("This is a base expression",
                     this = self.pprint()), []

@dc.dataclass
class Bool(Expression):
    value       : bool

    def pprint(self):
        return "true" if self.value else "false"

    def tac(self, generator, declared):
        return (1 if self.value else 0), []
    
@dc.dataclass
class Number(Expression):
    value       : int

    def pprint(self):
        return self.value

    def tac(self, generator, declared):
        return self.value, []

@dc.dataclass
class Name(Expression):
    name        : str

    def pprint(self):
        return self.name

    def tac(self, generator, declared):
        if self.name not in declared:
            return Error(f"{{{self.name}}} used before declaration",
                         this = self.pprint()), []
        return declared[self.name], []

@dc.dataclass
class BinaryOperation(Expression):
    left        : Expression
    right       : Expression
    operator    : str

    def pprint(self):
        return f"binary operation {{{self.operator}}} with left: {{{self.left.pprint()}}}, right: {{{self.right.pprint()}}}"

    def tac(self, generator, declared):
        x, L1   = self.left.tac(generator, declared)
        if isinstance(x, Error):
            return x, []

        y, L2   = self.right.tac(generator, declared)
        if isinstance(y, Error):
            return y, []

        temp    = next(generator)
        return temp, L1 + L2 + [{"opcode": bin_ops[self.operator],
                                "args"  : [x, y],
                                "result": temp}]

@dc.dataclass
class UnaryOperation(Expression):
    right       : Expression
    operator    : str

    def pprint(self):
        return f"unary operation {{{self.operator}}} with right: {{{self.right}}}"

    def tac(self, generator, declared):
        x, L    = self.right.tac(generator, declared)
        if isinstance(x, Error):
            return x, []

        temp    = next(generator)
        return temp, L + [{"opcode": un_ops[self.operator],
                          "args"  : [x],
                          "result": temp}]

def temp_names():
    i = 0
    while True:
        yield f"%{i}"
        i += 1

bin_ops = {
        '&'     : 'and',
        '-'     : 'sub',
        '>>'    : 'shr',
        '^'     : 'xor',
        '<<'    : 'shl',
        '%'     : 'mod',
        '|'     : 'or',
        '+'     : 'add',
        '/'     : 'div',
        '*'     : 'mul'}
un_ops = {
        '-'     : 'neg',
        '~'     : 'not'}

