from .statement import Statement
from .reporter  import Reporter

### PROGRAM CLASS ###

# maintains the program and declared temps
# builds tac and checks syntax in to_tac()

def temp_names():
    i = 0
    while 1:
        yield f"%{i}"
        i += 1

class Program:
    def __init__(self, block, reporter):
        self.block      = block     # Block
        self.reporter   = reporter  # Reporter
        self.declared   = dict()
    
    def to_tac(self):
        gen     = temp_names()

        result  = self.block.check_type()
        if result:
            self.reporter.log(result)

        self.reporter.checkpoint()

        result  = self.block.set_declared(gen, dict()) # change dict() here for global vars
        if result:
            self.reporter.log(result)

        self.reporter.checkpoint()

        body    = self.block.tac(dict()).json()

        return [{"proc": "@main", "body": body}]
