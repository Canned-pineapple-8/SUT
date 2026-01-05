from scanner.functions import *
from scanner.data import *

from sut.translator import LL1Parser, LLTable
from sut.semantic_engine import SemanticEngine
from sut.symbol_table import SymbolTable
from sut.instructions import IntructionTable
from sut.base_type import Type
from sut.enums import *

def main():
    _temp_id = 0

    # инициализация таблицы символов
    symbol_table = SymbolTable()
    symbol_table.add_types()
    symbol_table.add_constants()

    # инициализация таблицы команд
    instruction_table = IntructionTable()

    # чтение таблицы разбора
    table = LLTable()
    table.load_from_xml("LL_Table.xml")
    print(table.rows)

    # сканер
    attr_codes = process_atributes_codes(attr_names)

    with open("test_small.txt", "r", encoding="utf-8") as f:
        source_code = f.read()

    try:
        input_buffer = list(source_code)
        tokens = [token for token in process_input(
            input_buffer,
            attr_codes,
            keyword_table,
            keyword_tokens,
            symbol_table
        ) if token is not None]
    except Exception as e:
        print(f"Ошибка в работе сканера: {e}")
        return

    # отладочный вывод токенов
    #print([f'{token[0]}, {str(token[1])}' for token in tokens])

    # инициализация семантического движка
    engine = SemanticEngine(symbol_table=symbol_table, instruction_table=instruction_table)

    # инициализация транслятора
    parser = LL1Parser(table, engine, tokens, symbol_table)
    parser.parse()

    # формирование вывода информации
    var_text = symbol_table.form_variables_info()
    print(var_text)

    instruction_text = instruction_table.form_instructions_info()
    print(instruction_text)


if __name__ == "__main__":
    main()