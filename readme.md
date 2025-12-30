# Overview

## 1. Support for Locally Defined Functions

The first major goal was to allow function definitions within other functions at arbitrary nesting depths.

### Parsing
The parser was modified to accept `ProcDecl` (procedure declarations) as valid statements within blocks. This simple change ensured that nested function definitions could be represented in the Abstract Syntax Tree (AST) without syntax errors.

### Type Checking
Significant changes were made to the type checker to handle nested scopes. The context for tracking the current function was changed from a single `self.proc` variable to a stack (`self.proc` list). A `Scope` object (`self.procs`) was introduced to manage the visibility of nested function names, ensuring functions are accessible only within their defining block and that variable references are correctly resolved to outer scopes. Return type checking was adjusted to work with this nested context.

### TAC (Three-Address Code) Generation
To generate unique labels for nested functions that may share the same name, a `Scope` object (`self._procs`) was implemented to map source function names to unique TAC labels. The `fresh_proc_label` method was updated to append a counter, guaranteeing label uniqueness across all scopes. A stack (`self._proc` list) was also used during TAC generation to track the current nesting depth of function definitions.

### Assembly Generation & Static Links
The core challenge was generating correct assembly to allow nested functions to access variables from their enclosing (lexical parent) functions. This requires creating *static links* in the stack frame. An algorithm was designed where the static link in a callee's frame points to the base pointer (`%rbp`) of its lexical parent's frame.

To implement this, each function call in the TAC was annotated with a `link_depth`—the number of static link traversals needed to reach the callee's parent frame from the caller's frame. During assembly generation, this `link_depth` dictates a sequence of `movq` instructions that walk the chain of static links (stored at offset `16(%r12)`) to find the correct base pointer before setting up the new stack frame. Temporary variable names in TAC were also annotated with their definition depth (e.g., `temp:2`) so the assembly generator knows how many links to traverse to access a captured variable.

## 2. Support for Functions as Parameters

The second goal was to enable functions to be passed as arguments to other functions, supporting higher-order programming.

### Parsing
The grammar was extended with new `function_type` rules and keywords (`function`, `void`, `ARROW`). A new `FunctionType` AST node was created to represent the types of these parameters, encapsulating their argument and return types.

### Type Checking
The type checker was enhanced to differentiate between variable and function parameters within argument lists. Function parameters are registered in the `self.procs` scope, while regular variables go into `self.scope`. When a `VarExpression` is type-checked in a context expecting a `FunctionType`, the checker now looks it up in `self.procs` instead of `self.scope`. Equality for `FunctionType` objects was implemented to ensure type compatibility.

### TAC Generation & Fat Pointers
Passing a function as a parameter requires creating a *fat pointer*—a structure containing both the function's code address and the static link needed for its execution context. A new `fatptr` TAC instruction was introduced. This instruction, given a function label and a `link_depth`, creates a fat pointer in a temporary location.

When a call is made through a function parameter (an indirect call), a new `callfatptr` TAC instruction is used instead of a regular `call`. This instruction takes the fat pointer's temporary as an operand, from which it will extract both the function address and the correct static link during assembly generation.

### Assembly Generation for Fat Pointers
The assembly generator was extended with `_emit_fatptr` and `_emit_callfatptr` methods. The `_emit_fatptr` method allocates space on the stack for the fat pointer structure (function address and static link) and initializes it by computing the required static link using the provided `link_depth`.

The `_emit_callfatptr` method handles indirect calls. It extracts the function address and static link from the fat pointer structure, pushes the static link onto the stack to set up the callee's context, and then performs an indirect call (`callq *(%r12)`). This ensures the called function executes with access to the variables from its original lexical scope, not the scope of the call site.

## Summary
This project successfully implemented two advanced language features: lexically scoped nested functions and first-class functions. The solution involved coordinated changes across the entire compiler pipeline, introducing mechanisms for scope management, static link generation, and fat pointer creation to correctly handle variable capture and higher-order function calls.

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

# Function Parameters

Now we look at each step required for accepting functions as parameters for functions.

## Steps

### Parsing

#### Intention

Specifically for function arguments, we want to accept a new type, which is the `function_type`.

#### Implementation

After defining new keywords `void`, `function` and `ARROW` in the lexer, we use them in the parser to capture function types:

```py
(line 301, bxparser.py)


    def p_arg_type(self, p):
        """arg_type : type
                    | function_type"""
        p[0] = p[1]

    def p_arg_types_1(self, p):
        """arg_types_1  : arg_type
                        | arg_types_1 COMMA arg_type"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[1].append(p[3])

    def p_arg_types(self, p):
        """arg_types    :
                        | arg_types_1"""
        p[0] = [] if len(p) == 1 else p[1]

    def p_function_return_type(self, p):
        """function_return_type : type"""
        p[0] = p[1]

    def p_function_return_type(self, p):
        """function_return_type : VOID"""
        p[0] = Type.VOID

    def p_function_type(self, p):
        """function_type : FUNCTION LPAREN arg_types RPAREN ARROW function_return_type"""
        p[0] = FunctionType(
                arg_types   = p[3],
                return_type = p[6],
        )
```

And create the class to describe the function parameter in the AST.

```py
(line 25, bxast.py)

@dc.dataclass
class FunctionType():
    arg_types   : list
    return_type : Type
```

As for Calls, they already accept `Name`s in the form of `VarExpression`s, so any function being passed will initally be encoded in the tree as a `VarExpression`.

### Type Checking

#### Intention

Now that the object has been created, let us
    (a) allow function parameters to be passed into scope
    (b) check that the functions match the required arg and return types
    (c) check that function calls match the return values and args

My first thought is to follow a similar process with function parameters as with normal parameters, but using the `self.procs` Scope object for them as they will be used as Procs.

#### Implementation

We write parallel methods `self.check_local_proc_free` (like `self.check_local_free`) and `self.check_local_proc_bound` (like `self.check_local_bound`), that are the same as their counterparts, just referring to the `self.procs` Scope object, rather than `self.scope` (for vars).

(a) we differentiate `ProcDecl` arguments by type, and push them to either `.procs` or `.scope`:

```py
(line 223, bxtychecker.py)

    case ProcDecl(name, arguments, retty, body):
        ...
            for vnames, vtype_ in arguments:
                match vtype_:
                    case FunctionType(arg_types, return_type):
                        for vname in vnames:
                            if self.check_local_proc_free(vname):
                                self.procs.push(vname.value, (arg_types, return_type))
                    case _:
                        for vname in vnames:
                            if self.check_local_free(vname):
                                self.scope.push(vname.value, vtype_)
```

(b) once the functions are in the scope, they will be correctly typechecked

(c) for function calls, arguments are typechecked with the call to `for_expression`

```py
(line 195, bxtychecker.py)


    for i, a in enumerate(arguments):
        self.for_expression(a, atypes[i] if i in range(len(atypes)) else None)
```

and in the AST, function parameters are captured as `VarExpression`s. Therefore, we simply differentiate `VarExpression`s by their expected type to know whether they should be treated as a function or a variable:

```py
(line 156, bxtychecker.py)

    case VarExpression(name):
        match etype:
            case FunctionType(arg_types, return_type):
                if self.check_local_proc_bound(name):
                    (a, r)  = self.procs[name.value]
                    type_   = FunctionType(a, r)
            case _:
                if self.check_local_bound(name):
                    type_ = self.scope[name.value]
```

Then `type_` is a `FunctionType` and gets compared to `etype`. In the `FunctionType` class, we implement equality.

### TAC Generation

Now we must focus on passing the necessary information for building the fat pointer over to the assembly in tac, where scope and type information is lost. My first idea is to pass TAC objects with new opcodes.

#### Intention

(a) when a function is passed, a fatpointer is created. 'fatptr', which takes arguments that will allow it to build the fat pointer. these are going to be probably the function (label) name, and its depth, or relative depth, so that we can in the asmgen know how far back to go to build up the static link part of the fat pointer, and returns to a temporary. it's temporary will be passed as a parameter in a 'param' tac object

(b) in a higher order function, when a function parameter is used, the call is done indirectly. i.e. a 'callfatptr', when a fat pointer is called, so that the asm knows to not blindly call the proc's name, and calculate a new static link for it, because the proc's name is not going to have an associated proc in _procs, nor in depths. instead, here it's going to call the instruction pointer in the fat pointer, and push the static link from the fat pointer.

#### Implementation

(a) when a function is passed as a parameter, we create the fat pointer:

```py
(line 218, bxmm.py)

    case VarExpression(name):
        # function being passed to call
        if isinstance(expr.type_, FunctionType):
            target = self.fresh_temporary()
            f_label = self._procs[name.value]

            callee_depth = self.depths[f_label]
            caller_depth = self.

            link_depth = None if callee_depth==0 else caller_depth - callee_depth + 1

            self.push('fatptr', f_label, result = target, link_depth = link_depth)
        else:
            target = self._scope[name.value]
```

(b) when a function uses a function parameter, we make an indirect call to the fat pointer pointed to in a parameter:

```py
(line 243, bxmm.py)

    case CallExpression(proc, arguments):
        if f"%{proc.value}" in self._proc[-1].arguments:

            fatptr_temp = self._scope[proc.value]

            for i, argument in enumerate(arguments):
                temp = self.for_expression(argument)
                self.push('param', i+1, temp)
            if expr.type_ != Type.VOID:
                target = self.fresh_temporary()

            self.push('callfatptr', fatptr_temp, len(arguments), result = target)
        else:
            ...
```

### Assembly

#### Intention

We need to process the new tac objects 'fatptr', and 'callfatptr'. also we need to see if we need to change indexing for parameters, but i don't think so because the parameters passed are really just pointers to the fat pointers, so they have just one quadword of size, not messing up the indexing. However, we might have to identify which parameter is a function to process parameters differently. otherwise, we only need to turn the pointer in the parameter into a fatpointer when a callfatptr asks for it, that way we know where to go and know that it is a fatptr.

#### Implementation

for callfatptrs:

```py
(line 269, bxasmgen.py)

    def _emit_callfatptr(fatptr_temp, arg, ret = None):
        # extract function address from fatptr
        self._emit('movq', self._temp(fatptr_temp), '%r12')

        assert(arg == len(self._params))

        for i, x in enumerate(self._params[:6]):
            self._emit('movq', self._temp(x), self.PARAMS[i])

        qarg = 0 if arg <= 6 else arg - 6

        if qarg & 0x1:
            self._emit('subq', '$8', '%rsp')

        for x in self._params[6:][::-1]:
            self._emit('pushq', self._temp(x))

        self._emit('pushq', '-8(%r12)') # static link put on stack
        self._emit('pushq', '$0')

        self._emit('callq', '*(%r12)')

        if qarg > 0:
            self._emit('addq', f'${qarg + qarg & 0x1}', '%rsp')

        self._emit('addq', '$16', '%rsp')

        if ret is not None:
            self._emit('movq', '%rax', self._temp(ret))

        self._params = []
```

As for fatptr creation, we create the spaces in stack and create the fatptr object. Its last quadword can be placed in registers, becoming a pointer to the full fatptr.

```py
(line 308, bxasmgen.py)

    def _emit_fatptr(self, f_label, link_depth, dst):
        # create the fat pointer at dst
        self._emit('leaq', self._temp(dst, size = 3), '%r13')

        self._emit('movq', '%r13', '(%r13)')
        self._emit('subq', '$8', '(%r13)')

        # self._emit('movq', f"${f_label}", '-8(%r13)')
        self._emit('leaq', f"{f_label}(%rip)", '%rax')
        self._emit('movq', '%rax', '-8(%r13)')
        
        self._emit('movq', '%rbp', '%r12')

        for i in range(link_depth):
            self._emit('movq', '24(%r12)', '%r12')

        self._emit('movq', '%r12', '-16(%r13)')
```
