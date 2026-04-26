from enum import Enum

from enum import Enum

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