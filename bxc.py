from bx.tools import Tools
from bx.parser import Parser
from bx.reporter import Reporter

def main():
    """
    usage:
    python3 bxc.py <filename>.bx

    creates executable called <filename>.exe
    """
    # preliminary objects
    reporter    = Reporter()
    tools       = Tools(reporter)
    parser      = Parser(reporter)

    # parse args
    reporter.checkpoint("parsing")
    inname, outbasename = tools.parseargs()

    # filename to ast
    reporter.checkpoint("ast gen")
    prgm = parser.to_prgm(inname)

    # ast to tac
    reporter.checkpoint("tac gen")
    tac = prgm.to_tac()

    # tac to json file
    reporter.checkpoint("json wr")
    tools.writejson(tac, outbasename + ".tac.json")

    reporter.checkpoint("end")


if __name__ == "__main__":
    main()















