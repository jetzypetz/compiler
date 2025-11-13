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
    opcode    : str
    arguments : list[str | int]
    result    : Opt[str | int] = None

    def tojson(self):
        return dict(
            opcode = self.opcode   ,
            args   = self.arguments,
            result = self.result   ,
        )
