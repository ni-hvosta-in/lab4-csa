from AppData.Local.Programs.Python.Python312.Lib import random
from isa import from_bytes_instruction, from_bytes_data
from typing import List
from enum import Enum, auto

class Mux_Signal(Enum):

    SEL_SP_NEXT = auto()
    SEL_SP_PREV = auto()

    SEL_S_STACK = auto()
    SEL_S_TOP = auto()

    SEL_T_SECOND = auto()
    SEL_T_ALU = auto()
    SEL_T_IMM = auto()
    SEL_T_A = auto()
    SEL_T_MEM = auto()
    SEL_T_INPUT = auto()

    SEL_A_INC = auto()
    SEL_A_T = auto()

    SEL_AR_A = auto()
    SEL_AR_CU = auto()

    SEL_MPC_OPCODE = auto()
    SEL_MPC_FETCH = auto()
    SEL_MPC_NEXT = auto()

    SEL_PC_RET = auto()
    SEL_PC_NEXT = auto()
    SEL_PC_ADDR = auto()

    SEL_RET_NEXT = auto()
    SEL_RET_PREV = auto()

    JUMP_TYPE_N = auto()
    JUMP_TYPE_Z = auto()

class ALU_Signal(Enum):

    ALU_ADD = auto()
    ALU_SUB = auto()
    ALU_MUL = auto()
    ALU_DIV = auto()
    ALU_AND = auto()
    ALU_OR = auto()

class Signal(Enum):

    # Stack operations
    DATA_STACK_PUSH = auto()
    DATA_STACK_POP = auto()
    RETURN_STACK_PUSH = auto()
    RETURN_STACK_POP = auto()

    LATCH_SP = auto()
    LATCH_AR = auto()
    LATCH_S = auto()
    LATCH_T = auto()
    LATCH_A = auto()
    LATCH_R = auto()
    LATCH_PC = auto()
    LATCH_MPC = auto()



    MEMORY_WRITE = auto()
    OUTPUT = auto()
    INPUT = auto()


class DataPath:

    sp = None
    stack_size = None
    stack = None

    data_memory_size = None
    data_memory = None

    second = None
    top = None
    ar = None
    reg_A = None
    alu_res = None

    top_buff = None
    second_buff = None
    sp_buff = None
    ar_buff = None
    reg_A_buff = None


    def __init__(self, stack_size, data_memory_size):

        self.stack_size = stack_size
        self.data_memory_size = data_memory_size

        self.stack = [0] * self.stack_size
        self.data_memory = [0] * self.data_memory_size

        self.sp = -1
        self.ar = 0
        self.reg_A = 0
        self.second = 0
        self.top = 0
        self.alu_res = 0

    def start_cycle(self):
        self.sp_buff = self.sp
        self.ar_buff = self.ar
        self.reg_A_buff = self.reg_A
        self.second_buff = self.second
        self.top_buff = self.top

    def update(self):
        self.sp = self.sp_buff
        self.ar = self.ar_buff
        self.reg_A = self.reg_A_buff
        self.second = self.second_buff
        self.top = self.top_buff

    def signal_latch_SP(self, sel: Mux_Signal):

        assert sel in {Mux_Signal.SEL_SP_NEXT, Mux_Signal.SEL_SP_PREV}, f"internal error, latch_SP incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_SP_NEXT:
            self.sp_buff += 1
        elif sel == Mux_Signal.SEL_SP_PREV:
            self.sp_buff -= 1

        assert 0 <= self.sp_buff

    def signal_latch_S(self, sel: Mux_Signal):

        assert sel in {Mux_Signal.SEL_S_TOP, Mux_Signal.SEL_S_STACK}, f"internal error, latch_S incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_S_TOP:
            self.second_buff = self.top
        elif sel == Mux_Signal.SEL_S_STACK:

            assert self.sp > -1, f"stack is empty"

            self.second_buff = self.stack[self.sp]

    def signal_latch_T(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_T_SECOND,
            Mux_Signal.SEL_T_ALU,
            Mux_Signal.SEL_T_IMM,
            Mux_Signal.SEL_T_A,
            Mux_Signal.SEL_T_MEM,
            Mux_Signal.SEL_T_INPUT
        }, f"internal error, latch_T incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_T_SECOND:
            self.top_buff = self.second
        elif sel == Mux_Signal.SEL_T_ALU:
            self.top_buff = self.alu_res
        elif sel == Mux_Signal.SEL_T_IMM:
            self.top_buff = random.randint(0, 5)     # test value
        elif sel == Mux_Signal.SEL_T_A:
            self.top_buff = self.reg_A
        elif sel == Mux_Signal.SEL_T_MEM:
            self.top_buff = self.data_memory[self.ar]
        elif sel == Mux_Signal.SEL_T_INPUT:
            pass

    def signal_latch_AR(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_AR_A,
            Mux_Signal.SEL_AR_CU
        }, f"internal error, latch_AR incorrect selector: {sel}"

        if (sel == Mux_Signal.SEL_AR_A):
            self.ar_buff = self.reg_A
        elif (sel == Mux_Signal.SEL_AR_CU):
            pass

    def signal_latch_A(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_A_T,
            Mux_Signal.SEL_A_INC
        }, f"internal error, latch_A incorrect selector: {sel}"

        if (Mux_Signal.SEL_A_T):
            self.reg_A_buff = self.T
        elif (Mux_Signal.SEL_A_INC):
            self.reg_A_buff = self.reg_A + 1

    def signal_write_st(self):

        assert self.sp > -1, f"stack is empty"

        self.stack[self.sp] = self.second

    def signal_write_dm(self):

        assert -1 <= self.ar <= self.data_memory_size, f"incorrect ar = {self.ar}"

        self.data_memory_size[self.ar] = self.top

    def alu(self, sel: ALU_Signal):

        assert sel in ALU_Signal, f"internal error, alu incorrect selector: {sel}"

        if (sel == ALU_Signal.ALU_ADD):
            self.alu_res = self.top + self.second
        elif (sel == ALU_Signal.ALU_SUB):
            self.alu_res = self.second - self.top
        elif (sel == ALU_Signal.ALU_MUL):
            self.alu_res = self.second * self.top
        elif (sel == ALU_Signal.ALU_DIV):
            self.alu_res = self.second // self.top
        elif (sel == ALU_Signal.ALU_AND):
            self.alu_res = self.second & self.top
        elif (sel == ALU_Signal.ALU_OR):
            self.alu_res = self.second | self.top

    def __str__(self):
        return f"stack: {self.stack}, sp: {self.sp}, top: {self.top}, second: {self.second}"

def main(code_file, mem_file, input_file):
    with open(code_file, 'rb') as f:
        binary_instruction = f.read()

    print(binary_instruction)

    with open(mem_file, 'rb') as f:
        binary_memory = f.read()

    print(binary_memory)
    print(from_bytes_data(binary_memory))
    print(from_bytes_instruction(binary_instruction))

    dp: DataPath = DataPath(10, len(binary_memory))
    dp.start_cycle()
    dp.signal_latch_SP(Mux_Signal.SEL_SP_NEXT)
    dp.update()
    dp.start_cycle()
    dp.signal_write_st()
    dp.signal_latch_S(Mux_Signal.SEL_S_TOP)
    dp.signal_latch_T(Mux_Signal.SEL_T_IMM)
    dp.update()

    print(dp)

    dp.start_cycle()
    dp.signal_latch_SP(Mux_Signal.SEL_SP_NEXT)
    dp.update()
    dp.start_cycle()
    dp.signal_write_st()
    dp.signal_latch_S(Mux_Signal.SEL_S_TOP)
    dp.signal_latch_T(Mux_Signal.SEL_T_IMM)
    dp.update()

    print(dp)

    dp.start_cycle()
    dp.signal_latch_SP(Mux_Signal.SEL_SP_NEXT)
    dp.update()
    dp.start_cycle()
    dp.signal_write_st()
    dp.signal_latch_S(Mux_Signal.SEL_S_TOP)
    dp.signal_latch_T(Mux_Signal.SEL_T_IMM)
    dp.update()

    print(dp)

    dp.start_cycle()
    dp.signal_latch_S(Mux_Signal.SEL_S_TOP)
    dp.signal_latch_T(Mux_Signal.SEL_T_SECOND)
    dp.alu(ALU_Signal.ALU_ADD)
    dp.update()
    print(dp)
    print(dp.alu_res)


if __name__ == "__main__":
    main("instruction_memory.bin", "data_memory.bin", ".")