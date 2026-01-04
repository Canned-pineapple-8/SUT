from typing import List, Dict, Optional
from sut.enums import OpCode


class Instruction:
    def __init__(self, op, arg1=-1, arg2=-1, result=-1):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __repr__(self):
        return f"({self.op}, {str(self.arg1)}, {str(self.arg2)}, {self.result})"


class IntructionTable:
    def __init__(self):
        self.instructions:List[Instruction] = []
        self.orders:Dict[Instruction, int]  = {}

        self.label_name = 0

    def __str__(self):
        text = ''
        for entry in self.instructions:
            text += str(entry) + '\n'
        return text

    def generate_instruction(self, op:OpCode, arg1=-1, arg2=-1, result=-1) -> Instruction:
        if op == OpCode.label:
            instruction = Instruction(OpCode.label, arg1, arg2, f'L{self.label_name}')
            self.label_name += 1
        else:
            instruction = Instruction(op, arg1, arg2, result)
        self.orders[instruction] = len(self.instructions)
        self.instructions.append(instruction)
        return instruction

    def make_list(self, operation: Instruction):
        commands_index = [self.orders[operation]]
        return commands_index

    def backpatch(self, falselist: List[int], label:str):
        for index in falselist:
            self.instructions[index].result = label

    def calc_address(self, record, ident):
        field_offset = 0
        for field in record.type.fields:
            if field.lexem == ident.lexem:
                field_offset = field.offset
        return (ident, record.address + field_offset)


