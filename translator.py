from Opcode import Opcode
from typing import Dict

def name_to_opcode() -> Dict[str, Opcode]:
    """Отображение операторов исходного кода в коды операций."""
    return {

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
        "and": Opcode.AND,
        "or": Opcode.OR,
        "jump": Opcode.JUMP,
        "jz": Opcode.JZ,
        "jn": Opcode.JN,
        "call": Opcode.CALL,
        "ret": Opcode.RET,
        "input": Opcode.INPUT,
        "output": Opcode.OUTPUT,
        "halt": Opcode.HALT
        
    }

def special_directives() -> set:
    """Множество допустимых директив исходного кода."""
    return {".org", ".data", ".text"}

def names_instructions() -> set:
    """Множество допустимых операторов исходного кода."""
    return set(name_to_opcode().keys())

def is_label(s: str) -> bool:
    return s.endswith(':')

def strip_comments(line: str) -> str:
    if ';' in line:
        return line.split(';')[0].strip()
    return line.strip()

def main(source: str, instruction_memory: str, data_memory: str):
    
    with open(source, 'r') as f:
        lines = f.readlines()

    intructions = []

    variables = []

    segments_text = []
    segments_data = []
    
    global_variables = set()
    curr_text_org = 0
    curr_data_org = 0
    curr_section = None
    

    for idx, line in enumerate(lines):
        line = strip_comments(line)
        if not(line):
            continue
        
        tokens = line.split()
        tokens = list(map(lambda x: x.strip(" ,"), tokens))
        key = tokens[0]
        if (curr_section is None):
            assert key in special_directives() and key != ".org", f"Expected section directive at line {idx+1}"

        if key in special_directives():         

            if key == ".org":
                assert len(tokens) == 2, f"Invalid .org directive at line {idx+1}"

                assert start_section, f".org directive must be at the beginning of a section at line {idx+1}"
                
                if curr_section == ".text":
                    if (len(intructions) > 0):
                        segments_text.append((curr_text_org, intructions))
                        intructions = []

                    curr_text_org = int(tokens[1])

                else:
                    if (len(variables) > 0):
                        segments_data.append((curr_data_org, variables))
                        variables = []

                    curr_data_org = int(tokens[1])


            else:
                assert len(tokens) == 1, f"Invalid {key} directive at line {idx+1}"

                curr_section = key
                start_section = True
                continue

        elif key in names_instructions():
            assert curr_section == ".text", f"Instructions must be in .text section at line {idx+1}"
            
            opcode = name_to_opcode()[key]
            assert len(tokens) == 1 + opcode.arg_count, f"Invalid number of arguments for {key} at line {idx+1}"
            
            instruction = name_to_opcode()[key]
            args = tokens[1:]
            intructions.append((instruction, args))
        
        else:
            assert is_label(key), f"Invalid token {key} at line {idx+1}"

            if len(tokens) > 1:
                assert curr_section == ".data", f"Data labels must be in .data section at line {idx+1}"

                label = key.strip(':')
                assert label not in global_variables, f"Duplicate label {label} at line {idx+1}"
                variables.append((label, tokens[1:]))
                global_variables.add(label)

        start_section = False

    segments_text.append((curr_text_org, intructions))
    segments_data.append((curr_data_org, variables))
            

    print(segments_text)
    print(segments_data)


if __name__ == "__main__":
    main("code.s", "instruction_memory.txt", "data_memory.txt")