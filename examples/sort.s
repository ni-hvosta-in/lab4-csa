.data
size: 0
i: 0
j: 0
tmp1: 0
tmp2: 0

array: 0 0 0 0 0 0 0 0 0 0

.text

_start:
    call read_array
    call bubble_sort
    call print_array
    halt

; =====================================

read_array:
    pushi array
    setA

read_loop:
    input 1
    dup
    jz read_end

    storeA
    incA

    ; size++

    push size
    pushi 1
    add
    store size

    jump read_loop

read_end:
    ret

; =====================================

bubble_sort:

    ; i = 0

    pushi 0
    store i

outer_loop:

    push size
    push i
    sub
    jz sort_end

    ; j = 0

    pushi 0
    store j

inner_loop:

    push size
    push j
    sub
    pushi 1
    sub
    jz next_outer

    pushi array
    setA

    push j

addr_loop:
    dup
    jz addr_done

    incA

    pushi 1
    sub

    jump addr_loop

addr_done:
    drop

    ; tmp1 = array[j]

    fetchA
    store tmp1

    ; tmp2 = array[j+1]

    incA
    fetchA
    store tmp2

    push tmp1
    push tmp2
    sub

    dup
    jn no_swap

    pushi array
    setA

    push j

swap_addr_loop:
    dup
    jz swap_addr_done

    incA

    pushi 1
    sub

    jump swap_addr_loop

swap_addr_done:
    drop

    ; array[j] = tmp2

    push tmp2
    storeA

    ; array[j+1] = tmp1

    incA

    push tmp1
    storeA

    jump after_swap

no_swap:
    drop

after_swap:

    ; j++

    push j
    pushi 1
    add
    store j

    jump inner_loop

next_outer:

    ; i++

    push i
    pushi 1
    add
    store i

    jump outer_loop

sort_end:
    ret

; =====================================

print_array:

    ; i = 0

    pushi 0
    store i

print_loop:

    push size
    push i
    sub
    jz print_end

    ; A = &array[i]

    pushi array
    setA

    push i

print_addr_loop:
    dup
    jz print_addr_done

    incA

    pushi 1
    sub

    jump print_addr_loop

print_addr_done:
    drop

    fetchA
    output 2

    ; i++

    push i
    pushi 1
    add
    store i

    jump print_loop

print_end:
    ret