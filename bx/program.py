import dataclasses as dc

from .statement import Statement
from .reporter  import Reporter, Error

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

        for statement in self.statements:
            statement_tac = statement.tac(gen, self.declared)
            match statement_tac:
                case Error():
                    self.reporter.log(statement_tac)
                case _:
                    body += statement_tac

        if len(body) == 0:
            self.reporter.log("no tac generated")

        return [{"proc": "@main", "body": body}]
