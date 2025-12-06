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

The ProcDecl case is accounted for in the `for_statement()` function (line 209) using the same structure as is present in the function `for_topdecl()`. However, the context manager had to be changed do allow nested functions. Specifically, the `self.proc` variable, which previously was None outside global procdecls and the `ProcDecl` object itself when traversing it, is now a list of `ProcDecl`s, such that as a nested procdecl is encountered in `for_statement()`, it creates a new context, appending itself to the list `self.proc`. Then inside the nested procdecl, if a return call is found, this is checked with the return type of the last procdecl in the list, which is non empty in any `for_statement()` call, so will not raise an Index error. For identifying which function call refers to which function in the nested context, I changed the `self.procs` object to be a `Scope()`, and created a `self.procs` subscope each time a new context is created (in `for_block` and `in_proc`).

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

For the functions to be added to scope, I check if the proc name is locally free, and push it after the function has been processed, so the function is not accessible inside itself, not allowing recursion.

```
(line 230)
    if self.procs.islocal(name.value):
        self.report(
            f'duplicated function declaration for {name.value}',
            position = name.position
        )
    else:
        self.procs.push(name.value, (
            tuple(it.chain(*((x[1],) * len(x[0]) for x in arguments))),
            Type.VOID if retty is None else retty
        ))
```

### 2. Maximal Munch

In this section, we must create the TAC for locally defined functions.

#### Intention

Create the TAC for Locally declared functions, such that the function can be identified correctly by its label, keeping in mind that functions now may have the same name. When a call is encountered, a call to the correct function must be made.

#### Implementation

Functions' names in bx were being used directly in the TAC, and subsequently in the Assembly. This is ok when function names are unique, but if we have nested functions, we need to differentiate different functions with the same name. For this reason, similarly to the TypeChecking section, we need to implement a Scope object `self._procs` that now associates function names to their unique label name in TAC.
```
(line 46)
    @classmethod
    def fresh_proc_label(cls, procname : str): # changed
        cls._counter += 1
        return f'{procname}_{cls._counter}'
```
Then, no matter where a function is being called, the call will be made to the correct function, no matter where the code is being executed.
```
(line 221)
    # using unique function name in TAC and ASM, not function name in BX
    self.push('call', self._procs[proc.value], ...
```
In fact, now that the function has a unique name in TAC, it can be added to the tac anywhere, as it can be accessed by all the lowered code (we have already checked for calls outside its block). Therefore, `self._proc` becomes a list as in TypeChecking, and the `TACProc` is appended ot the list. As soon as a function has been converted to tac, the tac can be added to the `self._tac` attribute for lowering and popped from `self._proc`.
