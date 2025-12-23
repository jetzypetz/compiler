lets try to understand whats going on in the assembly generation. my goal is to identify and understand where memory addresses like `-8(%rbp)` for temporaries are made, so that i can identify where (a) i need to stop the nested functions from believing that old adresses that have since been changed by other functions are still valid, and (b), identify how to build the new address specifically for captured vars, which have to be read from a previous scope. the idea would be: know where the static pointer is, load it into REG, where REG is some register i will choose for this task, then know where the captured var is from there, use `(-n(%REG)` to access it if it is in this scope, otherwise, continue going down the chain by knowing where the previous static link is and load that one into REG `movq -n(%REG), %REG`. and keeping count of how many static links i have left to go is going to be connected to keeping count of where the next static link is relative to the last one. this suggests ill need some nested structure of static links (potentially in the tac, if this is where the memory addresses for temporaries are created; or lower down, but still needing to pass down some information about which vars are captured etc from the tac).

Alright. starting from the top: bxc.py calls .lower(taclist) on the class associated to the specific architecture of the machine. lower outputs a string which is all the assembly code to write to the .s file. it does the following:

- calls _.lower1(tac) on each tac in the tac list, so on each TACProc or TACVar.

    if tac is a TACVar, i.e. if it is a global variable, _.lower1(tac) creates an `emitter` and emits direct assembly code to it using `_emit()`. this appends the return value of `_get_asm()` to `_asm`, which will be returned. basically _lower1(tac) returns a list of strings representing each assembly line associated to that tac instruction

    if tac is a TACProc, i.e. if it is a procedure, _.lower1(tac) creates an `emitter` and returns the following:
        
        - makes global space in `.text` for the function (using the name defined in the TACProc)
        - creates the stack frame based on the the number of `emitter._temps` (aligned to 16 bytes) (check line 250).

        - adds emitter._asm which is the emitted code for the function (in lines 241-248)

        - closing code for the stack frame.

    what interests us is now temps are decided in `emitter._temps` and then we can go into the `emitter(instr)` part of the code, as we need to implement new stack frames for nested functions, which will probably be the place where all the work is done.

    _temps is a dict that has the temp name : the temp index in the stack frame. _tparams is a dict with the parameters after the first 6, that are pushed to stack. what's strange is that _tparams have indexes back from zero, rather than

    so `emitter(instr)` calls one of the `_emit_...` functions with the names of the temporaries like "%11", and these are associated to the position in stack. for a nested function call, we do the following:
        - add the static link to the stack, such that the function can access it. the static link points to the 
