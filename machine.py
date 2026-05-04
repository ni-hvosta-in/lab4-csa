from AppData.Local.Programs.Python.Python312.Lib.test.test_print import dispatch
from isa import from_bytes_instruction, from_bytes_data, Instruction, Opcode
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
    SEL_PC_JZ = auto()
    SEL_PC_JN = auto()

    SEL_R_NEXT = auto()
    SEL_R_PREV = auto()


class ALU_Signal(Enum):

    ALU_ADD = auto()
    ALU_SUB = auto()
    ALU_MUL = auto()
    ALU_DIV = auto()
    ALU_AND = auto()
    ALU_OR = auto()

class Signal(Enum):

    LATCH_SP = auto()
    LATCH_AR = auto()
    LATCH_S = auto()
    LATCH_T = auto()
    LATCH_A = auto()
    LATCH_R = auto()
    LATCH_PC = auto()
    LATCH_MPC = auto()
    LATCH_IR = auto()

    WRITE_MEM = auto()
    WRITE_ST = auto()
    WRITE_RET = auto()
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

    controlUnit: ControlUnit = None

    def __init__(self, stack_size, data_memory: List[int], controlUnit: ControlUnit = None):

        self.stack_size = stack_size
        self.data_memory_size = len(data_memory)
        self.controlUnit = controlUnit

        self.stack = [0] * self.stack_size
        self.data_memory = data_memory

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

        assert sel in {
            Mux_Signal.SEL_SP_NEXT,
            Mux_Signal.SEL_SP_PREV
        }, f"internal error, latch_SP incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_SP_NEXT:
            self.sp_buff = self.sp + 1
        elif sel == Mux_Signal.SEL_SP_PREV:
            self.sp_buff = self.sp - 1

        assert 0 <= self.sp_buff < len(self.stack), f"index out of range stack: {self.sp_buff}"

    def signal_latch_S(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_S_TOP,
            Mux_Signal.SEL_S_STACK
        }, f"internal error, latch_S incorrect selector: {sel}"

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
            print(self.controlUnit.ir.arg)
            self.top_buff = self.controlUnit.ir.arg
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
            self.ar_buff = self.controlUnit.ir.arg
            assert self.ar_buff != None, f"wrong selector latch_AR {sel}"

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

class MicroInstr:

    latch = None
    sel = None

    def __init__(self, latch: Signal, sel: Mux_Signal = None):
        self.latch = latch
        self.sel = sel

    def __str__(self):
        return f"latch: {self.latch}, sel: {self.sel}"


class ControlUnit:

    program: List[Instruction] = None
    pc = None
    dataPath: DataPath = None

    mpc = None
    reg_R = None
    return_stack = None
    ir: Instruction = None
    _tick = None

    next_micro = MicroInstr(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_NEXT)
    next_sp = MicroInstr(Signal.LATCH_SP, Mux_Signal.SEL_SP_NEXT)
    prev_sp = MicroInstr(Signal.LATCH_SP, Mux_Signal.SEL_SP_PREV)
    s_from_top = MicroInstr(Signal.LATCH_S, Mux_Signal.SEL_S_TOP)
    fetch = MicroInstr(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_FETCH)
    write_st = MicroInstr(Signal.WRITE_ST)
    next_pc = MicroInstr(Signal.LATCH_PC, Mux_Signal.SEL_PC_NEXT)
    _microprogram = [
        #(Instructin Fetch)
        #(0)
        [MicroInstr(Signal.LATCH_IR), next_micro],
        #(1)
        [MicroInstr(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_OPCODE)],
        #(push addr)
        #(2)
        [MicroInstr(Signal.LATCH_AR, Mux_Signal.SEL_AR_CU), next_micro, next_sp],
        #(3)
        [write_st, s_from_top, MicroInstr(Signal.LATCH_T, Mux_Signal.SEL_T_MEM), next_pc, fetch],
        #(pushi val)
        #(4)
        [next_sp, next_micro],
        #(5)
        [write_st, s_from_top, MicroInstr(Signal.LATCH_T, Mux_Signal.SEL_T_IMM), next_pc, fetch]

    ]

    mpc_of_opcode = {
        Opcode.PUSH : 2,
        Opcode.PUSHI : 4
    }

    def __init__(self, dataPath: DataPath, program: List[Instruction], start):
        self.dataPath = dataPath
        self.program = program
        self.pc = start
        self._tick = 0
        self.reg_R = 0
        self.return_stack = [0] * 100
        self.mpc = 0

    def signal_latch_IR(self):
        assert self.pc < len(self.program), f"pc = {self.pc} out of range"

        self.ir = self.program[self.pc]

    def signal_latch_R(self, sel: Mux_Signal):

        assert sel in {Mux_Signal.SEL_R_NEXT, Mux_Signal.SEL_R_PREV}, f"internal error, latch_R incorrect selector: {sel}"

        if (sel == Mux_Signal.SEL_R_NEXT):
            self.reg_R += 1
        elif (sel == Mux_Signal.SEL_R_PREV):
            self.reg_R -= 1

        assert 0 <= self.reg_R < len(self.return_stack), f"index out of range returnStack: {self.reg_R}"

    def signal_latch_mPC(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_MPC_NEXT,
            Mux_Signal.SEL_MPC_OPCODE,
            Mux_Signal.SEL_MPC_FETCH
        }, f"internal error, latch_mPC incorrect selector: {sel}"

        if (sel == Mux_Signal.SEL_MPC_NEXT):
            self.mpc += 1
        elif (sel == Mux_Signal.SEL_MPC_FETCH):
            self.mpc = 0
        elif (sel == Mux_Signal.SEL_MPC_OPCODE):
            self.mpc = self.mpc_of_opcode.get(self.ir.opcode)
            print(self.mpc, self.ir)

    def signal_latch_PC(self, sel: Mux_Signal):

        assert sel in {
            Mux_Signal.SEL_PC_NEXT,
            Mux_Signal.SEL_PC_RET,
            Mux_Signal.SEL_PC_ADDR,
            Mux_Signal.SEL_PC_JN,
            Mux_Signal.SEL_PC_JZ
        }, f"internal error, latch_PC incorrect selector: {sel}"

        if (sel == Mux_Signal.SEL_PC_NEXT):
            self.pc += 1
        elif (sel == Mux_Signal.SEL_PC_ADDR):
            self.pc = self.arg
        elif (sel == Mux_Signal.SEL_PC_JN):
            self.pc = self.arg if self.dataPath.top < 0 else self.pc + 1
        elif (sel == Mux_Signal.SEL_PC_JZ):
            self.pc = self.arg if self.dataPath.top == 0 else self.pc + 1
        elif (sel == Mux_Signal.SEL_PC_RET):

            assert self.reg_R >= 0, f"return stack is empty"

            self.pc = self.return_stack[self.reg_R]

    def dispatch(self, microinstr: MicroInstr):

        assert microinstr.latch in Signal, f"wrong latch: {microinstr.latch}"
        sel: Mux_Signal = microinstr.sel

        if (microinstr.latch == Signal.LATCH_PC):
            self.signal_latch_PC(sel)

        elif (microinstr.latch == Signal.LATCH_R):
            self.signal_latch_R(sel)

        elif (microinstr.latch == Signal.LATCH_MPC):
            self.signal_latch_mPC(sel)

        elif (microinstr.latch == Signal.LATCH_IR):
            self.signal_latch_IR()

        elif (microinstr.latch == Signal.LATCH_AR):
            self.dataPath.signal_latch_AR(sel)

        elif (microinstr.latch == Signal.LATCH_SP):
            self.dataPath.signal_latch_SP(sel)

        elif (microinstr.latch == Signal.LATCH_S):
            self.dataPath.signal_latch_S(sel)

        elif (microinstr.latch == Signal.LATCH_T):
            self.dataPath.signal_latch_T(sel)

        elif (microinstr.latch == Signal.WRITE_ST):
            self.dataPath.signal_write_st()

        else:
            assert False, f"unknown latch: {microinstr.latch}"

    def sumulate(self):
        while self.ir == None or self.ir.opcode != Opcode.HALT:
            print(self.mpc)
            curr_tick = self._microprogram[self.mpc]
            self.dataPath.start_cycle()
            for m in curr_tick:
                self.dispatch(m)

            print(self)
            print(self.dataPath)
            self.dataPath.update()


    def __str__(self):
        return f"pc = {self.pc}, mpc = {self.mpc}"

def main(code_file, mem_file, input_file):
    with open(code_file, 'rb') as f:
        binary_instruction = f.read()

    print(binary_instruction)

    with open(mem_file, 'rb') as f:
        binary_memory = f.read()

    data = from_bytes_data(binary_memory)
    instructions = [Instruction(Opcode.PUSH, arg=16, addr = 0),
                    Instruction(Opcode.PUSH, arg=18, addr = 1),
                    Instruction(Opcode.PUSH, arg=19, addr = 1),
                    Instruction(Opcode.PUSHI, arg = 255, addr = 2),
                    Instruction(Opcode.HALT, addr = 2)]

    dp: DataPath = DataPath(10, data)
    cu: ControlUnit = ControlUnit(dp, instructions, start= 0)
    dp.controlUnit = cu
    cu.sumulate()


if __name__ == "__main__":
    main("instruction_memory.bin", "data_memory.bin", ".")