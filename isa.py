from __future__ import annotations

from enum import Enum
from typing import Any


class Opcode(Enum):
    PUSH = (0x01, 1)
    PUSHI = (0x02, 1)
    STORE = (0x03, 1)

    FETCH_A = (0x04, 0)
    STORE_A = (0x05, 0)
    SET_A = (0x06, 0)
    GET_A = (0x07, 0)
    INCA = (0x08, 0)

    DROP = (0x10, 0)
    DUP = (0x11, 0)
    SWAP = (0x12, 0)
    OVER = (0x13, 0)

    ADD = (0x20, 0)
    SUB = (0x21, 0)
    MUL = (0x22, 0)
    DIV = (0x23, 0)
    ADDC = (0x24, 0)

    AND = (0x30, 0)
    OR = (0x31, 0)
    NOT = (0x32, 0)

    JUMP = (0x40, 1)
    JZ = (0x41, 1)
    JN = (0x42, 1)
    CALL = (0x43, 1)
    RET = (0x44, 0)

    INPUT = (0x50, 1)
    OUTPUT = (0x51, 1)

    HALT = (0xFF, 0)

    def __init__(self, code: int, arg_count: int) -> None:
        self.code = code
        self.arg_count = arg_count

    def __str__(self) -> str:
        return self.name


class Instruction:
    def __init__(self, opcode: Opcode, arg: Any= None, labels: list[str] | None = None, addr: int| None = None) -> None:
        self.opcode = opcode
        self.arg = arg
        self.labels = labels if labels is not None else []
        self.addr = addr

    def __repr__(self) -> str:
        labels = f"labels = {self.labels}" if self.labels else ""
        addr = f"addr = {self.addr}" if self.addr is not None else ""

        return (
            f"{self.opcode} "
            f"{self.arg} "
            f"{labels} "
            f"{addr}"
        )

class Variable:
    def __init__(self, label: str, value: Any, addr: int | None = None, varType: VarType | None = None) -> None:
        self.label = label
        self.value = value
        self.addr = addr
        self.type = varType

    def __repr__(self) -> str:
        return f"{self.label} {self.value} addr = {self.addr}"


class VarType(Enum):
    INT = 1
    STRING = 2
    ARRAY = 3


binary_to_opcode = {op.code: op for op in Opcode}


def from_bytes_instruction(binary_instruction: bytearray) -> list[Instruction]:

    instructions: list[Instruction] = list()

    index = 0
    while index < len(binary_instruction):
        while binary_instruction[index] == 0x00:
            index += 4
            instructions.append(Instruction(Opcode.HALT, None, addr=index))
            if index == len(binary_instruction):
                return instructions

        for i in range(index, len(binary_instruction), 4):
            if binary_instruction[i] == 0x00:
                index = i
                break
            else:
                assert i % 4 == 0, f"opcode should be at the beginnig of word {i}"
                word = (
                    (binary_instruction[i] << 24)
                    | (binary_instruction[i + 1] << 16)
                    | (binary_instruction[i + 2] << 8)
                    | binary_instruction[i + 3]
                )
                opcode_bin = (word >> 24) & 0xFF
                arg = word & 0x00FFFFFF

                if arg & 0x00800000:
                    arg -= 0x01000000

                opcode = binary_to_opcode.get(opcode_bin)
                assert opcode is not None, f"wrong opcode: {binary_instruction[i]}"

                instruction = Instruction(opcode )

                instruction.addr = i // 4

                if opcode.arg_count:
                    instruction.arg = arg
                else:
                    assert arg == 0, f"arg {arg} should be 0 in instruction {opcode.name}"
                    instruction.arg = None

                instructions.append(instruction)

            index = i

    return instructions


def from_bytes_data(binary_data: bytearray) -> list[int]:

    memory: list[int] = list()

    for i in range(0, len(binary_data), 4):
        word = int.from_bytes(binary_data[i : i + 4], byteorder="big", signed=True)
        memory.append(word)

    return memory
