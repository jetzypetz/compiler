import sys
import json

class Tools:
    def __init__(self, reporter):
        self.reporter = reporter

    def parseargs(self):
        """
        return infile and outfile names
        """
        if len(sys.argv) < 2:
            self.reporter.crash(f"usage: {sys.argv[0]} <bxfilename>")

        if len(sys.argv) > 2:
            self.reporter.log(f"didnt expect so many args: {sys.argv}")

        if not sys.argv[1].endswith(".bx"):
            self.reporter.log(f"expected '.bx' file, got {sys.argv[1]}")
            return sys.argv[1], sys.argv[1]

        return sys.argv[1], sys.argv[1].removesuffix(".bx")
    
    def writejson(self, data, filename):
        """
        write the json file
        """
        try:
            with open(filename, "r") as f:
                if self.reporter.confirm(f"file {{{filename}}} already exists, "
                                         "do you want to overwrite? [Y/n]"):
                    with open(filename, "w") as f:
                        json.dump(data, f)

        except FileNotFoundError:
            with open(filename, "w") as f:
                json.dump(data, f)

        except Exception as e:
            self.reporter.log(f"Error writing JSON file: {e}")




