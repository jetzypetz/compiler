import sys
import dataclasses as dc

class Reporter():
    """
    report errors
    """
    def __init__(self):
        self.errors  = []
        self.section = None

    def crash(self, errstr):
        print("=== Error backlog ===")

        for err in self.errors:
            print(f"[ Error ] {err}", file=sys.stderr)

        errstr = f"{{{self.section}}} \t| " + errstr if self.section else errstr
        print(f"[ Fatal Error ] | {errstr}", file=sys.stderr)

        exit()

    def log(self, error):
        match error:
            case Errors():
                for err in error.errors:
                    self.log(err)
            case _:
                self.errors.append(f"{{{self.section}}} \t| " + str(error))

    def checkpoint(self, section = None):
        self.section = section

        if self.errors:
            self.crash("error backlog at checkpoint")

    def confirm(self, errstr):
        answer = input(errstr)
        if not len(answer) or answer[0].lower() == "y":
            return True
        return False

class Error():
    """
    class allows to pass errors forward with all information
    """
    def __init__(self, errstr, this = None, context = None):
        self.errstr     = errstr
        self.this       = this
        self.context    = context

    def __repr__(self):
        to_log  = self.errstr
        to_log += f" in {{{self.this}}}"              if self.this     else ""
        to_log += f" in context {{{self.context}}}"   if self.context  else ""
        return to_log
    
class Errors():
    def __init__(self, errors = None):
        self.errors = errors or []
         
    def __bool__(self):
        return len(self.errors) != 0

    def __len__(self):
        return len(self.errors)

    def __repr__(self):
        to_log = ""
        for err in self.errors:
            to_log += str(err)
        return to_log

    def merge(self, other):
        self.errors += other.errors
        return self

    def add(self, error : Error):
        self.errors.append(error)
        return self

