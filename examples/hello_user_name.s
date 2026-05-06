.data
    start_mess: "What is your name?"
    hello: "Hello, "
    buff: ""

.text
_start:
    pushi start_mess
    call print

    call input_name

    pushi hello
    call print

    pushi buff
    call print

    halt

print:
    setA

print_loop:
    fetchA
    dup
    jz print_end

    output 1
    incA
    jump print_loop

print_end:
    drop
    ret

input_name:
    pushi buff
    setA

input_loop:
    input 2
    dup

    pushi 10
    sub
    jz input_end

    storeA
    incA
    jump input_loop

input_end:
    drop

    pushi 0
    storeA

    ret