# Mano Compiler

Mano Compiler is a proof-of-concept compiler that converts a simple high-level
language into the 25-instruction assembly dialect accepted by the
[Mano Machine](http://en.wikipedia.org/wiki/Mano_machine). The result can then
be assembled and executed on a simulator.

The language supports integer, array and string data types, functions, and
textual output of any variable. Being a proof of concept, it also has some
flaws, including sharing of local variables (but not arguments) between
instances of the same function during recursion and lack of support for reading
input during runtime (partly due to lack of simulator support).

The compiler is written in Python 2 and does not use anything outside the
standard library. It is portable to any platform that supports Python, and can
be used to generate large amounts of assembly code to test new implementations
of the machine or its simulator.

## Usage

The compiler is invoked from the command line and passed the name of the file
containing the source code to be compiled, and optionally the name of the output
file. The -O flag can be used to produce optimized code.

Once compiled, the code can be run using a simulator. However, due to the lack
of linking, the runtime library used by the compiler (included in the
distribution) has to be loaded manually. In `manosim.exe`, the whole sequence of
assembling, loading and running a compiled program looks like this:

    * source lib
    [Some assembly information, including identifier list.]
    * source compiled_filename
    [Some more assembly information.]
    * go
    [Output of the program goes here.]

A language definition and some example code is included in the resources folder.

## Simulators

There are several simulators for the Mano machine, although each has its own
problems:

* [`manosim.exe` or `mano2.exe`](http://www.cs.albany.edu/~sdc/CSI404/), the one
    explicitly targeted by this compiler and included in the Windows
    distribution download works well, but it is a DOS program, and does not run
    natively on 64-bit Windows systems, much less any kind of UNIX. However, it
    can be convinced to work in DOSBox or on a 16- or 32-bit virtual Windows
    machine. I was unable to track down its source code to recompile it.
* [Mark Roth's ManoSimulator](http://octagonsoftware.com/home/mark/mano/) is a
    newer open-source implementation, and can be compiled on most platforms
    using modern tools with minor modifications. However, it lacks I/O support,
    so its practical usefulness is rather limited. It also uses a slightly
    different assembly syntax (slashes instead of semicolons for comments) and
    limits the maximum length of identifiers to 3 characters, which is
    incompatible with Mano Compiler (but not hard to remedy).
* [Basic Computer Simulator](http://code.google.com/p/basic-computer-simulator/)
    is a simulator with quite a rich GUI, written in Flash/ActionScript (of all
    things). It seems to work well, but lacks textual output capabilities and
    like Mark Roth's simulator, uses a slightly different syntax:
    * Labels are created using a colon rather than a comma.
    * Comments start with a double-slash rather than a semicolon.
    * There must be exactly one space between an instruction and its arguments.
    * OUT has no parameters (manosim requires an explicit AC).
    * Programs must end with the pseudo-instruction END.
* [javamanomachine](http://code.google.com/p/javamanomachine/) and
    [Mano Virtual Computer](http://cs.unco.edu/course/CS222/MANO/computer.htm)
    are two simulators written in Java, neither of which I could get to run
    properly, and my knowledge of Java is too limited to tinker with their code.

## License

This code is licensed under the MIT licence.
