# Implementation of locally defined functions

## Steps

There are several parts of the compilation process that must be extended to accept this functionality. We split it up into steps, explaining what we need to change and how we go about it.

### 1. Parsing
    
#### Intention

Here we need to accept ProcDecls as statements in order for them to be accepted without syntax errors in the AST Blocks. These only occur inside other procedures, and at any depth in the nested scopes.

#### Implementation

Solved simply by accepting procdecls as statements:

```py
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

```py
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

```py
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
```py
(line 46)

    @classmethod
    def fresh_proc_label(cls, procname : str): # changed
        cls._counter += 1
        return f'{procname}_{cls._counter}'
```
Then, no matter where a function is being called, the call will be made to the correct function, no matter where the code is being executed.
```py
(line 221)

    # using unique function name in TAC and ASM, not function name in BX
    self.push('call', self._procs[proc.value], ...
```
In fact, now that the function has a unique name in TAC, it can be added to the tac anywhere, as it can be accessed by all the lowered code (we have already checked for calls outside its block). Therefore, `self._proc` becomes a list as in TypeChecking, and the `TACProc` is appended ot the list. As soon as a function has been converted to tac, the tac can be added to the `self._tac` attribute for lowering and popped from `self._proc`.

### 3. Assembly Generation

Now comes the most problematic part. We have now created functions that should be able to access data that is not in their stack frame, but we haven't yet created the static links that connect a function with the stack frame of previous functions.

#### Intention

The first hurdle is to understand that static links are created in the stack between a caller and callee, but the link itself does not necessarily relate the callee to the caller, rather to its lexicographic parent. Specifically, our intention is to have the static link point to the base of the lexico. parent's stack frame. As the caller function will be either a sibling, or a child of a sibling of the callee, they will share (up to following back static links) an ancestor, which is the callee's parent. We can subsequently create a recursive algorithm to follow back the static links of the callee to create the static link of the caller, which only requires us to add a `.depth` parameter to all functions and instructions in tac, which only counts nesting of function definitions (not blocks). We will use %r12 for static link computations, as it is unused otherwise. Here is a pseudocode sketch of the algorithm:

```py
# Let c be a call to the function g, made in the function f

# -- before creating the new stack frame --

# you cannot call a deeper function than yourself, as it wont be in scope
assert(c.depth >= g.depth)

if c.depth == g.depth:

    # then g must be f's direct lexico. parent, so
    # rbp will point to the parent's stack frame
    static link = %rbp

else:
    n = g.depth - c.depth
    
    %r12 = %rbp

    for i in range(n):

        # 16(%r12) is where we find the next static link
        %r12 = 16(%r12)

    static link = %r12
```

#### Implementation

The first thing to do is add a `depth` attribute to `TACProc` and `TAC` objects, which is initialised in the maximal munch using `len(self._proc)`, which holds each of the nested definitions as they are being processed, and hence the depth of the function definitions:

```py
(line 122, bxmm.py)

    # processing of a TACProc

    ...
    self._proc.append(TACProc(
        depth       = len(self._proc)
        name      = self._procs[name.value],
        arguments = [f'%{x.value}' for x in arguments],
    ))
    ...
```

In the assembly generation, we now have to create the static links in function calls. In a function call, we have access to the depth of the call,

```py
(line 46, bxasmgen.py)

    if opcode == "call":
        args.append(instr.depth)

    ...

    getattr(self, f'_emit_{opcode}')(*args)
```

As well as the label of the function being called. To get the depth of the callee, we store the depths of the functions in the class in the `self.depths : dict()` attribute, writing the entries in each time we are lowering a TACProc. As each TACProc is written to assembly before it is called, we have access to it's depth when it is called, and write the following code:

```py
(line 213, bxasmgen.py)
        
    n = self.depths[lbl] - depth # depth is the depth of the call

    if n == 0:
        self._emit('pushq', '%rbp')
    else:
        self._emit('movq', '%rbp', '%r12')

        for i in range(n):
            self._emit('movq', '16(%r12)', '%r12')

    self._emit('pushq', '$0')
```

... do i need to only create a static link if vars are captured? whats going on with recursive functions?

##### change of plan

instead of passing info about the depth to the assembly generator, which has more difficulty accessing information about captured vars and relative depth of caller and callee, we choose to pass information only about the relative depth, in the form of a `Opt[int]`, where there is no `link_depth` if there is no need for a link. this is if the callee has no parent (or later, if there are no captured variables). Otherwise `link_depth == 0` if the caller is the parent of the callee, and `link_depth = caller.depth - callee.depth + 1` in general. Then, creating the static link will follow easily in the lowering of any call, where we pass the `link_depth` information.

To achieve this, we need to change the structure we just worked on. Only Calls will have a `link_depth : Opt[int]` and no TAC or TACProc will need a depth attribute. The link depth must be calculated as follows: in the maximal munch, we find the depth of each function, from 0 being global and with a `depth(child) = 1 + depth(parent)`, using len(self._proc), and save it in `self.depths : dict()`. then when we encounter a call, we put in the call's TAC the link_depth. we know the function in which the call is made, because it is self._proc[-1], and the function being called which is the `CallExpression.proc` attribute.

Here we associate the unique assembly name of a function to it's depth:

```py
(line 88, )

    # at beginning of ProcDecl processing
    self.depths[self._procs[name.value]] = len(self._proc)
```

Then in processing the CallExpression:

```py
(line 236, bxmm.py)

    callee_depth = self.depths[proc]

    if callee_depth == 0:
        link_depth = None
    else:
        caller_depth = self.depths[self._proc[-1]]

        link_depth = caller_depth - callee_depth + 1

    self.push(... , link_depth = link_depth)
```

Now moving on to variable capture, we need to use the conveniently placed `prelude` in `_temp` to emit, in the case that a variable is captured at `link_depth = d`, to put d instructions to follow static links before finding where the index of the temp is. we modify `_format_temp` to accept a link depth, and build the prelude:

```py
(line 98, bxasmgen.py)

    def _format_temp(self, index, link_depth):
        if isinstance(index, str):
            return [], f'{index}(%rip)'

        assert(link_depth is not None)

        if link_depth == 0:
            return [], f'-{8*(index+1)}(%rbp)'

        prelude.append(['movq', '%rbp', '%r12'])

        for i in range(link_depth):
            prelude.append(['movq', '24(%r12)', '%r12'])

        return prelude, f'-{8*(index+1)}(%r12)'
```

When we call _temp(some_temp), we need to know how many static links away it is. we can know this by passing information about how far a temporary is, from the tac generation. a temporary name in tac, in the case that the temporary is associated to a variable, should include ':n' where n is the depth of the temporary's definition. We can do this by simply changing its name at definition:

```py
(line 143, bxmm.py)

    self._scope.push(name.value, self.fresh_temporary() + f":{len(self._proc)}")
```

Then we give `TACProc`s a depth in the maximal munch:

```py
(line 283, bxasmgen.py)

    case TACProc(depth, name, arguments, ptac):
        emitter.curr_depth = depth + 1
```

and we make sure formatting of params takes into consideration the extra space of a static link when there is one. to do this we keep track of whether there is a static link

For now, we always have a static link, to see if this works.
