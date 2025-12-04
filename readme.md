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

The ProcDecl case is accounted for in the `for_statement()` function (line 209) using the same structure as is present in the function `for_topdecl()`. However, the context manager had to be changed do allow nested functions. Specifically, the `self.proc` variable, which previously was None outside global procdecls and the `ProcDecl` object itself when traversing it, is now a list of `ProcDecl`s, such that as a nested procdecl is encountered in `for_statement()`, it creates a new context, appending itself to the list `self.proc`. Then inside the nested procdecl, if a return call is found, this is checked with the return type of the last procdecl in the list, which is non empty in any `for_statement()` call, so will not raise an Index error.

~ make sure typechecker.proc is used correctly everywhere
~ global functions can be recursive
~ for part 3, im considering having a self.proc_scope attribute to keep track of when functions go out of scope. Using a separate `scope` object. as i am processing a block, when i encounter a proc decl, then information has to be saved at this level about the function, and removed at the end of the context. any time a new scope is open for variables, a parallel one must be created for functions with name : Procedure, in order to access its return value and the number of arguments and their types.
~ instead of the above, procs becomes a scope. any context that creates a subscope for vars, must also create a subscope for procs.
