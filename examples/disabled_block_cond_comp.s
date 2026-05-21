#define PORT 1
#define ENABLE_IO 1

.text

macro PUSH2 a b
    pushi a
    pushi b
endmacro

macro OUTPUT_NUM x
    pushi x
    output PORT
endmacro

_start:

    PUSH2 5 7
    add
    output PORT

if ENABLE_IO
    OUTPUT_NUM 123
endif

if DISABLED
    OUTPUT_NUM 999
endif

    halt