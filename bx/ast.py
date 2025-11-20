import dataclasses as dc
import enum

from .reporter import Reporter, Error

### AST CLASSES ###

# Statement and Expression Objects for ast
# maintain line information for errors
# two transformers:
# tac() -> Error() or tac in json form
# pprint() -> str for display

@dc.dataclass
class AST:
    line        : int

    def pprint(self):
        return "base ast"

### EXPRESSIONS ###

@dc.dataclass
class Expression(AST):

    def pprint(self):
        return "base statement"

    def tac(self, generator, declared):
        return Error("This is a base expression",
                     this = self.pprint()), []

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

### STATEMENTS ###

@dc.dataclass
class Statement(AST):

    def pprint(self):
        return "base statement"

    def tac(self, generator, declared):
        return Error("This is a base statement", this = self.pprint())

@dc.dataclass
class Declaration(Statement):
    name        : str
    value       : Expression

    def pprint(self):
        return f"declaration of {{{self.name}}} with value {{{self.value.pprint()}}}"

    def tac(self, generator, declared):
        if self.name in declared.keys():
            return Error(f"declaring {{{self.name}}} again",
                         this = self.pprint())

        x, L = self.value.tac(generator, declared)
        if isinstance(x, Error):
            x.context = self.pprint()
            return x

        temp = next(generator)
        declared[self.name] = temp
        return L + [{"opcode"   : "const",
                     "args"     : [x],
                     "result"   : temp}]

@dc.dataclass
class Block(Statement):
    statements  : [Statement]

    def pprint(self):
        return f"block with contents: {"\n" + stmt.pprint() for stmt in self.statements}"

    def tac(self, generator, declared):
        return None # TODO

@dc.dataclass
class Assignment(Statement):
    name        : str
    value       : Expression

    def pprint(self):
        return f"assignment of {{{self.name}}} with value {{{self.value.pprint()}}}"

    def tac(self, generator, declared):
        if self.name not in declared.keys():
            return Error(f"{{{self.name}}} assigned before declaration",
                         this = self.pprint())

        x, L = self.value.tac(generator, declared)
        if isinstance(x, Error):
            x.context = self.pprint()
            return x

        return L + [{"opcode"   : "copy",
                     "args"     : [x],
                     "result"   : next(generator)}]

@dc.dataclass
class Print(Statement):
    value       : Expression

    def pprint(self):
        return f"printing of {{{self.value.pprint()}}}"

    def tac(self, generator, declared):
        x, L = self.value.tac(generator, declared)
        if isinstance(x, Error):
            x.context = self.pprint()
            return x

        return L + [{"opcode"    : "print",
                     "args"      : [x],
                     "result"    : None}]

@dc.dataclass
class Ifelse(Statement):
    condition   : Expression
    success     : Block
    failure     : Ifelse | Block | None

    def pprint(self):
        return f"ifelse block with condition: {{{self.condition.pprint()}}}, then: {{{self.success.pprint()}}}, else: {{{self.failure.pprint()}}}"

    def tac(self, generator, declared):
        return None # TODO

@dc.dataclass
class While(Statement):
    condition   : Expression
    loop        : Block

    def pprint(self):
        return f"while loop with condition: {{{self.condition.pprint()}}}, loop: {{{self.loop.pprint()}}}"

    def tac(self, generator, declared):
        return None # TODO

@dc.dataclass
class  Break(Statement):

    def pprint(self):
        return f"break statement"

    def tac(self, generator, declared):
        return None # TODO

@dc.dataclass
class  Continue(Statement):

    def pprint(self):
        return f"continue statement"

    def tac(self, generator, declared):
        return None # TODO

### PROGRAM CLASS ###

# maintains the program and declared temps
# builds tac and checks syntax in to_tac()

@dc.dataclass
class Program:
    stmts       : [Statement]
    reporter    : Reporter
    declared    = dict()
    
    def to_tac(self):
        body = []
        gen = temp_names()

        for stmt in self.stmts:
            stmt_tac = stmt.tac(gen, self.declared)
            match stmt_tac:
                case Error():
                    self.reporter.log(stmt_tac)
                case _:
                    body += stmt_tac

        if len(body) == 0:
            self.reporter.log("no tac generated")

        return [{"proc": "@main", "body": body}]













