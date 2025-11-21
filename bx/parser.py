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
        ('left'     , 'BOOL_OR'                 ),
        ('left'     , 'BOOL_AND'                ),
        ('left'     , 'PIPE'                    ),
        ('left'     , 'HAT'                     ),
        ('left'     , 'AMP'                     ),
        ('nonassoc' , 'BOOL_EQ', 'BOOL_EQ'      ),
        ('nonassoc' , 'BOOL_LT', 'BOOL_GT', 'BOOL_LEQ', 'BOOL_GEQ' ),
        ('left'     , 'LTLT', 'GTGT'            ),
        ('left'     , 'PLUS', 'DASH'            ),
        ('left'     , 'STAR', 'SLASH', 'PCENT'  ),
        ('right'    , 'UMINUS', 'BOOL_NOT'      ),
        ('right'    , 'UNEG'                    ),
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

    def p_bool(self, p):
        """expr : TRUE
                | FALSE"""
        p[0] = Bool(
            value       = (p[1] == "true"),
            line        = p.lineno,
        )

    def p_type_number(self, p):
        """type : INT"""
        p[0] = Type.INT

    def p_type_bool(self, p):
        """type : BOOL"""
        p[0] = Type.BOOL

    def p_unary_operation(self, p):
        """expr : DASH expr %prec UMINUS
                | TILD expr %prec UNEG
                | BOOL_NOT expr"""
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
                | expr GTGT     expr
                | expr BOOL_EQ  expr
                | expr BOOL_NEQ expr
                | expr BOOL_LT  expr
                | expr BOOL_LEQ expr
                | expr BOOL_GT  expr
                | expr BOOL_GEQ expr
                | expr BOOL_AND expr
                | expr BOOL_OR  expr"""
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
        """declaration : VAR IDENT EQ expr COLON INT SEMICOLON"""
        p[0] = Declaration(
            name        = p[2],
            value       = p[4],
            line        = p.lineno(0),
        )

    def p_block(self, p):
        """block : LBRACE stmts RBRACE"""
        p[0] = Block(
            statements  = p[2],
            line        = p.lineno(0),
        )

    def p_assignment(self, p):
        """assignment : IDENT EQ expr SEMICOLON"""
        p[0] = Assignment(
            name        = p[1],
            value       = p[3],
            line        = p.lineno(0),
        )

    def p_print(self, p):
        """print : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = Print(
            value       = p[3],
            line        = p.lineno(0),
        )

    def p_ifelse(self, p):
        """ifelse : IF LPAREN expr RPAREN block ifrest"""
        p[0] = Ifelse(
            condition   = p[3],
            success     = p[5],
            failure     = p[6],
            line        = p.lineno(0),
        )
    
    def p_ifrest(self, p):
        """ifrest :
                  | ELSE ifelse
                  | ELSE block"""
        if len(p) == 1:
            p[0] = None
        else:
            p[0] = p[2]

    def p_while(self, p):
        """while : WHILE LPAREN expr RPAREN block"""
        p[0] = While(
            condition   = p[3],
            loop        = p[5],
            line        = p.lineno(0),
        )

    def p_jump(self, p):
        """jump : BREAK SEMICOLON
                | CONTINUE SEMICOLON"""
        if p[1] == "break":
            p[0] = Break(
                line = p.lineno(0),
            )
        else:
            p[0] = Continue(
                line = p.lineno(0),
            )

    def p_stmt(self, p):
        """stmt : declaration
                | block
                | assignment
                | print
                | ifelse
                | while
                | jump"""
        p[0] = p[1]

    def p_stmts(self, p):
        """stmts :
                 | stmts stmt"""
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_program(self, p):
        """program : DEF MAIN LPAREN RPAREN block"""
        p[0] = Program(p[5], self.reporter)

    def p_error(self, p):
        if p:
            self.reporter.log(f'syntax error at line {p.lineno}')
        else:
            self.reporter.log('syntax error at end of file')
