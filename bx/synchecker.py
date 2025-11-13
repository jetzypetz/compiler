import dataclasses as dc

from reporter import Reporter

@dc.dataclass
class Checker:
    reporter: Reporter

    def check_syntax(self, ast):
        for stmt in ast:
            if (errstr = stmt.pprint()):
                self.reporter.log(errstr)
        # check no declared twice

                
