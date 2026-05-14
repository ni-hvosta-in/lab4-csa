import re
import sys

from isa import (
    Instruction,
    Opcode,
    Variable,
    VarType,
    is_number,
    is_valid_number,
    is_valid_number_param,
    is_valid_string,
)

name_to_opcode_dict: dict[str, Opcode] = {
    "push": Opcode.PUSH,
    "pushi": Opcode.PUSHI,
    "store": Opcode.STORE,
    "fetchA": Opcode.FETCH_A,
    "storeA": Opcode.STORE_A,
    "setA": Opcode.SET_A,
    "getA": Opcode.GET_A,
    "incA": Opcode.INCA,
    "drop": Opcode.DROP,
    "dup": Opcode.DUP,
    "swap": Opcode.SWAP,
    "over": Opcode.OVER,
    "add": Opcode.ADD,
    "sub": Opcode.SUB,
    "mul": Opcode.MUL,
    "div": Opcode.DIV,
    "addc": Opcode.ADDC,
    "and": Opcode.AND,
    "or": Opcode.OR,
    "not": Opcode.NOT,
    "jump": Opcode.JUMP,
    "jz": Opcode.JZ,
    "jn": Opcode.JN,
    "call": Opcode.CALL,
    "ret": Opcode.RET,
    "input": Opcode.INPUT,
    "output": Opcode.OUTPUT,
    "halt": Opcode.HALT,
}


def preprocess(lines: list[str]) -> list[str]:
    """Работа с макросами, условными компиляциями и константами"""
    defines = dict()
    result = []

    skip_stack = []

    for idx, line in enumerate(lines):
        line = strip_comments(line)
        if not line:
            continue

        tokens = line.split()
        key = tokens[0]

        if key == "#define":
            assert len(tokens) == 3, f"Invalid #define directive at line {idx + 1}"

            name = tokens[1]
            value = tokens[2]

            assert name not in defines, f"Duplicate #define {name} at line {idx + 1}"

            defines[name] = value
            continue

        if key == "if":
            assert len(tokens) == 2, f"Invalid ifdef directive at line {idx + 1}"

            name = tokens[1]
            skip_stack.append(name not in defines)
            continue

        if key == "endif":
            assert len(skip_stack) > 0, f"Invalid endif directive at line {idx + 1}"

            skip_stack.pop()
            continue

        if any(skip_stack):
            continue

        for i, token in enumerate(tokens):
            if token in defines:
                tokens[i] = defines[token]

        result.append(" ".join(tokens))

    assert len(skip_stack) == 0, "block if not closed"

    return result


def apply_macro(lines: list[str]) -> list[str]:

    macros = {}
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        tokens = get_tokens(line)

        key = tokens[0]

        if key == "macro":
            assert len(tokens) >= 2, f"Invalid macro directive at line {i + 1}"

            name = tokens[1]
            params = tokens[2:]

            body = []
            i += 1

            while not lines[i].startswith("endmacro"):
                body.append(lines[i])
                i += 1
                assert i < len(lines), "block macro not closed"

            macros[name] = (params, body)
            i += 1

            continue

        if key in macros:
            params, body = macros[key]
            args = tokens[1:]
            assert len(args) == len(params), f"Invalid macro directive at line {i + 1}"

            for line_macro in body:
                macro_tokens = get_tokens(line_macro)

                for j, tok in enumerate(macro_tokens):
                    for p, a in zip(params, args, strict=True):
                        if tok == p:
                            macro_tokens[j] = a

                result.append(" ".join(macro_tokens))

            i += 1
            continue

        result.append(line)
        i += 1

    return result


def get_tokens(line: str) -> list[str]:

    tokens = re.findall(r'"[^"]*"|\S+', line)
    tokens = list(map(lambda x: x.strip(" ,"), tokens))
    return tokens


def name_to_opcode(name: str) -> Opcode:
    """Отображение операторов исходного кода в коды операций."""
    return name_to_opcode_dict[name]


def special_directives() -> set[str]:
    """Множество допустимых директив исходного кода."""
    return {".org", ".data", ".text"}


def names_instructions() -> set[str]:
    """Множество допустимых операторов исходного кода."""
    return set(name_to_opcode_dict.keys())


def is_label(s: str) -> bool:
    return s.endswith(":")


def strip_comments(line: str) -> str:
    if ";" in line:
        return line.split(";")[0].strip()
    return line.strip()


def parse_instruction_and_variables(lines: list[str])\
        -> tuple[ list[tuple[int, list[Instruction]]], list[tuple[int, list[Variable]]]]:
    """Парсинг исходного кода на инструкции и переменные"""

    instructions: list[Instruction] = []

    variables: list[Variable] = []

    segments_text: list[tuple[int, list[Instruction]]] = []
    segments_data: list[tuple[int, list[Variable]]] = []

    global_variables = set()
    curr_text_org = 1
    curr_data_org = 0
    curr_section = None
    curr_instruction_labels: list[str] = []

    lines = preprocess(lines)
    lines = apply_macro(lines)
    start_section = False
    for idx, line in enumerate(lines):
        tokens = get_tokens(line)
        key = tokens[0]
        if curr_section is None:
            assert key in special_directives() and key != ".org", f"Expected section directive at line {idx + 1}"

        if key in special_directives():
            if key == ".org":
                assert len(tokens) == 2, f"Invalid .org directive at line {idx + 1}"

                assert start_section, f".org directive must be at the beginning of a section at line {idx + 1}"

                if curr_section == ".text":
                    if len(instructions) > 0:
                        segments_text.append((curr_text_org, instructions))
                        instructions = []

                    curr_text_org = int(tokens[1])
                    assert curr_text_org > 0, "Incorrect address"

                else:
                    if len(variables) > 0:
                        segments_data.append((curr_data_org, variables))
                        variables = []

                    curr_data_org = int(tokens[1])
                    assert curr_text_org >= 0, "Incorrect address"

            else:
                assert len(tokens) == 1, f"Invalid {key} directive at line {idx + 1}"

                curr_section = key
                start_section = True
                continue

        elif key in names_instructions():
            assert curr_section == ".text", f"Instructions must be in .text section at line {idx + 1}"

            opcode = name_to_opcode(key)
            assert len(tokens) == 1 + opcode.arg_count, f"Invalid number of arguments for {key} at line {idx + 1}"

            arg = None if opcode.arg_count == 0 else tokens[1]
            instruction = Instruction(name_to_opcode(key), arg, curr_instruction_labels.copy())

            instructions.append(instruction)

        else:
            assert is_label(key), f"Invalid token {key} at line {idx + 1}"

            if len(tokens) > 1:
                assert curr_section == ".data", f"Data labels must be in .data section at line {idx + 1}"

                label = key.strip(":")
                assert label not in global_variables, f"Duplicate label {label} at line {idx + 1}"
                variables.append(Variable(label, tokens[1:]))
                global_variables.add(label)

            else:
                assert curr_section == ".text", f"Instruction labels must be in .text section at line {idx + 1}"

                curr_instruction_labels.append(key.strip(":"))
                continue

        curr_instruction_labels.clear()
        start_section = False

    segments_text.append((curr_text_org, instructions))
    segments_data.append((curr_data_org, variables))

    return segments_text, segments_data


def arrange_instructions(
    segments_text: list[tuple[int, list[Instruction]]])\
        -> tuple[list[Instruction], dict[str, int], int]:
    """присвоение каждой инструкции своего адресса"""
    instruction_addr = 0

    used_addr = set()
    instructions_with_addr: list[Instruction] = []
    instruction_labels_addr: dict[str, int] = dict()
    start_addr = None
    for addr, instructions in segments_text:
        instruction_addr = addr
        for instruction in instructions:
            assert instruction_addr not in used_addr, (
                f"Memory address {instruction_addr} already occupied by another instruction"
            )

            for label in instruction.labels:
                assert label not in instruction_labels_addr, f"Duplicate label {label}"

                if label == "_start":
                    start_addr = instruction_addr

                instruction_labels_addr[label] = instruction_addr

            used_addr.add(instruction_addr)
            instruction.addr = instruction_addr
            instructions_with_addr.append(instruction)
            instruction_addr += 1

    assert start_addr is not None, "no label _start"

    return instructions_with_addr, instruction_labels_addr, start_addr


def arrange_variables(segments_data: list[tuple[int, list[Variable]]]) -> dict[str, Variable]:
    """присвоение каждой переменной своего адреса"""
    variables_addr: dict[str, Variable] = dict()
    variable_addr = 0

    for addr, variables in segments_data:
        variable_addr = addr
        for variable in variables:

            label = variable.label

            assert label not in variables_addr, f"Duplicate label {label}"
            variable.addr = variable_addr
            variables_addr[label] = variable

            if len(variable.value) == 1:
                arg = variable.value[0]
                if is_valid_string(arg):
                    arg = arg.strip('"')
                    variable_addr += len(arg) + 1
                    variable.value = arg
                    variable.type = VarType.STRING

                else:
                    assert is_valid_number(arg), f"variable should be number {arg}"
                    variable_addr += 1
                    variable.value = int(arg)
                    variable.type = VarType.INT

            else:
                variable.type = VarType.ARRAY
                new_array = []
                for arg in variable.value:
                    assert is_valid_number(arg)
                    new_array.append(int(arg))

                variable.value = new_array
                variable_addr += len(new_array)

    return variables_addr


def instruction_to_bin(
    instructions_with_addr: list[Instruction],
    instruction_labels_addr: dict[str, int],
    variable_addr: dict[str, Variable],
) -> bytearray:

    instruction_mem = bytearray(200 * 4)
    logs = []
    for instruction in instructions_with_addr:
        addr = instruction.addr
        opcode = instruction.opcode.code
        arg = instruction.arg
        int_val = 0

        if arg is not None:
            if not is_number(arg):
                assert arg in instruction_labels_addr or arg in variable_addr, f"Incorrect label {arg}"

                if arg in instruction_labels_addr:
                    int_val = instruction_labels_addr[arg]
                else:
                    var_addr = variable_addr[arg].addr
                    assert var_addr is not None
                    int_val = var_addr

            else:
                assert is_valid_number_param(arg), f"Invalid argument {arg}"
                int_val = int(arg, 0)

        opcode_byte = bytes([opcode])
        byte_val = int_val.to_bytes(3, byteorder="big", signed=True)

        full: bytes = opcode_byte + byte_val
        hex_code = full.hex()

        assert addr is not None
        mem_addr = addr * 4
        instruction_mem[mem_addr : mem_addr + 4] = full
        logs.append(f"{addr} - {hex_code} - {instruction.opcode.name} {int_val if instruction.arg else ''} \n")

    with open("instruction_logs.txt", "w") as f:
        f.writelines(logs)

    return instruction_mem


def data_to_bin(variables_addr: dict[str, Variable]) -> bytearray:

    variable_mem = bytearray(50 * 4)
    logs = []
    for variable in variables_addr.values():
        addr = variable.addr
        assert addr is not None

        mem_addr = addr * 4
        if variable.type == VarType.INT:
            num = variable.value
            variable_mem[mem_addr : mem_addr + 4] = num.to_bytes(4, byteorder="big", signed=True)
            logs.append(f"{addr} - {variable.label} - {num}\n")

        elif variable.type == VarType.STRING:
            string = variable.value

            for i, byte in enumerate((string + "\0").encode()):
                variable_mem[mem_addr : mem_addr + 4] = byte.to_bytes(4, "big", signed=True)
                logs.append(f"{addr + i} - string: {variable.label}[{i}] - {hex(byte)}\n")
                mem_addr += 4

        elif variable.type == VarType.ARRAY:
            array = variable.value
            for i, arg in enumerate(array):
                num = int(arg)
                variable_mem[mem_addr : mem_addr + 4] = num.to_bytes(4, byteorder="big", signed=True)
                logs.append(f"{addr} - array: {variable.label}[{i}] - {num}\n")
                addr += 1
                mem_addr += 4

    with open("variable_logs.txt", "w") as f:
        f.writelines(logs)

    return variable_mem


def main(source: str, target_instruction_file: str, target_data_file: str) -> None:

    with open(source) as f:
        lines = f.readlines()

    segments_text, segments_data = parse_instruction_and_variables(lines)

    instructions_with_addr, instruction_labels_addr, start_addr = arrange_instructions(segments_text)
    instructions_with_addr.insert(0, Instruction(opcode=Opcode.JUMP, arg = str(start_addr), addr = 0))
    variables_addr = arrange_variables(segments_data)

    instruction_mem = instruction_to_bin(instructions_with_addr, instruction_labels_addr, variables_addr)
    data_mem = data_to_bin(variables_addr)

    with open(target_instruction_file, "wb") as f:
        f.write(instruction_mem)

    with open(target_data_file, "wb") as f:
        f.write(data_mem)

    print("source LoC:", len(lines), "code instr:", len(instructions_with_addr))


if __name__ == "__main__":
    assert len(sys.argv) == 4, (
        "Wrong arguments: translator.py <input_file> <target_instruction_file> <target_data_file> "
    )
    _, source_file, target_instruction_file, target_data_file = sys.argv
    main(source_file, target_instruction_file, target_data_file)
