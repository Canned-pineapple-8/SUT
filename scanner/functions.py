import os
from scanner.data import *
from sut.symbol_table import SymbolTableEntry, SymbolTable
from sut.enums import *
from sut.base_type import Type, TypeCode

def binary_search(sorted_list, target):
    """Выполняет бинарный поиск target в отсортированном списке с учетом ASCII-кодов.
    Возвращает индекс элемента или -1, если элемент не найден."""
    left = 0
    right = len(sorted_list) - 1
    target_ascii = [ord(c) for c in target]  # Преобразуем target в ASCII коды один раз

    while left <= right:
        mid = (left + right) // 2
        current_ascii = [ord(c) for c in sorted_list[mid]]  # ASCII коды текущего элемента

        if current_ascii == target_ascii:
            return mid
        elif (lambda x, y: x < y)(current_ascii, target_ascii):  # Лямбда для сравнения
            left = mid + 1
        else:
            right = mid - 1

    return -1


def read_file_chars(file_path):
    """
    Проверяет наличие файла и возвращает список символов из файла.

    Args:
        file_path (str): Путь к файлу

    Returns:
        list: Список символов из файла, если файл существует
        None: Если файл не существует
    """
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            chars = list(file.read())
        return chars
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None


# определение типа символа и возврат номера строки в таблице состояний
def get_symbol_type(char: str) -> int:
    if char in SYMBOL_MAP:
        return SYMBOL_MAP[char]
    if char.isalpha():
        return 17 if char != 'e' else 23  # l или e
    if char == ":":
        return 18
    if char.isdigit() or char == "_":
        return 19  # d
    if char == ' ':
        return 20  # sp
    if char == '\t':
        return 21  # tab
    if char == '\n':
        return 22  # \n
    return 24  # Неизвестный символ


def form_token(state, word, attrCodes, keywords, keyword_tokens, symbol_table):
    match state:
        case -1:
            return (";", 0)
        case -2:
            return ("}", 0)
        case -3:
            return ("{", 0)
        case -4:
            return (")", 0)
        case -5:
            return ("(", 0)
        case -6:
            return ("rel", OpCode.opEq)
        case -7:
            return ("ass", 0)
        case -8:
            return (",", 0)
        case -9:
            return (".", 0)
        case -10:
            return ("add", OpCode.opAdd)
        case -11:
            return ("add", OpCode.opSub)
        case -12:
            return ("add", OpCode.opOr)
        case -13:
            return ("mult", OpCode.opMult)
        case -14:
            return ("mult", OpCode.opDiv)
        case -15:
            return None
        case -16:
            return ("mult", OpCode.opAnd)
        case -17:
            return ("!", 0)
        case -18:
            return ("rel", OpCode.opNotEq)
        case -19:
            return ("rel", OpCode.opGreat)
        case -20:
            return ("rel", OpCode.opGreatEq)
        case -21:
            return ("rel", OpCode.opLess)
        case -22:
            return ("rel", OpCode.opLessEq)
        case -23:
            pointer = symbol_table.add_lexem(word)
            if word in keywords:
                if word in base_types:
                    return "id", symbol_table.find_lexem(word)
                if word in bool_constants:
                    return "bool", symbol_table.find_lexem(word)
                return keyword_tokens[word], pointer
            else:
                return ("id", pointer)
        case -24:
            '''if word not in num_table:
                ind = len(num_table)
                num_table[word] = ("real", ind)
                return ("num", word)
            '''
            pointer = symbol_table.add_lexem(word)
            symbol_table.add_type(pointer, category=Category.catConst, new_type=symbol_table.get_base_type(TypeCode.typeFloat))
            return ("num", pointer)
        case -25:
            '''if word not in num_table:
                ind = len(num_table)
                num_table[word] = ("int", ind)
                return ("num", word)
            '''
            pointer = symbol_table.add_lexem(word)
            symbol_table.add_type(pointer, category=Category.catConst, new_type=symbol_table.get_base_type(TypeCode.typeInt))
            return ("num", pointer)
        case -26:
            return None
        case -27:
            return None
        case -28:
            return (":", 0)
        case -29:
            return ("err1", 0)
        case -30:
            return ("err2", 0)
        case -31:
            return ("err3", 0)
    return None


def process_input(buffer, attrCodes, keywords, keyword_tokens, symbol_table:SymbolTable):
    """Обрабатывает входной буфер и возвращает список токенов."""
    current_state = 0
    output = []
    i = 0
    begin = i
    while i < len(buffer):
        # Определяем тип символа
        char = buffer[i]
        symbol_row = get_symbol_type(char)

        # Получаем новое состояние из таблицы
        new_state = conditions_table[symbol_row][current_state]

        if new_state < 0:  # Конечное состояние
            current_state = 0  # Сброс состояния
            i -= return_steps[new_state]
            output.append(form_token(new_state, ''.join(buffer[begin:i+1]), attrCodes, keywords, keyword_tokens, symbol_table))
            begin = i + 1
        else:
            current_state = new_state  # Переход в новое состояние
        i += 1

    return output

# на каждый идентификатор: само слово, номер лексемы (атрибут <id, <номер>>)
# на каждое число: число, номер числа в таблице (атрибут <num, <номер>>), тип числа

        # e(1) = -27
        # e(2) = -28
        # e(3) = -29
        # end = -30

def print_tokens(token_list, word_table, num_table, filename=None):
    output_lines = []  # Собираем все строки вывода

    for token in [t for t in token_list if t]:
        match token[0]:
            case "err":
                line = errors[int(token[0][-1])]
                output_lines.append(line)
                if filename is not None:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(line + '\n')
                print(line)
                return  # Выходим после ошибки
            case "id":
                line = f'<{token[0]}, {word_table[token[1]]}>, лексема: {token[1]}'
            case "num":
                line = f'<{token[0]}, {num_table[token[1]][1]}>, лексема: {token[1]}, тип: {num_table[token[1]][0]}'
            case _:
                line = f'<{token[0]}, {token[1]}>'

        output_lines.append(line)
        print(line)

    # Если указан файл, записываем все строки (кроме случая с ошибкой)
    if filename is not None and output_lines:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines) + '\n')

'''def main():
    attr_codes = process_atributes_codes(attr_names)
    lex_table = dict()
    num_table = dict()

    file_path = "test_full.txt"
    input_buffer = read_file_chars(file_path)
    try:
        tokens = process_input(input_buffer, attr_codes, keyword_table, keyword_tokens, lex_table, num_table)
        print("Найденные токены:")
        print_tokens(tokens,lex_table, num_table, "output.txt")
    except ValueError as e:
        print("Ошибка:", e)

main()'''