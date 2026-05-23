from __future__ import annotations

import sys
from enum import Enum, auto

from isa import Instruction, Opcode, from_bytes_data, from_bytes_instruction, parse_input

MASK32 = 0xFFFFFFFF
SIGN32 = 0x80000000


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

    SEL_SP_READ_WRITE_SP = auto()
    SEL_SP_READ_WRITE_NEXT = auto()

class ALU_Signal(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    ADDC = auto()
    AND = auto()
    OR = auto()
    NOT = auto()


class Signal(Enum):
    LATCH_SP = auto()
    LATCH_AR = auto()
    LATCH_S = auto()
    LATCH_T = auto()
    LATCH_A = auto()
    LATCH_R = auto()
    LATCH_PC = auto()
    LATCH_MPC = auto()

    WRITE_DM = auto()
    WRITE_ST = auto()
    WRITE_RET = auto()

    WRITE_IO = auto()

    SELECT_CURR_SP = auto()

    ALU = auto()


class DataPath:
    sp: int
    stack_size: int
    stack: list[int]

    data_memory_size: int
    data_memory: list[int]

    second: int
    top: int
    ar: int
    reg_A: int
    alu_res: int

    top_buff: int
    second_buff: int
    sp_buff: int
    ar_buff: int
    reg_A_buff: int

    sp_read_write: int
    controlUnit: ControlUnit

    io_ports: dict[int, list[int]]

    def __init__(self, stack_size: int, data_memory: list[int], io_ports: dict[int, list[int]]):

        self.stack_size = stack_size
        self.data_memory_size = len(data_memory)

        self.stack = [0] * self.stack_size
        self.data_memory = data_memory

        self.sp = -1
        self.ar = 0
        self.reg_A = 0
        self.second = 0
        self.top = 0
        self.alu_res = 0
        self.flag_N = 0
        self.flag_Z = 1
        self.flag_V = 0
        self.flag_C = 0
        self.io_ports = io_ports

    def start_cycle(self) -> None:
        self.sp_buff = self.sp
        self.ar_buff = self.ar
        self.reg_A_buff = self.reg_A
        self.second_buff = self.second
        self.top_buff = self.top

    def update(self) -> None:
        self.sp = self.sp_buff
        self.ar = self.ar_buff
        self.reg_A = self.reg_A_buff
        self.second = self.second_buff
        self.top = self.top_buff

    def signal_latch_SP(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_SP_NEXT, Mux_Signal.SEL_SP_PREV}, (
            f"internal error, latch_SP incorrect selector: {sel}"
        )

        if sel == Mux_Signal.SEL_SP_NEXT:
            self.sp_buff = self.sp + 1
        elif sel == Mux_Signal.SEL_SP_PREV:
            self.stack[self.sp] = 0
            self.sp_buff = self.sp - 1

        assert -1 <= self.sp_buff < len(self.stack), f"index out of range stack: {self.sp_buff}"

    def signal_latch_S(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_S_TOP, Mux_Signal.SEL_S_STACK}, (
            f"internal error, latch_S incorrect selector: {sel}"
        )

        if sel == Mux_Signal.SEL_S_TOP:
            self.second_buff = self.top
        elif sel == Mux_Signal.SEL_S_STACK:
            assert self.sp > -1, "stack is empty"
            self.sp_read_write = self.sp
            self.second_buff = self.stack[self.sp_read_write]

    def signal_latch_T(self, sel: Mux_Signal) -> None:

        assert sel in {
            Mux_Signal.SEL_T_SECOND,
            Mux_Signal.SEL_T_ALU,
            Mux_Signal.SEL_T_IMM,
            Mux_Signal.SEL_T_A,
            Mux_Signal.SEL_T_MEM,
            Mux_Signal.SEL_T_INPUT,
        }, f"internal error, latch_T incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_T_SECOND:
            self.top_buff = self.second

        elif sel == Mux_Signal.SEL_T_ALU:
            self.top_buff = self.alu_res

        elif sel == Mux_Signal.SEL_T_IMM:
            self.top_buff = self.controlUnit.program[self.controlUnit.pc].arg

        elif sel == Mux_Signal.SEL_T_A:
            self.top_buff = self.reg_A

        elif sel == Mux_Signal.SEL_T_MEM:
            self.top_buff = self.data_memory[self.ar]

        elif sel == Mux_Signal.SEL_T_INPUT:
            port = self.controlUnit.program[self.controlUnit.pc].arg

            assert port in self.io_ports, f"wrong io port {port}"
            assert len(self.io_ports[port]) > 0, "io buffer is empty"

            self.top_buff = self.io_ports[port].pop(0)
            self.controlUnit.last_io = f"INPUT[{port}] -> {self.top_buff}"

        value = self.top_buff & MASK32

        self.flag_Z = int(value == 0)
        self.flag_N = int((value & SIGN32) != 0)

    def signal_latch_AR(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_AR_A, Mux_Signal.SEL_AR_CU}, f"internal error, latch_AR incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_AR_A:
            self.ar_buff = self.reg_A

        elif sel == Mux_Signal.SEL_AR_CU:
            self.ar_buff = self.controlUnit.program[self.controlUnit.pc].arg

            assert self.ar_buff is not None, f"wrong selector latch_AR {sel}"

    def signal_latch_A(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_A_T, Mux_Signal.SEL_A_INC}, f"internal error, latch_A incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_A_T:
            self.reg_A_buff = self.top

        elif sel == Mux_Signal.SEL_A_INC:
            self.reg_A_buff = self.reg_A + 1

    def signal_write_st(self) -> None:

        assert self.sp_read_write > -1, "stack is empty"

        self.stack[self.sp_read_write] = self.second

    def signal_select_sp_read_write(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_SP_READ_WRITE_SP, Mux_Signal.SEL_SP_READ_WRITE_NEXT},\
            f"internal error, select_sp_read_write incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_SP_READ_WRITE_SP:
            self.sp_read_write = self.sp
        elif sel == Mux_Signal.SEL_SP_READ_WRITE_NEXT:
            self.sp_read_write = self.sp + 1


    def signal_write_dm(self) -> None:

        assert 0 <= self.ar < self.data_memory_size, f"incorrect ar = {self.ar}"

        self.data_memory[self.ar] = self.top

    def signal_write_io(self) -> None:

        port = int(self.controlUnit.program[self.controlUnit.pc].arg)
        assert port in self.io_ports, f"wrong io port {port}"

        self.io_ports[port].append(self.top)

        self.controlUnit.last_io = f"OUTPUT[{port}] <- {self.top}"

    def alu(self, sel: ALU_Signal) -> None:

        assert sel in ALU_Signal, f"internal error, alu incorrect selector: {sel}"

        a = self.second & MASK32
        b = self.top & MASK32

        if sel == ALU_Signal.ADD:
            res = a + b

            self.flag_C = int(res > MASK32)
            self.alu_res = res & MASK32

            sign_a = (a & SIGN32) != 0
            sign_b = (b & SIGN32) != 0
            sign_r = (self.alu_res & SIGN32) != 0

            self.flag_V = int((sign_a == sign_b) and (sign_a != sign_r))

        elif sel == ALU_Signal.SUB:
            res = a - b

            self.flag_C = int(a < b)
            self.alu_res = res & MASK32

            sign_a = (a & SIGN32) != 0
            sign_b = (b & SIGN32) != 0
            sign_r = (self.alu_res & SIGN32) != 0

            self.flag_V = int((sign_a != sign_b) and (sign_a != sign_r))

        elif sel == ALU_Signal.MUL:
            res = a * b
            self.alu_res = res & MASK32
            self.flag_C = int(res > MASK32)
            self.flag_V = 0

        elif sel == ALU_Signal.DIV:
            assert b != 0, "division by zero"

            self.alu_res = (a // b) & MASK32
            self.flag_C = 0
            self.flag_V = 0

        elif sel == ALU_Signal.AND:
            self.alu_res = (a & b) & MASK32
            self.flag_C = 0
            self.flag_V = 0

        elif sel == ALU_Signal.OR:
            self.alu_res = (a | b) & MASK32
            self.flag_C = 0
            self.flag_V = 0
        elif sel == ALU_Signal.NOT:
            self.alu_res = (~b) & MASK32

        elif sel == ALU_Signal.ADDC:
            carry = self.flag_C
            res = a + b + carry

            self.flag_C = int(res > MASK32)
            self.alu_res = res & MASK32

            sign_a = (a & SIGN32) != 0
            sign_b = (b & SIGN32) != 0
            sign_r = (self.alu_res & SIGN32) != 0

            self.flag_V = int((sign_a == sign_b) and (sign_a != sign_r))

    def __str__(self) -> str:
        return (
            f"stack: {self.stack}, "
            f"sp: {self.sp}, "
            f"top: {self.top}, "
            f"second: {self.second}, "
            f"ar: {self.ar}, "
            f"reg_A: {self.reg_A}"
        )

class ControlSignal:
    latch = None
    sel = None

    def __init__(self, latch: Signal, sel: Mux_Signal | ALU_Signal | None = None):
        self.latch = latch
        self.sel = sel

    def __str__(self) -> str:
        return f"latch: {self.latch}, sel: {self.sel}"


class ControlUnit:


    mpc_next = ControlSignal(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_NEXT)
    fetch = ControlSignal(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_FETCH)

    sp_next = ControlSignal(Signal.LATCH_SP, Mux_Signal.SEL_SP_NEXT)
    sp_prev = ControlSignal(Signal.LATCH_SP, Mux_Signal.SEL_SP_PREV)

    s_from_top = ControlSignal(Signal.LATCH_S, Mux_Signal.SEL_S_TOP)
    s_from_stack = ControlSignal(Signal.LATCH_S, Mux_Signal.SEL_S_STACK)

    t_from_second = ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_SECOND)

    select_sp_read_write_next = ControlSignal(Signal.SELECT_CURR_SP, Mux_Signal.SEL_SP_READ_WRITE_NEXT)
    select_sp_read_write_sp = ControlSignal(Signal.SELECT_CURR_SP, Mux_Signal.SEL_SP_READ_WRITE_SP)

    write_st = ControlSignal(Signal.WRITE_ST)
    write_dm = ControlSignal(Signal.WRITE_DM)

    pc_next = ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_NEXT)

    _microprogram = [

        #(Instructin Fetch)
        #(0)
        [ControlSignal(Signal.LATCH_MPC, Mux_Signal.SEL_MPC_OPCODE)],

        #(push addr)
        #(1)
        [ControlSignal(Signal.LATCH_AR, Mux_Signal.SEL_AR_CU), mpc_next],
        #(2)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_MEM),
            pc_next,
            fetch
        ],

        #(pushi val)
        #(3)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_IMM),
            pc_next,
            fetch
        ],

        #(store addr)
        #(4)
        [ControlSignal(Signal.LATCH_AR, Mux_Signal.SEL_AR_CU), mpc_next],
        #(5)
        [write_dm, t_from_second, s_from_stack, sp_prev, pc_next, fetch],

        #(fetchA)
        #(6)
        [ControlSignal(Signal.LATCH_AR, Mux_Signal.SEL_AR_A), mpc_next],
        #(7)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_MEM),
            pc_next,
            fetch
        ],

        #(incA)
        #(8)
        [ControlSignal(Signal.LATCH_A, Mux_Signal.SEL_A_INC), pc_next, fetch],

        #(storeA)
        #(9)
        [ControlSignal(Signal.LATCH_AR, Mux_Signal.SEL_AR_A), mpc_next],
        #(10)
        [
            write_dm,
            t_from_second,
            s_from_stack,
            sp_prev,
            pc_next,
            fetch
        ],

        #(setA)
        #(11)
        [
            ControlSignal(Signal.LATCH_A, Mux_Signal.SEL_A_T),
            t_from_second,
            s_from_stack,
            sp_prev,
            pc_next,
            fetch
        ],

        #(getA)
        #(12)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_A),
            pc_next,
            fetch
        ],

        #(drop)
        #(13)
        [
            t_from_second,
            s_from_stack,
            sp_prev,
            pc_next,
            fetch
        ],

        #(dup)
        #(14)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            pc_next,
            fetch
        ],

        #(swap)
        #(15)
        [s_from_top, t_from_second, pc_next, fetch],

        #(over)
        #(16)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            t_from_second,
            s_from_top,
            pc_next,
            fetch
        ],

        #(add)
        #(17)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.ADD),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch,
        ],

        # (sub)
        # (18)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.SUB),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch,
        ],

        # (mul)
        # (19)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.MUL),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch,
        ],

        # (div)
        # (20)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.DIV),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch,
        ],

        # (and)
        # (21)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.AND),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch
        ],

        # (or)
        # (22)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.OR),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch
        ],

        # (jump)
        # (23)
        [ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_ADDR), fetch],

        # (jz)
        # (24)
        [
            ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_JZ),
            s_from_stack,
            t_from_second,
            sp_prev,
            fetch
        ],

        # (jn)
        # (25)
        [
            ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_JN),
            s_from_stack,
            t_from_second,
            sp_prev,
            fetch
        ],

        # (call)
        # (26)
        [
            ControlSignal(Signal.LATCH_R, Mux_Signal.SEL_R_NEXT),
            ControlSignal(Signal.WRITE_RET),
            ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_ADDR),
            fetch
        ],

        # (ret)
        # (27)
        [
            ControlSignal(Signal.LATCH_PC, Mux_Signal.SEL_PC_RET),
            ControlSignal(Signal.LATCH_R, Mux_Signal.SEL_R_PREV),
            fetch
        ],

        # (input n)
        # (28)
        [
            select_sp_read_write_next,
            write_st,
            sp_next,
            s_from_top,
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_INPUT),
            pc_next,
            fetch
        ],

        # (output n)
        # (29)
        [
            ControlSignal(Signal.WRITE_IO),
            t_from_second,
            s_from_stack,
            sp_prev,
            pc_next,
            fetch
        ],

        # (addc)
        # (30)
        [
            s_from_stack,
            sp_prev,
            ControlSignal(Signal.ALU, ALU_Signal.ADDC),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch
        ],

        # (not)
        # (31)
        [
            ControlSignal(Signal.ALU, ALU_Signal.NOT),
            ControlSignal(Signal.LATCH_T, Mux_Signal.SEL_T_ALU),
            pc_next,
            fetch
        ],

    ]

    mpc_of_opcode = {
        Opcode.PUSH: 1,
        Opcode.PUSHI: 3,
        Opcode.STORE: 4,
        Opcode.FETCH_A: 6,
        Opcode.INCA: 8,
        Opcode.STORE_A: 9,
        Opcode.SET_A: 11,
        Opcode.GET_A: 12,
        Opcode.DROP: 13,
        Opcode.DUP: 14,
        Opcode.SWAP: 15,
        Opcode.OVER: 16,
        Opcode.ADD: 17,
        Opcode.SUB: 18,
        Opcode.MUL: 19,
        Opcode.DIV: 20,
        Opcode.AND: 21,
        Opcode.OR: 22,
        Opcode.JUMP: 23,
        Opcode.JZ: 24,
        Opcode.JN: 25,
        Opcode.CALL: 26,
        Opcode.RET: 27,
        Opcode.INPUT: 28,
        Opcode.OUTPUT: 29,
        Opcode.ADDC: 30,
        Opcode.NOT: 31,
    }

    program: list[Instruction]
    pc: int
    dataPath: DataPath

    mpc: int
    reg_R: int
    return_stack: list[int]

    _tick: int

    last_io: str | None = None

    def __init__(self, dataPath: DataPath, program: list[Instruction], start: int) -> None:
        self.dataPath = dataPath
        self.program = program
        self.pc = start
        self._tick = 0
        self.reg_R = -1
        self.return_stack = [0] * 10
        self.mpc = 0

    def tick(self) -> None:
        self._tick += 1

    def signal_latch_R(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_R_NEXT, Mux_Signal.SEL_R_PREV}, (
            f"internal error, latch_R incorrect selector: {sel}"
        )

        if sel == Mux_Signal.SEL_R_NEXT:
            self.reg_R += 1
        elif sel == Mux_Signal.SEL_R_PREV:
            self.return_stack[self.reg_R] = 0
            self.reg_R -= 1

        assert -1 <= self.reg_R < len(self.return_stack), f"index out of range returnStack: {self.reg_R}"

    def signal_latch_mPC(self, sel: Mux_Signal) -> None:

        assert sel in {Mux_Signal.SEL_MPC_NEXT, Mux_Signal.SEL_MPC_OPCODE, Mux_Signal.SEL_MPC_FETCH}, (
            f"internal error, latch_mPC incorrect selector: {sel}"
        )

        if sel == Mux_Signal.SEL_MPC_NEXT:
            self.mpc += 1
        elif sel == Mux_Signal.SEL_MPC_FETCH:
            self.mpc = 0
        elif sel == Mux_Signal.SEL_MPC_OPCODE:

            instr = self.program[self.pc].opcode
            if instr == Opcode.HALT:
                return
            assert instr in self.mpc_of_opcode, (
                f"wrong instruction {instr}"
            )

            self.mpc = self.mpc_of_opcode[instr]

    def signal_latch_PC(self, sel: Mux_Signal) -> None:

        assert sel in {
            Mux_Signal.SEL_PC_NEXT,
            Mux_Signal.SEL_PC_RET,
            Mux_Signal.SEL_PC_ADDR,
            Mux_Signal.SEL_PC_JN,
            Mux_Signal.SEL_PC_JZ,
        }, f"internal error, latch_PC incorrect selector: {sel}"

        if sel == Mux_Signal.SEL_PC_NEXT:
            self.pc += 1

        elif sel == Mux_Signal.SEL_PC_ADDR:
            self.pc = self.program[self.pc].arg

        elif sel == Mux_Signal.SEL_PC_JN:
            self.pc = self.program[self.pc].arg if self.dataPath.flag_N else self.pc + 1

        elif sel == Mux_Signal.SEL_PC_JZ:
            self.pc = self.program[self.pc].arg if self.dataPath.flag_Z else self.pc + 1

        elif sel == Mux_Signal.SEL_PC_RET:
            assert self.reg_R >= 0, "return stack is empty"
            self.pc = self.return_stack[self.reg_R]

    def signal_write_ret(self) -> None:

        assert self.reg_R > -1, "return stack is empty"

        self.return_stack[self.reg_R] = self.pc + 1

    def dispatch(self, microinstr: ControlSignal) -> None:
        assert microinstr.latch in Signal, (
            f"wrong latch: {microinstr.latch}"
        )

        sel = microinstr.sel
        latch = microinstr.latch

        if latch == Signal.LATCH_PC:
            assert isinstance(sel, Mux_Signal)
            self.signal_latch_PC(sel)

        elif latch == Signal.LATCH_R:
            assert isinstance(sel, Mux_Signal)
            self.signal_latch_R(sel)

        elif latch == Signal.LATCH_MPC:
            assert isinstance(sel, Mux_Signal)
            self.signal_latch_mPC(sel)

        elif latch == Signal.WRITE_RET:
            self.signal_write_ret()

        elif latch == Signal.LATCH_AR:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_latch_AR(sel)

        elif latch == Signal.LATCH_SP:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_latch_SP(sel)

        elif latch == Signal.LATCH_S:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_latch_S(sel)

        elif latch == Signal.LATCH_T:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_latch_T(sel)

        elif latch == Signal.WRITE_ST:
            self.dataPath.signal_write_st()

        elif latch == Signal.SELECT_CURR_SP:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_select_sp_read_write(sel)

        elif latch == Signal.LATCH_A:
            assert isinstance(sel, Mux_Signal)
            self.dataPath.signal_latch_A(sel)

        elif latch == Signal.WRITE_DM:
            self.dataPath.signal_write_dm()

        elif latch == Signal.ALU:
            assert isinstance(sel, ALU_Signal)
            self.dataPath.alu(sel)

        elif latch == Signal.WRITE_IO:
            self.dataPath.signal_write_io()

        else:
            raise AssertionError(f"unknown latch: {microinstr.latch}")

    def __repr__(self) -> str:
        instr = self.program[self.pc]
        instr_str = f"{instr.opcode.name} {instr.arg}" if instr else "None"

        return (
            f"PC: {self.pc:4} | "
            f"MPC: {self.mpc:3} | "
            f"Insr: {instr_str:12} | "
            f"R: {self.reg_R:3} | "
            f"SP: {self.dataPath.sp:3} | "
            f"T: {self.dataPath.top:5} | "
            f"S: {self.dataPath.second:5} | "
            f"A: {self.dataPath.reg_A:5} | "
            f"AR: {self.dataPath.ar:5} | "
            f"N:{self.dataPath.flag_N} "
            f"Z:{self.dataPath.flag_Z} "
            f"V:{self.dataPath.flag_V} "
            f"C:{self.dataPath.flag_C}\n"
            f"STACK:   {self.dataPath.stack}   |   "
            f"RETURN_STACK:   {self.return_stack}\n"
            f"IO: {self.dataPath.io_ports}"
        )


def simulation(
    instructions: list[Instruction],
    data_memory: list[int],
    io_ports: dict[int, list[int]],
    limit: int = 1000000000,
    debug: bool = True,
) -> None:

    data_path = DataPath(10, data_memory, io_ports)
    controlUnit = ControlUnit(data_path, instructions, 0)
    data_path.controlUnit = controlUnit

    micro_code_logs: list[str] = []

    with open("machine.log", "w") as log_file:
        while controlUnit._tick < limit:
            controlUnit.tick()

            curr_mpc = controlUnit.mpc
            curr_tick = controlUnit._microprogram[curr_mpc]
            instr = controlUnit.program[controlUnit.pc]
            curr_instr = instr.opcode.name
            controlUnit.dataPath.start_cycle()

            micro_code_logs.append(
                f"\n==== TICK {controlUnit._tick:4} | MPC {curr_mpc:4} | {curr_instr} "
            )

            for m in curr_tick:
                micro_code_logs.append(f"   {m}")
                controlUnit.dispatch(m)

            if debug:
                log_file.write(f"\n=== TICK {controlUnit._tick} ===\n")
                log_file.write(repr(controlUnit) + "\n")
                if controlUnit.last_io:
                    log_file.write(controlUnit.last_io + "\n")
                controlUnit.last_io = None
                log_file.write("-" * 60)

            controlUnit.dataPath.update()

            if instr.opcode == Opcode.HALT:
                log_file.write("\nHALT\n")
                break

        else:
            log_file.write("\nLIMIT REACHED\n")

        log_file.write(f"\nTOTAL TICK : {controlUnit._tick}\n")
        log_file.write(f"\nFINAL io-ports {controlUnit.dataPath.io_ports}\n")

        if debug:
            log_file.write("\n\n===== MICROCODE TRACE =====\n")

            for line in micro_code_logs:
                log_file.write(line + "\n")


def main(code_file: str, data_file: str, input_file: str, debug: bool=True) -> None:

    with open(code_file, "rb") as f:
        binary_instruction = bytearray(f.read())

    with open(data_file, "rb") as f:
        binary_memory = bytearray(f.read())

    io_ports = parse_input(input_file)

    instructions = from_bytes_instruction(binary_instruction)
    data = from_bytes_data(binary_memory)
    simulation(instructions, data, io_ports, debug=debug)


if __name__ == "__main__":
    assert len(sys.argv) == 4, "Wrong arguments: machine.py <code_file> data_file> <input_file>"
    _, code_file, data_file, input_file = sys.argv
    main(code_file, data_file, input_file)
