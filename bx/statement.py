import dataclasses as dc

from .expression    import Expression, Type
from .tac           import Tac, Taclist
from .reporter      import Error, Errors

### STATEMENTS ###

# holds a line number for the beginning of each statement
# holds the expressions and values associated to one statement
# blocks hold the declarations in their scope, and the scope is passed down in tac gen
# methods:
# pprint()          -> str representation of statement
# check_type()      -> Errors() | None, check expression types are correct
#                      in all top level expressions in statement
# set_declared()    -> Errors() | dict passing back declarations to blocks
#       set_declared checks if there are errors in the block-wise declaration
#       and sets the declarations into scope, assigning the temp names
# tac()             -> Error() | Taclist list of tac lines

@dc.dataclass
class Statement():
    line        : int

    def pprint(self):
        return "base statement"

    def check_type():
        return None

    def set_declared(self, generator, declared):
        return Errors.add(Error("calling set_declared on base statement",
                                this = self.pprint()))

    def tac(self, generator, declared):
        return None

@dc.dataclass
class Declaration(Statement):
    name        : str
    value       : Expression

    def pprint(self):
        return (f"line {self.line}: declaration of {{{self.name}}} "
                f"with value {{{self.value.pprint()}}}")

    def check_type(self):

        match self.value._type:
            case Errors():
                return self.value._type
            case Type.INT:
                return None
            case _:
                return Errors().add(    Error(f"{{{self.value.pprint()}}} "
                                              f"has type {{{self.value._type.name}}} "
                                              f"instead of INT",
                                              this = self.pprint())     )

    def set_declared(self, generator, declared, declared_in_scope):
        errors = Errors()

        # name already declared?
        if self.name in declared_in_scope.keys():
            errors.add(Error(f"declaring {{{self.name}}} again in same scope",
                             this = self.pprint()))

        # expressions not declared?
        result = self.value.set_declared(generator, declared)
        if result:
            errors.merge(result)

        return errors or {self.name : next(generator)}

    def tac(self, declared):
        x, L = self.value.tac(declared)
        return L.add(   Tac("const", [x], declared[self.name])  )

class Block(Statement):
    def __init__(self, statements, line):
        self.statements         = statements    # [Statement]
        self.line               = line          # int
        self.declared           = dict()
        self.declared_in_scope  = dict()


    def pprint(self):
        contents = "\n"
        for statement in self.statements:
            contents += statement.pprint() + "\n"
        return f"line {self.line}: block with contents: {contents}"

    def check_type(self):
        errors = Errors()

        for statement in self.statements:
            result = statement.check_type()
            if result:
                errors.merge(result)

        return errors or None

    def set_declared(self, generator, declared):
        self.declared = declared.copy()
        errors = Errors()

        for statement in self.statements:
            match statement:
                case Declaration():
                    result = statement.set_declared(generator,
                            self.declared, self.declared_in_scope) # only for decls!!
                    if isinstance(result, Errors):
                        errors.merge(result)
                    else:
                        self.declared           |= result
                        self.declared_in_scope  |= result
                case _:
                    result = statement.set_declared(generator, self.declared)
                    if result:
                        errors.merge(result)

        return errors or dict()
                    

    def tac(self, declared):
        taclist = Taclist()
        for statement in self.statements:
            taclist.merge(statement.tac(self.declared))
        return taclist

@dc.dataclass
class Assignment(Statement):
    name        : str
    value       : Expression

    def pprint(self):
        return (f"line {self.line}: assignment of {{{self.name}}} "
                f"with value {{{self.value.pprint()}}}")

    def check_type(self):

        match self.value._type:
            case Errors():
                return self.value._type
            case Type.INT:
                return None
            case _:
                return Errors().add(    Error(f"{{{self.value.pprint()}}} "
                                              f"has type {{{self.value._type.name}}} "
                                              f"instead of INT",
                                              this = self.pprint())     )

    def set_declared(self, generator, declared):
        errors = Errors()

        # name not declared?
        if self.name not in declared.keys():
            errors.add(     Error(f"using {{{self.name}}} before declaration",
                             this = self.pprint())      )

        # expressions not declared?
        result = self.value.set_declared(generator, declared)
        if result:
            errors.merge(result)

        return errors or dict()

    def tac(self, declared):
        x, L = self.value.tac(declared)
        return L.add(   Tac("copy", [x], declared[self.name])    )

class Print(Statement):
    def __init__(self, value, line):
        self.value      = value # Expression
        self.line       = line  # int

    def pprint(self):
        return f"line {self.line}: printing of {{{self.value.pprint()}}}"

    def check_type(self):

        match self.value._type:
            case Errors():
                return self.value._type
            case Type.INT:
                return None
            case Type.BOOL:
                return None
            case _:
                return Errors().add(    Error(f"{{{self.value.pprint()}}} "
                                              f"has type {{{self.value._type.name}}} "
                                              f"instead of INT or BOOL",
                                              this = self.pprint())     )

    def set_declared(self, generator, declared):
        errors = self.value.set_declared(generator, declared)
        return errors or dict()

    def tac(self, declared):
        x, L = self.value.tac(declared)
        return L.add(   Tac("print", [x], None)     )

class Ifelse(Statement):
    def __init__(self, condition, success, failure, line):
        self.condition  = condition # Expression
        self.success    = success   # Block
        self.failure    = failure   # Ifelse | Block | None
        self.line       = line      # int

    def pprint(self):
        return (f"line {self.line}: ifelse block "
                f"with condition: {{{self.condition.pprint()}}}, "
                f"then: {{{self.success.pprint()}}}, "
                f"else: {{{self.failure.pprint()}}}")

    def check_type(self):

        errors = Errors()

        match self.condition._type:
            case Errors():
                errors.merge(self.condition._type)
            case Type.BOOL:
                pass
            case _:
                errors.add(    Error(f"{{{self.condition.pprint()}}} "
                                     f"has type {{{self.condition._type.name}}} "
                                     f"instead of BOOL",
                                     this = self.pprint())     )

        result = self.success.check_type()
        if result:
            errors.merge(result)

        if failure:
            result = self.failure.check_type()
            if result:
                errors.merge(result)

        return errors or None

    def set_declared(self, generator, declared):
        errors = Errors()

        # check condition
        result = self.condition.set_declared(generator, declared)
        if result:
            errors.merge(result)

        # check success block
        result = self.success.set_declared(generator, declared)
        if result:
            errors.merge(result)

        # check rest
        if self.failure is not None:
            result = self.failure.set_declared(generator, declared)
            if result:
                errors.merge(result)

        return errors or dict()

    def tac(self, declared):
        return None # TODO

class While(Statement):
    def __init__(self, condition, loop, line):
        self.condition  = condition # Expression
        self.loop       = loop      # Block
        self.line       = line      # int

    def pprint(self):
        return (f"line {self.line}: while loop"
                f"with condition: {{{self.condition.pprint()}}}, "
                f"loop: {{{self.loop.pprint()}}}")

    def check_type(self):
        errors = Errors()

        match self.condition._type:
            case Errors():
                errors.merge(self.condition._type)
            case Type.BOOL:
                pass
            case _:
                errors.add(    Error(f"{{{self.condition.pprint()}}} "
                                     f"has type {{{self.condition._type.name}}} "
                                     f"instead of BOOL",
                                     this = self.pprint())     )

        result = self.loop.check_type()
        if result:
            errors.merge(result)

        return errors or None

    def set_declared(generator, declared):
        errors = Errors()

        # check condition
        result = self.condition.set_declared(generator, declared)
        if result:
            errors.merge(result)

        # check loop
        result = self.loop.set_declared(generator, declared)
        if result:
            errors.merge(result)

        return errors or dict()

    def tac(self, declared):
        return None # TODO

class  Break(Statement):

    def pprint(self):
        return f"line {self.line}: break statement"

    def check_type():
        return None

    def set_declared(generator, declared):
        return dict()

    def tac(self, declared):
        return None # TODO

@dc.dataclass
class  Continue(Statement):

    def pprint(self):
        return f"line {self.line}: continue statement"

    def check_type():
        return None

    def set_declared(generator, declared):
        return dict()

    def tac(self, declared):
        return None # TODO

