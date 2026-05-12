macro print_char value
    pushi value
    output 1
endmacro

.text
_start:
    print_char 72
    print_char 105
    halt