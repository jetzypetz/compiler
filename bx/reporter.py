import sys
import dataclasses as dc

@dc.dataclass
class Reporter():
    """
    report errors
    """
    errors  = []
    section = None

    def crash(self, errstr):
        print("=== Error backlog ===")

        for err in self.errors:
            print(f"[ Error ]       {err}", file=sys.stderr)

        errstr = f"{{{self.section}}} " + errstr if self.section else errstr
        print(f"[ Fatal Error ] {errstr}", file=sys.stderr)

        exit()

    def log(self, err):
        match err:
            case Error(errstr, this, context):
                to_log = f"{{{self.section}}}" + errstr
                to_log += f"\nin         {{{this}}}"        if this     else ""
                to_log += f"\nin context {{{context}}}\n"   if context  else ""
                self.errors.append(to_log)
            case _:
                self.errors.append(f"{{{self.section}}}" + err)

    def checkpoint(self, section = None):
        self.section = section

        if self.errors:
            self.crash("error backlog at checkpoint")

    def confirm(self, errstr):
        answer = input(errstr)
        if not len(answer) or answer[0].lower() == "y":
            return True
        return False


@dc.dataclass
class Error():
    """
    class allows to pass errors forward with all information
    """
    errstr  : str
    this    = None
    context = None
    
