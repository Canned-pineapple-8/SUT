from typing import List, Dict, Optional
from sut.enums import OpCode


class Instruction:
    """
    Команда
    """
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op  # код операции
        self.arg1 = arg1  # аргумент 1
        self.arg2 = arg2  # аргумент 2
        self.result = result  # результат

    def __repr__(self):
        return f"({self.op}, {str(self.arg1)}, {str(self.arg2)}, {self.result})"


class IntructionTable:
    def __init__(self):
        self.instructions:List[Instruction] = []  # список команд
        self.orders:Dict[Instruction, int]  = {}  # порядковый номер команды (на всякий случай)

        self.label_name = 0  # следующий уникальный номер метки

    def __str__(self):
        text = ''
        for entry in self.instructions:
            text += str(entry) + '\n'
        return text

    def generate_instruction(self, op:OpCode, arg1=None, arg2=None, result=None) -> Instruction:
        """
        Генерация команды
        """
        if op == OpCode.label:
            instruction = Instruction(OpCode.label, arg1, arg2, f'L{self.label_name}')  # генерация метки
            self.label_name += 1
        else:
            instruction = Instruction(op, arg1, arg2, result)  # обычная команда
        self.orders[instruction] = len(self.instructions)
        self.instructions.append(instruction)
        return instruction

    def make_list(self, operation: Instruction):
        """
        Список переходов для условных команд (backpatching)
        """
        commands_index = [self.orders[operation]]
        return commands_index

    def backpatch(self, falselist: List[int], label:str):
        """
        Корректировка меток в переходах (backpatching)
        """
        for index in falselist:
            self.instructions[index].result = label

    def form_instructions_info(self):
        """
        Генерация текстового представления команд (для отображения на экране)
        """
        from scanner.data import operation_codes
        text = ""

        for entry in self.instructions:
            if entry.op == OpCode.opAss:
                text += f"{entry.result.lexem} := {entry.arg1.lexem}\n"
            elif entry.op == OpCode.label:
                text += f"Label: {entry.result}\n"
            elif entry.op in [OpCode.opGoto, OpCode.opGotoFalse]:
                text += f"{entry.op}: {entry.result}\n"
            elif entry.op == OpCode.opNot:
                text += f"!{entry.result.lexem}\n"
            else:
                text += f"{entry.result.lexem} := {entry.arg1.lexem} {operation_codes[entry.op]} {entry.arg2.lexem}\n"

        return text



