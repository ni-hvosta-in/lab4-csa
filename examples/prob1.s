.data
ans: 0

.text

_start:

    pushi 110

while_i:

    dup
    pushi 1000
    sub
    jn continue_i

    jump finish

continue_i:

    pushi 100

while_j:

    dup
    pushi 1000
    sub
    jn continue_j

    jump next_i

continue_j:

    over
    over
    mul

    dup

    dup
    call reverse_number

    sub
    jz palindrome

not_palindrome:

    drop

next_j:

    pushi 1
    add

    jump while_j

palindrome:

    dup
    push ans
    sub
    jn skip_store

    dup
    store ans

skip_store:

    drop

    jump next_j

next_i:

    drop

    pushi 11
    add

    jump while_i

finish:

    push ans
    output 1
    halt


reverse_number:

    pushi 0

reverse_loop:

    over
    jz reverse_done

    over
    pushi 10
    call mod

    swap
    pushi 10
    mul
    add

    swap
    pushi 10
    div
    swap

    jump reverse_loop

reverse_done:

    swap
    drop

    ret

mod:

    over
    over

    div
    mul
    sub

    ret