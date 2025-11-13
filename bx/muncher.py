import dataclasses as dc

from .reporter import Reporter

def temp_names():
    i = 0
    while True:
        yield f"%{i}"
        i += 1

@dc.dataclass
class Muncher:
    reporter: Reporter

    def to_tac(self, ast):

        body = []
        gen = temp_names()

        for statement in ast:
            body += statement.tac(gen)

        if len(body) == 0:
            self.reporter.log("no tac generated")

        return [{"proc": "@main", "body": body}]
