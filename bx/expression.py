import dataclasses as dc
import enum

from .tac       import Tac,     Taclist
from .reporter  import Error,   Errors

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

# types of expressions:
# bool, number, name
# binary operation, unary operation (with temporary associated)
# set_declared()    -> Errors() | None, check vars are declared and set .temp for operations
# set_type()        -> Errors() | Type, check types match and propagate up

class Expression():
    def __init__(self, line):
        self.line       = line              # int
        self.set_type()                     # Type

    def pprint(self):
        return "base statement"

    def set_type(self):
        self._type = Errors().add(    Error("setting type to a base expression",
                                      this = self.pprint()) )

    def set_declared(self, generator, declared):
        return Errors().add(    Error("called set_declared on a base expression",
                                      this = self.pprint()) )

    def tac(self, declared):
        return None, Taclist()

class Bool(Expression):
    def __init__(self, value, line):
        self.value      = value             # bool
        self.line       = line              # int
        self.set_type()                     # Type

    def pprint(self):
        return "true" if self.value else "false"

    def set_type(self):
        self._type = Type.BOOL

    def set_declared(self, generator, declared):
        return None

    def tac(self, declared):
        return (1 if self.value else 0), Taclist()
    
class Number(Expression):
    def __init__(self, value, line):
        self.value      = value             # int
        self.line       = line              # int
        self.set_type()                     # Type

    def pprint(self):
        return self.value

    def set_type(self):
        self._type = Type.INT

    def set_declared(self, generator, declared):
        return None

    def tac(self, declared):
        return self.value, Taclist()

class Name(Expression):
    def __init__(self, name, line):
        self.name       = name              # str
        self.line       = line              # int
        self.set_type()                     # Type

    def pprint(self):
        return self.name

    def set_type(self):
        self._type = Type.INT

    def set_declared(self, generator, declared):
        if self.name not in declared:
            return Errors().add(    Error(f"{{{self.name}}} used before declaration",
                         this = self.pprint())  )

    def tac(self, declared):
        return declared[self.name], Taclist()

class BinaryOperation(Expression):
    def __init__(self, left, right, operator, line):
        self.left       = left              # Expression
        self.right      = right             # Expression
        self.operator   = operator          # str
        self.line       = line              # int
        self.set_type()                     # Type
        self.temp       = ""

    def pprint(self):
        return (f"binary operation {{{self.operator}}} on line {self.line} "
                f"with left: {{{self.left.pprint()}}}, "
                f"right: {{{self.right.pprint()}}}")

    def set_type(self):
        errors = Errors()

        if self.left._type != operator_arg_type[self.operator]:
            errors.add(     Error(f"{{{self.left.pprint()}}} not of type {operator_arg_type[self.operator]}",
                                  this = self.pprint)   )

        if self.right._type != operator_arg_type[self.operator]:
            errors.add(     Error(f"{{{self.right.pprint()}}} not of type {operator_arg_type[self.operator]}",
                                  this = self.pprint)   )

        self._type = errors or operator_ret_type[self.operator]

    def set_declared(self, generator, declared):
        errors = Errors()

        result = self.left.set_declared(generator, declared)
        if result:
            errors.merge(result)

        result = self.right.set_declared(generator, declared)
        if result:
            errors.merge(result)

        self.temp = next(generator)

        return errors or None

    def tac(self, declared):
        x, L1   = self.left.tac(declared)
        y, L2   = self.right.tac(declared)
        new_tac = Tac(bin_ops[self.operator], [x, y], self.temp)
        return self.temp, L1.merge(L2).add(new_tac)

class UnaryOperation(Expression):
    def __init__(self, right, operator, line):
        self.right      = right             # Expression
        self.operator   = operator          # operator
        self.line       = line              # int
        self.set_type()                     # Type
        self.temp       = ""


    def pprint(self):
        return (f"unary operation {{{self.operator}}} on line {self.line} "
                f"with right: {{{self.right}}}")

    def set_type(self):
        errors = Errors()

        if self.right._type != operator_arg_type[self.operator]:
            errors.add(     Error(f"{{{self.right.pprint()}}} not of type {operator_arg_type[self.operator]}",
                                  this = self.pprint)   )

        self._type = errors or operator_ret_type[self.operator]

    def set_declared(self, generator, declared):
        errors = Errors()

        result = self.right.set_declared(generator, declared)
        if result:
            errors.merge(result)

        self.temp = next(generator)

        return errors or None

    def tac(self, declared):
        x, L    = self.right.tac(declared)
        new_tac = Tac(un_ops[self.operator], [x], self.temp)
        return self.temp, L.add(new_tac)

bin_ops = {
        '&'     :   'and',
        '-'     :   'sub',
        '>>'    :   'shr',
        '^'     :   'xor', 
        '<<'    :   'shl',  
        '%'     :   'mod', 
        '|'     :   'or', 
        '+'     :   'add', 
        '/'     :   'div', 
        '*'     :   'mul',
        # not needed?
        '=='    :   'BOOL_EQ',
        '!='    :   'BOOL_NEQ',
        '<'     :   'BOOL_LT',
        '<='    :   'BOOL_LEQ',
        '>'     :   'BOOL_GT',
        '>='    :   'BOOL_GEQ',
        '&&'    :   'BOOL_AND',
        '||'    :   'BOOL_OR',
        }
un_ops = {
        '-'     :   'neg', 
        '~'     :   'not',
        # not needed?
        '!'     :   'BOOL_NOT',
        }

operator_arg_type = {
        '&'         : Type.INT,
        '-'         : Type.INT,
        '>>'        : Type.INT,
        '^'         : Type.INT,
        '<<'        : Type.INT,
        '%'         : Type.INT,
        '|'         : Type.INT,
        '+'         : Type.INT,
        '/'         : Type.INT,
        '*'         : Type.INT,
        '~'         : Type.INT,
        '=='        : Type.INT,
        '!='        : Type.INT,
        '<'         : Type.INT,
        '<='        : Type.INT,
        '>'         : Type.INT,
        '>='        : Type.INT,
        '&&'        : Type.BOOL,
        '||'        : Type.BOOL,
        '!'         : Type.BOOL,
        }
operator_ret_type = {
        '&'         : Type.INT,
        '-'         : Type.INT,
        '>>'        : Type.INT,
        '^'         : Type.INT,
        '<<'        : Type.INT,
        '%'         : Type.INT,
        '|'         : Type.INT,
        '+'         : Type.INT,
        '/'         : Type.INT,
        '*'         : Type.INT,
        '~'         : Type.INT,
        '=='        : Type.BOOL,
        '!='        : Type.BOOL,
        '<'         : Type.BOOL,
        '<='        : Type.BOOL,
        '>'         : Type.BOOL,
        '>='        : Type.BOOL,
        '&&'        : Type.BOOL,
        '||'        : Type.BOOL,
        '!'         : Type.BOOL,
        }
