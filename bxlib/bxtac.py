# --------------------------------------------------------------------
import dataclasses as dc

from typing import Optional as Opt

# ====================================================================
# Three-Address Code

OPCODES = {
    'opposite'            : 'neg',
    'addition'            : 'add',
    'subtraction'         : 'sub',
    'multiplication'      : 'mul',
    'division'            : 'div',
    'modulus'             : 'mod',
    'bitwise-negation'    : 'not',
    'bitwise-and'         : 'and',
    'bitwise-or'          :  'or',
    'bitwise-xor'         : 'xor',
    'logical-left-shift'  : 'shl',
    'logical-right-shift' : 'shr',
}

# --------------------------------------------------------------------
@dc.dataclass
class TAC:
    opcode      : str
    arguments   : list[str | int]
    result      : Opt[str | int]    = None
    link_depth  : Opt[int]          = None

    def tojson(self):
        return dict(
            opcode      = self.opcode    ,
            args        = self.arguments ,
            result      = self.result    ,
            link_depth  = self.link_depth,
        )

    def __repr__(self):
        aout = self.opcode
        if self.arguments:
            aout = f"{aout} {', '.join(map(repr, self.arguments))}"
        if self.result:
            aout = f"{self.result} = {aout}"
        if self.link_depth is not None:
            aout = f"{aout} : link depth = {self.link_depth}"
        return aout

# --------------------------------------------------------------------
class TACProc:
    __match_args__ = ('depth', 'name', 'arguments', 'tac')

    def __init__(self, depth: int, name: str, arguments: list[str]):
        self.depth      = depth
        self.name       = name
        self.arguments  = arguments
        self.tac        = []

    def __repr__(self):
        aout = f"proc @{self.name}"
        if self.arguments:
            aout = f"{aout}({', '.join(map(repr, self.arguments))})"
        aout = [f"{aout}: depth {self.depth}"]
        for tac in self.tac:
            aout.append(f"    {tac};")
        return "\n".join(aout) + "\n"

# --------------------------------------------------------------------
class TACVar:
    __match_args__ = ('name', 'value')

    def __init__(self, name: str, value: int):
        self.name   = name
        self.value  = value

    def __repr__(self):
        return f"var @{self.name} = {self.value};"
