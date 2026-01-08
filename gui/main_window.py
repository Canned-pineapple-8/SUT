from PyQt5.QtWidgets import (
    QWidget, QPlainTextEdit, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt

from scanner.functions import *
from scanner.data import *

from sut.translator import LL1Parser, LLTable
from sut.semantic_engine import SemanticEngine
from sut.symbol_table import SymbolTable
from sut.instructions import IntructionTable


MONO_FONT = "Consolas"
FONT_SIZE = 16


class OutputPanel(QWidget):
    def __init__(self, title: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel(title)
        label.setAlignment(Qt.AlignLeft)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)

        layout.addWidget(label)
        layout.addWidget(self.text)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_text(self, text: str):
        self.text.setPlainText(text)

    def clear(self):
        self.text.clear()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LL(1) Syntax-Directed Translator")
        self.resize(1600, 900)
        self._init_ui()

    def _init_ui(self):
        root_layout = QHBoxLayout(self)

        # ================= LEFT =================
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        # --- кнопки ---
        btn_load = QPushButton("Загрузить файл")
        btn_run = QPushButton("Анализировать")

        for btn in (btn_load, btn_run):
            btn.setMinimumHeight(42)
            btn.setStyleSheet(
                f"""
                font-size:{FONT_SIZE}px;
                font-weight:600;
                padding:6px 14px;
                """
            )

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(btn_load)
        buttons_layout.addWidget(btn_run)

        btn_load.clicked.connect(self.load_file)
        btn_run.clicked.connect(self.analyze)

        left_layout.addWidget(QLabel("Исходный код"))
        left_layout.addLayout(buttons_layout)

        # --- сплиттер для редактора и панели ошибок ---
        editor_error_splitter = QSplitter(Qt.Vertical)

        # Редактор
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Введите программу...")
        self.editor.setStyleSheet(f"font-family:{MONO_FONT}; font-size:{FONT_SIZE}px;")
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Панель ошибок с заголовком
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setContentsMargins(0, 0, 0, 0)

        error_label = QLabel("Ошибки")
        error_label.setAlignment(Qt.AlignLeft)
        self.error_bar = QPlainTextEdit()
        self.error_bar.setReadOnly(True)
        self.error_bar.setStyleSheet(f"font-family:{MONO_FONT}; font-size:{FONT_SIZE}px; color:#f85149;")
        self.error_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        error_layout.addWidget(error_label)
        error_layout.addWidget(self.error_bar)

        # Добавляем виджеты в вертикальный сплиттер
        editor_error_splitter.addWidget(self.editor)
        editor_error_splitter.addWidget(error_widget)
        editor_error_splitter.setSizes([700, 300])  # редактор больше, ошибки меньше

        left_layout.addWidget(editor_error_splitter)

        left_container = QWidget()
        left_container.setLayout(left_layout)

        # ================= RIGHT =================
        # --- токены и колонка символов+инструкций в горизонтальном сплиттере ---
        right_splitter = QSplitter(Qt.Horizontal)

        self.tokens = OutputPanel("Токены")
        self.tokens.setMinimumWidth(200)

        right_stack = QWidget()
        right_stack_layout = QVBoxLayout(right_stack)
        right_stack_layout.setContentsMargins(0, 0, 0, 0)

        self.symbols = OutputPanel("Таблица символов")
        self.instructions = OutputPanel("Инструкции")

        right_stack_layout.addWidget(self.symbols)
        right_stack_layout.addWidget(self.instructions)

        right_splitter.addWidget(self.tokens)
        right_splitter.addWidget(right_stack)
        right_splitter.setSizes([400, 800])  # начальные размеры колонок

        # ================= ROOT =================
        root_splitter = QSplitter(Qt.Horizontal)
        root_splitter.addWidget(left_container)
        root_splitter.addWidget(right_splitter)
        root_splitter.setSizes([600, 1000])  # начальные размеры левой и правой частей

        root_layout.addWidget(root_splitter)

        # Задаем шрифты для OutputPanel
        for panel in (self.tokens, self.symbols, self.instructions):
            panel.text.setStyleSheet(f"font-family:{MONO_FONT}; font-size:{FONT_SIZE}px;")

    # ================= logic =================

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Text files (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())

    def analyze(self):
        self.tokens.clear()
        self.symbols.clear()
        self.instructions.clear()
        self.error_bar.clear()

        try:
            source = self.editor.toPlainText()

            symbol_table = SymbolTable()
            symbol_table.add_types()
            symbol_table.add_constants()

            instruction_table = IntructionTable()

            table = LLTable()
            table.load_from_xml("LL_Table.xml")

            attr_codes = process_atributes_codes(attr_names)
            tokens = [
                t for t in process_input(
                    list(source),
                    attr_codes,
                    keyword_table,
                    keyword_tokens,
                    symbol_table
                ) if t
            ]

            if len(tokens) == 0:
                self.error_bar.setPlainText("Введите текст программы.")
                return

            self.tokens.set_text(
                "\n".join(f"{i + 1:>4}. <{tokens[i][0]}, {tokens[i][1]}>" for i in range(len(tokens)))
            )

            engine = SemanticEngine(symbol_table, instruction_table)
            parser = LL1Parser(table, engine, tokens, symbol_table)
            parser.parse()

            self.symbols.set_text(symbol_table.form_variables_info())
            self.instructions.set_text(instruction_table.form_instructions_info())

        except Exception as e:
            self.error_bar.setPlainText(str(e))
