from enum import Enum

from enum import Enum
from typing import List


class Opcode(Enum):

    PUSH   = (0x01, 1)
    PUSHI  = (0x02, 1)
    STORE  = (0x03, 1)

    FETCH_A = (0x04, 0)
    STORE_A = (0x05, 0)
    SET_A   = (0x06, 0)
    GET_A   = (0x07, 0)
    INCA    = (0x08, 0)

    DROP = (0x10, 0)
    DUP  = (0x11, 0)
    SWAP = (0x12, 0)
    OVER = (0x13, 0)

    ADD = (0x20, 0)
    SUB = (0x21, 0)
    MUL = (0x22, 0)
    DIV = (0x23, 0)

    AND = (0x30, 0)
    OR  = (0x31, 0)

    JUMP = (0x40, 1)
    JZ   = (0x41, 1)
    JN   = (0x42, 1)
    CALL = (0x43, 1)
    RET  = (0x44, 0)

    INPUT  = (0x50, 1)
    OUTPUT = (0x51, 1)

    HALT = (0xFF, 0)

    def __init__(self, code, arg_count):
        self.code = code
        self.arg_count = arg_count

    def __str__(self):
        return self.name


class Instruction:

    def __init__(self, opcode: Opcode = None, arg: str = None, label: str = None, addr: int = None):
        self.opcode = opcode
        self.arg = arg
        self.label = label
        self.addr = addr

    def __repr__(self):
        return f"{self.opcode} {self.arg} {"label = " + self.label if self.label else ''} {"addr = " + str(self.addr) if self.addr else ''}"


class Variable:

    def __init__(self, label: str, value, addr: int = None, varType: VarType = None):
        self.label = label
        self.value = value
        self.addr = addr
        self.type = varType

    def __repr__(self):
        return f"{self.label} {self.value} addr = {self.addr}"


class VarType(Enum):
    INT = 1
    STRING = 2
    ARRAY = 3



binary_to_opcode = {op.code: op for op in Opcode}

def from_bytes_instruction(binary_instruction: bytearray) -> List[Instruction]:

    instructions: List[Instruction] = list()

    index = 0
    while index < len(binary_instruction):

        while binary_instruction[index] == 0x00:
            index += 1
            if index == len(binary_instruction):
                return instructions

        for i in range(index, len(binary_instruction), 4):

            if binary_instruction[i] == 0x00:
                index = i
                break
            else:

                assert i % 4 == 0, f"opcode should be at the beginnig of word {i}"
                word = (binary_instruction[i] << 24) | (binary_instruction[i + 1] << 16) | (binary_instruction[i + 2] << 8) | binary_instruction[i + 3]
                opcode_bin = (word >> 24) & 0xFF
                arg = word & 0x00FFFFFF

                instruction = Instruction()
                opcode = binary_to_opcode.get(opcode_bin)

                assert opcode != None, f"wrong opcode: {binary_instruction[i]}"

                instruction.opcode = opcode
                instruction.addr = i // 4

                if opcode.arg_count:
                    instruction.arg = arg
                else:

                    assert arg == 0, f"arg {arg} should be 0 in instruction {opcode.name}"
                    instruction.arg = None

                instructions.append(instruction)

            index = i

    return instructions

def from_bytes_data(binary_data: bytearray) -> List[int]:

    memory: List[int] = list()

    for i in range(0, len(binary_data), 4):
        word = (binary_data[i] << 24) | (binary_data[i + 1] << 16) | (binary_data[i + 2] << 8) | \
               binary_data[i + 3]

        memory.append(hex(word))

    return memory