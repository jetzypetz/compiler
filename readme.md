# Implementation of locally defined functions

## Steps

There are several parts of the compilation process that must be extended to accept this functionality. We split it up into steps, explaining what we need to change and how we go about it.

### 1. Parsing
    
#### Intention

Here we need to accept ProcDecls as statements in order for them to be accepted without syntax errors in the AST Blocks. These only occur inside other procedures, and at any depth in the nested scopes.

#### Implementation

Solved simply by accepting procdecls as statements:

```
(line 213)
    def p_stmt_procdecl(self, p):
        """stmt : procdecl"""
        p[0] = p[1]
```

### 2. Type checking
    
#### Intention

1) In this section, we must create the match case for ProcDecls inside Blocks for the tree search type checker.
2) We need to make sure variables accessed inside the nested function are the ones defined outside its scope or in the arguments of the function.
3) We need the function to be accessible for calling in the scope it is defined in, and we need it to go out of scope at the end of the Block.
4) A type check must be done correctly on the return value of each function, correctly associating it to the function it is inside.

#### Implementation

The ProcDecl case is accounted for in the `for_statement()` function (line 209) using the same structure as is present in the function `for_topdecl()`. However, the context manager had to be changed do allow nested functions. Specifically, the `self.proc` variable, which previously was None outside global procdecls and the `ProcDecl` object itself when traversing it, is now a list of `ProcDecl`s, such that as a nested procdecl is encountered in `for_statement()`, it creates a new context, appending itself to the list `self.proc`. Then inside the nested procdecl, if a return call is found, this is checked with the return type of the last procdecl in the list, which is non empty in any `for_statement()` call, so will not raise an Index error. For identifying which function call refers to which function in the nested context, i changed the `self.procs` object to be a `Scope()`, and created a `self.procs` subscope each time a new context is created (in `for_block` and `in_proc`).

```
(line 107)
    @cl.contextmanager
    def in_proc(self, proc: ProcDecl):
        self.proc.append(proc)
        self.scope.open()
        self.procs.open()
        try:
            yield self
        finally:
            self.proc.pop()
            self.scope.close()
            self.procs.close()

(line 279)
    def for_block(self, block : Block):
        with self.scope.in_subscope():
            with self.procs.in_subscope():
                for stmt in block:
                    self.for_statement(stmt)
```

### 2. Maximal Munch


