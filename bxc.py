from bx.tools import Tools
from bx.parser import Parser
from bx.muncher import Muncher
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
    muncher     = Muncher(reporter)

    # parse args
    reporter.checkpoint("parsing")
    inname, outname = tools.parseargs()

    # filename to bx ast
    reporter.checkpoint("ast gen")
    ast = parser.to_ast(inname)

    # bxast to tac
    reporter.checkpoint("tac gen")
    tac = muncher.to_tac(ast)

    # tac to json file
    reporter.checkpoint("json wr")
    jsonname = tools.writejson(tac, outname + ".tac.json")


if __name__ == "__main__":
    main()















