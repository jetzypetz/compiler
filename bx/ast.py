import dataclasses as dc

from .reporter import Reporter, Error

### AST CLASS ###

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

    def tac(self, generator, declared):
        return Error(f"this is a base ast",
                     this = self.pprint())
