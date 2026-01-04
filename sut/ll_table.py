import xml.etree.ElementTree as ET
from typing import Set, List


class LLTableRow:
    def __init__(self, terminals: Set[str], jump: int, accept: bool, stack: bool, action: int, error: bool):
        self.terminals = terminals   # множество терминалов
        self.jump = jump             # номер строки для перехода
        self.accept = accept         # поле приема
        self.stack = stack           # стековое поле
        self.action = action         # код семантического действия
        self.error = error           # поле ошибки

    def __repr__(self):
        return (f"LLTableRow(terminals={self.terminals}, jump={self.jump}, "
                f"accept={self.accept}, stack={self.stack}, action={self.action}, error={self.error})")


class LLTable:
    def __init__(self):
        self.rows: List[LLTableRow] = []

    def load_from_xml(self, filename: str):
        """
        Загружает LL(1)-таблицу из XML.
        """
        tree = ET.parse(filename)
        root = tree.getroot()

        self.rows.clear()
        for elem in root.findall("Row"):
            # собираем терминалы из атрибутов Lexeme
            terminals_elem = elem.find("Terminals")
            terminals = set()
            if terminals_elem is not None:
                for terminal in terminals_elem.findall("Terminal"):
                    lexeme = terminal.get("Lexeme")
                    if lexeme:
                        terminals.add(lexeme)

            jump = int(elem.get("Jump", 0))
            accept = elem.get("Accept", "False").lower() == "true"
            stack = elem.get("Stack", "False").lower() == "true"

            action_str = elem.get("Action", "")
            action = int(action_str[1:]) if action_str.startswith("A") and action_str[1:].isdigit() else 0

            error = elem.get("Error", "False").lower() == "true"

            row = LLTableRow(terminals, jump, accept, stack, action, error)
            self.rows.append(row)

    def get_row(self, index: int) -> LLTableRow:
        """
        Получение строки по индексу (индексация с 1 для соответствия форме таблицы).
        """
        if 1 <= index <= len(self.rows):
            return self.rows[index - 1]
        else:
            raise IndexError(f"Обращение за пределы таблицы разбора: {index}")

    def __len__(self):
        return len(self.rows)
