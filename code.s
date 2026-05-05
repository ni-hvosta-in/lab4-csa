.data
.org 10
arr: 5, -12, 100, 99, 7, 42
len: 6
ans: 0
hello: "hello world"
.text
.org 10
_start:
    call func
    push ans
    output 1
    halt
func:
    pushi arr
    setA
    push len
 loop:
    fetchA
    dup
    push ans
    sub
    jn next
    drop
    store ans
    jump ld
next:
    drop
    drop
ld:
    pushi 1
    sub
    jz ret
    incA
    jump loop
ret:
    ret
