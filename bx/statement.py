import dataclasses as dc

from .ast           import AST
from .expression    import Expression
from .reporter      import Error

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

