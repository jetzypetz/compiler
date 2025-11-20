import bisect
import ply.lex
import re

class Lexer:
    keywords = {
        x: x.upper() for x in (
            'def'      ,
            'int'      ,
            'bool'     ,
            'main'     ,
            'print'    ,
            'var'      ,
            'true'     ,
            'false'    ,
            'if'       ,
            'else'     ,
            'while'    ,
            'break'    ,
            'continue' ,
        )
    }
    
    tokens = (
        'IDENT' ,               # : str
        'NUMBER',               # : int

        # Punctuation
        'LPAREN'       ,
        'RPAREN'       ,
        'LBRACE'       ,
        'RBRACE'       ,
        'COLON'        ,
        'SEMICOLON'    ,

        'AMP'          ,
        'DASH'         ,
        'EQ'           ,
        'GTGT'         ,
        'HAT'          ,
        'LTLT'         ,
        'PCENT'        ,
        'PIPE'         ,
        'PLUS'         ,
        'SLASH'        ,
        'STAR'         ,
        'TILD'         ,

        'BOOL_EQ'      ,
        'BOOL_NEQ'     ,
        'BOOL_LT'      ,
        'BOOL_LEQ'     ,
        'BOOL_GT'      ,
        'BOOL_GEQ'     ,
        'BOOL_AND'     ,
        'BOOL_OR'      ,
        'BOOL_NOT'     ,
    ) + tuple(keywords.values())

    t_LPAREN    = re.escape('(')
    t_RPAREN    = re.escape(')')
    t_LBRACE    = re.escape('{')
    t_RBRACE    = re.escape('}')
    t_COLON     = re.escape(':')
    t_SEMICOLON = re.escape(';')

    t_AMP       = re.escape('&')
    t_DASH      = re.escape('-')
    t_EQ        = re.escape('=')
    t_GTGT      = re.escape('>>')
    t_HAT       = re.escape('^')
    t_LTLT      = re.escape('<<')
    t_PCENT     = re.escape('%')
    t_PIPE      = re.escape('|')
    t_PLUS      = re.escape('+')
    t_SLASH     = re.escape('/')
    t_STAR      = re.escape('*')
    t_TILD      = re.escape('~')

    t_BOOL_EQ   = re.escape('==')
    t_BOOL_NEQ  = re.escape('!=')
    t_BOOL_LT   = re.escape('<')
    t_BOOL_LEQ  = re.escape('<=')
    t_BOOL_GT   = re.escape('>')
    t_BOOL_GEQ  = re.escape('>=')
    t_BOOL_AND  = re.escape('&&')
    t_BOOL_OR   = re.escape('||')
    t_BOOL_NOT  = re.escape('!')

    t_ignore = ' \t'            # Ignore all whitespaces
    t_ignore_comment = r'//.*'

    def __init__(self, reporter):
        self.lexer    = ply.lex.lex(module = self)
        self.reporter = reporter

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_IDENT(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        if t.value in self.keywords:
            t.type  = self.keywords[t.value]
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_error(self, t):
        self.reporter.log(f"lexer: illegal character '{t.value[0]}' -- skipping")
        t.lexer.skip(1)
