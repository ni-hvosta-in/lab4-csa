#define PORT 1
#define OUT 2
.text
_start:
loop:
    input PORT
    dup
    jz end
    output OUT
    jump loop
end:
    halt