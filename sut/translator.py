from sut.ll_table import LLTable
from sut.semantic_engine import SemanticEngine


class LL1Parser:
    """
    Транслятор
    """
    def __init__(self, ll_table:LLTable, semantic_engine:SemanticEngine, tokens, symbol_table):
        self.ll_table:LLTable = ll_table  # таблица разбора
        self.sem_engine = semantic_engine  # семантический движок
        self.tokens = tokens  # токены от сканера
        self.parser_stack = []  # стек парсера
        self.symbol_table = symbol_table  # таблица символов

    def push(self, val):
        """
        Поместить элемент в стек
        """
        self.parser_stack.append(val)

    def pop(self):
        """
        Извлечь элемент из стека
        """
        return self.parser_stack.pop() if self.parser_stack else 0

    def parse(self):
        self.parser_stack.clear()
        self.sem_engine.attr_stack.clear()
        self.push(0)       # начальное состояние
        i = 1              # первая строка таблицы
        la = True
        token = self.tokens[0]
        prev_token = token
        token_index = 0

        # общий алгоритм перемещения по таблице
        while token_index < len(self.tokens) or i != 0:
            elem = self.ll_table.get_row(i)
            if elem.action != 0 or token[0] in elem.terminals:
                if elem.action != 0:
                    # выполняем семантическое действие
                    getattr(self.sem_engine, f"A{elem.action}")(prev_token[1])
                la = elem.accept
                if elem.jump != 0:
                    if elem.stack:
                        self.push(i+1)
                    i = elem.jump
                else:
                    i = self.pop()
            else:
                if not elem.error:
                    i += 1
                    la = False
                else:
                    if token and token[0] and token[0] in ["id", "num"]:
                        msg_lex = token[1].lexem
                    else:
                        msg_lex = token[0]
                    raise Exception(f"Символ не соответствует грамматике: {msg_lex}")
            if la:
                token_index += 1
                prev_token = token
                if token_index < len(self.tokens):
                    token = self.tokens[token_index]
                else:
                    return
