# Translator + processor model for Assembler

- Ковыршин Александр Сергеевич. Группа: P3217
- Преподававтель: Пенской Александр Владимирович.
- ` asm | stack | harv | mc | tick | binary | stream | port | cstr | prob1 | vector `

  
## Язык программирования
### Синтаксис:
``` ebnf
<program> ::= <section_data> <section_text> | <section_text> <section_data> | <section_text>

<section_data> ::= ".data\n" <declaration>*
<section_text> ::= ".text\n" (<label> | <instruction>)*

<declaration> ::= <label> (<array> | <reserve> | <string>)
<instruction> ::= <label_arg_command> | <number_arg_command> | <without_arg_command>

<label> ::= (<label_name> ":" (" ")*) | (<label_name> ":" (" ")* "\n")

<array> ::= <number> ("," <number>)*
<reserve> ::= "res" (" ")+ <number>
<string> ::= "\"" <char>* "\""

<label_arg_command> ::= ("push" | "store" | "jump" 
| "jz" | "jn" | "call") (" ")+ <label_name>

<number_arg_command> ::= ("pushi" | "input" | "output") (" ")+ <number>
<without_arg_command> ::= ("halt"
                          | "drop" | "dup" | "swap" | "over"
                          | "add" | "sub" | "mul" | "div"
                          | "and" | "or"
                          | "ret" 
                          | "fetchA" | "incA" | "storeA" | "setA" | "getA")

<number> ::= [-2^32; 2^32 - 1]
<char> ::= any ASCII character except '"'
<label_name> ::= (<letter_or_>)+
<letter_or_> ::= <letter> | ("_")
<letter> ::= [a-z] | [A-Z]
``` 

### Семантика команд

#### Секции программы

- `.text` - секция, в которой все последующие записи интерпретируются как инструкции, их аргументы, метки и комментарии.
- `.data` - секция, в которой объявляются и инициализируются данные, размещаемые в памяти данных.

---

#### Метки

- `label` - имя, обозначающее адрес:
  - в `.text` - адрес инструкции, следующей за меткой;
  - в `.data` - адрес первого элемента соответствующего участка памяти.

---

#### Работа с данными

- `push addr` - помещает значение `mem[addr]` на вершину стека.
В силу гарвардской архитектуры `addr` может указывать только на данные (Data Memory).
- `pushi value` - помещает значение `value` на вершину стека.
- `store addr` - извлекает значение с вершины стека и записывает его в `mem[addr]`.
- `fetchA` - помещает значение `mem[A]` на вершину стека.
- `incA` - увеличивает значение регистра `A` на 1.
- `storeA` - записывает значение с вершины стека в `mem[A]`.
- `setA` - записывает значение с вершины стека в `A`.
- `getA` - помещает значение `A` на вершину стека.
---

#### Операции со стеком

- `drop` - удаляет верхний элемент стека.
- `dup` - дублирует верхний элемент стека.
- `swap` - меняет местами два верхних элемента стека.
- `over` - копирует второй элемент стека на вершину.

---

#### Арифметические операции

Операции выполняются над двумя верхними элементами стека.

- `add` - складывает два верхних значения, результат помещается на вершину стека.
- `sub` - вычитает верхний элемент из второго элемента стека, результат помещается на вершину.
- `mul` - перемножает два верхних значения.
- `div` - делит второй элемент стека на верхний элемент, результат помещается на вершину стека.
---

#### Логические операции

- `and` - побитовое И двух верхних элементов стека.
- `or` - побитовое ИЛИ двух верхних элементов стека.

---

### Управление потоком выполнения

- `jump label` - безусловно передаёт управление на инструкцию, обозначенную меткой.

- `jz label` - выполняет переход, если значение на вершине стека равно 0.

- `jn label` - выполняет переход, если значение на вершине стека меньше 0.
> Условные переходы проверяют значение на вершине стека и не удаляют его.

---

#### Вызовы процедур

- `call label` - сохраняет адрес следующей инструкции в стек вызовов и передаёт управление по метке.
- `ret` - извлекает адрес из стека вызовов и передаёт управление обратно.

---

#### Ввод-вывод

- `input n` - считывает один символ из порта `n` и помещает его на вершину стека.
- `output n` - записывает значение с вершины стека в порт `n`.

---

- `halt` - завершает выполнение программы.

---

В программе не может быть дублирующихся меток.
Метка памяти данных задается на той же строке, что и данные:
``` asm 
hello_world: "Hello, world!"
```

Метка памяти команд задается на строке предшетсвующей инструкции, на которую указывает метка:
```
foo:
    push 10
    ...
```

### Область видимости

В любом месте секции .text доступен стэк и операции над его верхними значениями

### Типизация, виды литералов

Литералы могут быть представлены в виде чисел и меток (в последствии интерпретируются как числа), в секции .data можно объявлять строки. Типизация отсутсвует, так как пользователь языка может интерпретировать любые данные как захочет и может с ними выполнить любые из возможных операций.

## Организация памяти

- Гарвардская архитектура
- Размер машинного слова:
  - Память данных - 32 бит;
  - Память команд - 32 бит.
- Адресации:
  - Прямая абсолютная (например, `push label`)

**Набор инструкций:**
| Номер  | Название команды   | Сигналы                                                                     |
|--------|--------------------|-----------------------------------------------------------------------------|
| 0      | Instruction Fetch  | sel_mpc_opcode, latch_mPC                                                   |
| 1      | push addr | sel_AR_CU, latch_AR, sel_SP_next, latch_SP, sel_mpc_next, latch_mpc |
| 2      |           | write_st, sel_S_top, sel_T_mem, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC | 
| 3      | pushi val | sel_SP_next, latch_SP, sel_mpc_next, latch_mpc | 
| 4      |           | write_st, sel_S_top, sel_T_imm, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC| 
| 5      | store addr| sel_AR_CU, latch_AR, sel_mpc_next, latch_mpc |
| 6      |           | write_dm, sel_T_second, sel_S_stack, sel_SP_prev, latch_SP, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 7      | fetchA    | sel_AR_A, latch_AR, sel_SP_next, latch_SP,sel_mpc_next, latch_mpc |
| 8      |           | write_st,  sel_S_top, sel_T_mem, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC | 
| 9      | incA      | sel_A_inc, latch_A, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 10      | storeA    | sel_AR_A, latch_AR, sel_mpc_next, latch_mpc |
| 11     |           | write_dm, sel_T_second, sel_S_stack, sel_SP_prev, latch_SP, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 12     | setA      | sel_A_T, sel_T_second, sel_S_stack, sel_SP_prev, latch_A, latch_S, latch_T, latch_SP, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 13     | getA      | sel_SP_next, latch_SP, sel_mpc_next, latch_mpc |
| 14     |           | write_st, sel_S_top, sel_T_A, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC| 
| 15     | drop      | sel_T_second, sel_S_stack, sel_SP_prev, latch_SP, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 16     | dup       | sel_SP_next, latch_SP, sel_mpc_next, latch_mpc |
| 17     |           | write_st, sel_S_top, latch_S, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 18     | swap      | sel_T_second, sel_S_top, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 19     | over      | sel_SP_next, latch_SP, sel_mpc_next, latch_mpc |
| 20     |           | write_st, sel_T_second, sel_S_top, latch_T, latch_S, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 21     | add       | sel_S_stack, sel_SP_prev, alu_add, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 22    | sub       | sel_S_stack, sel_SP_prev, alu_sub, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 23     | mul       | sel_S_stack, sel_SP_prev, alu_mul, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 24     | div       | sel_S_stack, sel_SP_prev, alu_div, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 25     | and       | sel_S_stack, sel_SP_prev, alu_and, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 26     | or        | sel_S_stack, sel_SP_prev, alu_or, sel_T_alu, latch_S, latch_SP, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |
| 27     | jump   label   | sel_PC_addr, latch_PC, sel_mpc_fetch, latch_mpc |
| 28     | jz   label     | jump_type_Z, sel_PC_addr, latch_PC, sel_mpc_fetch, latch_mpc |
| 29     | jn   label     | jump_type_N, sel_PC_addr, latch_PC, sel_mpc_fetch, latch_mpc |
| 30     | call   label   | sel_R_next, latch_R, sel_mpc_next, latch_mpc|
| 31     |           | write_ret, sel_PC_addr, latch_PC, sel_mpc_fetch, latch_mpc |
| 32     | ret       | sel_PC_ret, sel_R_prev, latch_R, latch_PC, sel_mpc_fetch, latch_mpc |
| 33     | input n   | sel_SP_next, latch_SP, sel_mpc_next, latch_mpc   |
| 34     |           | write_st, sel_S_top, sel_T_input, latch_S, latch_T, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC | 
| 35     | output n  | write_io, sel_T_second, sel_S_stack, sel_SP_prev, latch_A, latch_S, latch_T, latch_SP, sel_mpc_fetch, latch_mpc, sel_PC_next, latch_PC |