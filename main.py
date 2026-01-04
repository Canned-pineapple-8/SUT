import tkinter as tk
from tkinter import ttk, scrolledtext
from scanner.functions import *
from scanner.data import *

'''
class LexerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лексический анализатор")
        self.geometry("1000x600")

        # Инициализация таблиц
        self.attr_codes = process_atributes_codes(attr_names)
        self.lex_table = dict()
        self.num_table = dict()

        self.create_widgets()
        self.setup_clipboard()

    def create_widgets(self):
        # Панель разделения окна
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Левая панель для ввода
        self.input_frame = ttk.Frame(paned_window, width=500)
        self.input_text = scrolledtext.ScrolledText(self.input_frame, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        paned_window.add(self.input_frame)

        # Правая панель для вывода
        self.output_frame = ttk.Frame(paned_window, width=500)
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        paned_window.add(self.output_frame)

        # Кнопка анализа
        self.analyze_btn = ttk.Button(self, text="Анализировать", command=self.analyze)
        self.analyze_btn.pack(pady=10)

        # Контекстное меню
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        self.context_menu.add_command(label="Копировать", command=self.copy_to_clipboard)
        self.context_menu.add_command(label="Вырезать", command=self.cut_to_clipboard)

        # Привязка правой кнопки мыши
        self.input_text.bind("<Button-3>", self.show_context_menu)
        self.output_text.bind("<Button-3>", self.show_context_menu)

    def setup_clipboard(self):
        # Привязка горячих клавиш
        self.input_text.bind("<Control_L>", self.paste_from_clipboard)
        self.input_text.bind("<Control_R>", self.copy_to_clipboard)

    def show_context_menu(self, event):
        widget = event.widget
        self.context_menu.entryconfigure("Вставить", state='normal' if self.clipboard_exists() else 'disabled')
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def clipboard_exists(self):
        try:
            return bool(self.clipboard_get())
        except tk.TclError:
            return False

    def paste_from_clipboard(self, event=None):
        try:
            text = self.clipboard_get()
            widget = self.focus_get()
            if isinstance(widget, tk.Text):
                widget.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"  # Предотвращаем стандартную обработку

    def copy_to_clipboard(self, event=None):
        widget = self.focus_get()
        if isinstance(widget, tk.Text):
            try:
                text = widget.get("sel.first", "sel.last")
                self.clipboard_clear()
                self.clipboard_append(text)
            except tk.TclError:
                pass
        return "break"

    def cut_to_clipboard(self, event=None):
        self.copy_to_clipboard()
        widget = self.focus_get()
        if isinstance(widget, tk.Text):
            widget.delete("sel.first", "sel.last")
        return "break"

    def analyze(self):
        # Очистка предыдущих результатов
        self.output_text.delete(1.0, tk.END)
        self.lex_table.clear()
        self.num_table.clear()

        # Получение текста из поля ввода
        source_code = self.input_text.get(1.0, tk.END)

        try:
            # Обработка входных данных
            input_buffer = list(source_code)
            tokens = process_input(
                input_buffer,
                self.attr_codes,
                keyword_table,
                keyword_tokens,
                self.lex_table,
                self.num_table
            )

            # Формирование результата
            output_lines = []
            for token in [t for t in tokens if t]:
                # Адаптация вашей логики print_tokens для GUI
                if token[0].startswith("err"):
                    output_lines.append(errors[int(token[0][-1])])
                    break
                elif token[0] == "id":
                    line = f'<{token[0]}, {self.lex_table[token[1]]}>, лексема: {token[1]}'
                elif token[0] == "num":
                    line = f'<{token[0]}, {self.num_table[token[1]][1]}>, лексема: {token[1]}, тип: {self.num_table[token[1]][0]}'
                else:
                    line = f'<{token[0]}, {token[1]}>'
                output_lines.append(line)

            # Вывод результата
            self.output_text.insert(tk.END, "\n".join(output_lines))

        except Exception as e:
            self.output_text.insert(tk.END, f"Ошибка: {str(e)}")

app = LexerApp()
app.mainloop()
'''

from sut.translator import LL1Parser, LLTable
from sut.semantic_engine import SemanticEngine
from sut.symbol_table import SymbolTable
from sut.instructions import IntructionTable, Instruction
from sut.base_type import Type,TypeCode
from sut.enums import *

operation_codes = {
    OpCode.opAdd: "+",
    OpCode.opSub: "-",
    OpCode.opOr: "||",
    OpCode.opMult: "*",
    OpCode.opDiv: "/",
    OpCode.opAnd: "&&",
    OpCode.opEq: "==",
    OpCode.opNotEq: "!=",
    OpCode.opGreat: ">",
    OpCode.opGreatEq: ">=",
    OpCode.opLess: "<",
    OpCode.opLessEq: "<=",
}



def add_types(symbol_table:SymbolTable):
    base_types = [TypeCode.typeInt, TypeCode.typeFloat, TypeCode.typeBool, TypeCode.typeVoid]
    type_words = ["Int", "Float", "Boolean", "Void"]
    for i in range(len(base_types)):
        pnt = symbol_table.add_lexem(type_words[i])
        pnt.category = Category.catTypeName
        pnt.type = Type(base_types[i])
        symbol_table.base_types[base_types[i]] = pnt


def add_constants(symbol_table:SymbolTable):
    constants = ["true", "false"]
    for i in range(len(constants)):
        pnt = symbol_table.add_lexem(constants[i])
        symbol_table.add_type(pnt, category=Category.catConst, new_type=symbol_table.get_base_type(TypeCode.typeBool))


def main():
    DataMem = bytearray()
    InstrMem = []

    NextAddr = 0
    NextInstr = 0

    _temp_id = 0
    symbol_table = SymbolTable()
    instruction_table = IntructionTable()
    # чтение таблицы разбора
    table = LLTable()
    table.load_from_xml("LL_Table.xml")
    print(table.rows)

    # сканер

    add_types(symbol_table)
    add_constants(symbol_table)

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
        exit()

    print([f'{token[0]}, {str(token[1])}' for token in tokens])

    # транслятор
    engine = SemanticEngine(symbol_table=symbol_table, instruction_table=instruction_table)
    parser = LL1Parser(table, engine, tokens, symbol_table)

    parser.parse()

    var_text = form_variables_info(symbol_table)
    print(var_text)

    instruction_text = form_instructions_info(instruction_table)
    print(instruction_text)


def form_variables_info(symbol_table:SymbolTable):
    text = ""
    variables = []
    for entry in symbol_table.entries:
        if entry.address != -1:
            variables.append(entry)
    variables.sort(key=lambda e: e.address)

    for entry in variables:
        if entry.type.type_ptr is not None:
            record_name = entry.type.type_ptr.lexem
        else:
            record_name = ""
        text += f'{entry.address}: {entry.lexem}\n' \
                f'\ttype = {entry.type.type_code} {record_name}\n' \
                f'\tsize = {entry.type.width}\n'
    return text


def form_instructions_info(instructions_table:IntructionTable):
    text = ""

    for entry in instructions_table.instructions:
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


if __name__ == "__main__":
    main()