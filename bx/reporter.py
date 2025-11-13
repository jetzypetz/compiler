import sys

class Reporter():
    """
    report errors
    """

    def __init__(self):
        self.errors = []
        self.section = None

    def crash(self, errstr):
        print("=== Error backlog ===")

        for err in self.errors:
            print(f"[ Error ]       {err}", file=sys.stderr)

        errstr = f"{{{self.section}}} " + errstr if self.section else errstr
        print(f"[ Fatal Error ] {errstr}", file=sys.stderr)
        exit()

    def log(self, errstr):
        self.errors.append(f"{{{self.section}}}" + errstr)

    def checkpoint(self, section = None):
        self.section = section
        if self.errors:
            self.crash("error backlog at checkpoint")
