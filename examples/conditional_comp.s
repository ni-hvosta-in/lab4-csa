#define ENABLE_MATH 1
#define VALUE 10

.text

macro PUSH_AND_DUP x
    pushi x
    dup
endmacro

_start:

if ENABLE_MATH

    PUSH_AND_DUP VALUE
    add

endif

    halt