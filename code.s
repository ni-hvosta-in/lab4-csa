.data
.org 10
arr: 5, -12, 3, 99, 7, 42
len: 6
ans: 0
hello: "hello world"
.text
.org 10
_start:
    push arr
    dup
    setA

    fetchA              ; первый элемент → max
    push len
    fetchA
    pushi 100
    sub            ; осталось n-1

while:
    swap           ; [n, max]

    dup
    jz return

    swap           ; [max, n]

    fetchA              ; val → [max, n, val]

    over           ; [max, n, val, max]
    sub            ; val - max

    jn keep        ; если val <= max → оставить

    ; update max
    drop           ; убрать diff
    swap           ; [max, n, val] → [val, n, max]
    drop           ; убрать старый max
    jump cont

keep:
    drop           ; убрать diff

cont:
    swap           ; [n, max]
    pushi 1
    sub            ; n--

    incA
    jump while

.text
.org 200;
return:
    drop           ; убрать n
    push ans
    store ans
    halt