import ply.yacc
import dataclasses as dc

from .ast     import *
from .lexer     import Lexer
from .reporter  import Reporter

@dc.dataclass
class Parser:
    tokens      = Lexer.tokens
    start       = 'program'
    precedence  = (
        ('left'    , 'PIPE'                    ),
        ('left'    , 'HAT'                     ),
        ('left'    , 'AMP'                     ),
        ('left'    , 'LTLT', 'GTGT'            ),
        ('left'    , 'PLUS', 'DASH'            ),
        ('left'    , 'STAR', 'SLASH', 'PCENT'  ),
        ('right'   , 'UMINUS'                  ),
        ('right'   , 'UNEG'                    ),
    )


    def __init__(self, reporter: Reporter):
        self.reporter   = reporter
        self.lexer      = Lexer(self.reporter)
        self.parser     = ply.yacc.yacc(module = self)

    def to_prgm(self, filename: str):
        try:
            with open(filename, "r") as f:
                prgm = f.read()
        except Exception() as e:
            self.reporter.crash(e)

        return self.parser.parse(
            prgm,
            lexer       = self.lexer.lexer,
            tracking    = True
        )

    def p_name(self, p):
        """expr : IDENT"""
        p[0] = Name(
            name        = p[1],
            line        = p.lineno(0),
        )

    def p_number(self, p):
        """expr : NUMBER"""
        p[0] = Number(
            value       = p[1],
            line        = p.lineno(0),
        )

    def p_unary_operation(self, p):
        """expr : DASH expr %prec UMINUS
                | TILD expr %prec UNEG"""
        p[0] = UnaryOperation(
            right       = p[2],
            operator    = p[1],
            line        = p.lineno(0),
        )

    def p_binary_operation(self, p):
        """expr : expr PLUS     expr
                | expr DASH     expr
                | expr STAR     expr
                | expr SLASH    expr
                | expr PCENT    expr
                | expr AMP      expr
                | expr PIPE     expr
                | expr HAT      expr
                | expr LTLT     expr
                | expr GTGT     expr"""
        p[0] = BinaryOperation(
            left        = p[1],
            right       = p[3],
            operator    = p[2],
            line        = p.lineno(0),
        )

    def p_parentheses(self, p):
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]

    def p_declaration(self, p):
        """stmt : VAR IDENT EQ expr COLON INT SEMICOLON"""
        p[0] = Declaration(
            name        = p[2],
            value       = p[4],
            line        = p.lineno(0),
        )

    def p_assignment(self, p):
        """stmt : IDENT EQ expr SEMICOLON"""
        p[0] = Assignment(
            name        = p[1],
            value       = p[3],
            line        = p.lineno(0),
        )

    def p_print(self, p):
        """stmt : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = Print(
            value       = p[3],
            line        = p.lineno(0),
        )

    def p_stmts(self, p):
        """stmts :
                 | stmts stmt"""
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_program(self, p):
        """program : DEF MAIN LPAREN RPAREN LBRACE stmts RBRACE"""
        p[0] = Program(p[6], self.reporter)

    def p_error(self, p):
        if p:
            self.reporter.log(f'syntax error at line {p.lineno}')
        else:
            self.reporter.log('syntax error at end of file')
