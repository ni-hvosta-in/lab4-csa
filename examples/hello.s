.data
.org 10
    message: "hello world"
    
.text
.org 10
_start:
    pushi message
    setA
loop:
    fetchA
    dup
    jz ret
    output 1
    incA
    jump loop
ret:
    halt
