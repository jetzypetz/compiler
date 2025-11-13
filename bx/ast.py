import dataclasses as dc

@dc.dataclass
class AST:
    line    : int

    def pprint():
        return "base ast"

@dc.dataclass
class Statement(AST):

@dc.dataclass
class Expression(AST):

@dc.dataclass
class Declaration(Statement):
    name    : str
    value   : Expression

    def pprint():
        return f"declaration of {{{name}}} with value {{{value.pprint()}}}"

    def tac(self, generator):
        x, L = self.value.tac(generator)
        temp = next(generator)
        declared[self.name] = temp
        return L + [{"opcode"   : "const",
                     "args"     : [x],
                     "result"   : temp}]

@dc.dataclass
class Assignment(Statement):
    name    : str
    value   : Expression

    def pprint():
        return f"assignment of {{{name}}} with value {{{value.pprint()}}}"

    def tac(self, generator):
        x, L = self.value.tac(generator)
        return L + [{"opcode"   : "copy",
                     "args"     : [x],
                     "result"   : next(generator)}]

@dc.dataclass
class Print(Statement):
    value   : Expression

    def pprint():
        return f"printing of {{{value.pprint()}}}"

    def tac(self, generator):
        x, L = self.value.tac(generator)
        return L + [{"opcode"    : "print",
                     "args"      : [x],
                     "result"    : None}]

@dc.dataclass
class Number(Expression):
    value   : int

    def pprint():
        return value

    def tac(self, generator):
        return self.value, []

@dc.dataclass
class Name(Expression):
    name    : str

    def pprint():
        return name

    def tac(self, generator):
        return declared[self.name], []

@dc.dataclass
class BinaryOperation(Expression):
    left        : Expression
    right       : Expression
    operator    : str

    def pprint():
        return f"binary operation {{{operation}}} with:\nleft {{{left}}}\nright {{{right}}}"

    def tac(self, generator):
        x, L1   = self.left.tac(generator)
        y, L2   = self.right.tac(generator)
        temp    = next(generator)
        return temp, L1 + L2 + [{"opcode": bin_ops[self.operator],
                                "args"  : [x, y],
                                "result": temp}]

@dc.dataclass
class UnaryOperation(Expression):
    right       : Expression
    operator    : str

    def pprint():
        return f"unary operation {{{operation}}} with:\nright {{{right}}}"

    def tac(self, generator):
        x, L    = self.right.tac(generator)
        temp    = next(generator)
        return temp, L + [{"opcode": un_ops[self.operator],
                          "args"  : [x],
                          "result": temp}]

declared = dict()
bin_ops = {
        '&' : 'and',
        '-' : 'sub',
        '>>' : 'shr',
        '^' : 'xor',
        '<<' : 'shl',
        '%' : 'mod',
        '|' : 'or',
        '+' : 'add',
        '/' : 'div',
        '*' : 'mul'}
un_ops = {
        '-' : 'neg',
        '~' : 'not'}













