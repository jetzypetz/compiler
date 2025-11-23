### TAC class ###
# one line of tac
# has a json() -> dict() func
# has a pretty printing function -> str

class Tac():
    def __init__(self, opcode, args, result):
        self.opcode = opcode
        self.args   = args
        self.result = result

    def json(self):
        return {
                "opcode"    : self.opcode,
                "args"      : self.args,
                "result"    : self.result,
                }

    def pprint(self):
        r = f"{{{(self.result + " = ") if self.result else ""}"
        match len(self.args):
            case 1:
                return r + f"{self.opcode} {self.args[0]}"
            case 2:
                return r + f"{self.args[0]} {self.opcode} {self.args[1]}"

class Taclist():
    def __init__(self, taclist = None):
        self.taclist = taclist or []
    
    def __len__(self):
        return len(self.taclist)

    def __bool__(self):
        return len(self.taclist) != 0

    def add(self, tac):
        self.taclist.append(tac)
        return self

    def merge(self, other):
        if other:
            self.taclist += other.taclist
        return self
    
    def json(self):
        return [tac.json() for tac in self.taclist]
