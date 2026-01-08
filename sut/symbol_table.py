from sut.enums import Category, OpCode
from sut.base_type import Type, TypeCode
from sut.error import Type_Error
from typing import Dict, List, Optional


class SymbolTableEntry:
    """
    Запись в таблице символов
    """
    def __init__(self, lex):
        self.lexem = lex  # лексема
        self.category = Category.catNoCat  # категория
        self.type = None  # тип
        self.fields = None  # поля (для структур)
        self.address = -1  # адрес (для переменных/полей)
        self.offset = -1  # смещение (для полей)

    def __str__(self):
        return f"{self.lexem}"


class SymbolTable:
    """
    Таблица символов
    """
    def __init__(self):
        self.entries:List[SymbolTableEntry] = []  # записи
        self.orders:Dict[str, int] = {}  # порядковый номер по лексеме (на всякий случай)

        self.base_types:Dict[TypeCode, SymbolTableEntry] = {}  # базовые типы (доступ по TypeCode)
        self.record_types:Dict[str, SymbolTableEntry] = {}  # производные типы (доступ по лексеме)

        self.relation_codes = [OpCode.opEq,  OpCode.opNotEq, OpCode.opGreat,
                               OpCode.opGreatEq, OpCode.opLess, OpCode.opLessEq,
                               OpCode.opAnd, OpCode.opOr, OpCode.opNot]  # коды булевых операций

        self.next_addr = 0  # следующий свободный адрес в памяти
        self.temp_var_name = 0  # следующий уникальный номер временной переменной

    def __str__(self):
        text = ''
        for entry in self.entries:
            text += str(entry) + '\n'
        return text

    def get_record_type(self, lexem:str) -> Optional[SymbolTableEntry]:
        """
        Получить указатель на запись в таблице символов с типом структуры c именем lexem
        """
        if lexem in self.record_types.keys():
            return self.record_types[lexem]
        return None

    def get_base_type(self, type:TypeCode) -> SymbolTableEntry:
        """
        Получить указатель на запись в таблице символов с базовым типом по коду типа
        """
        return self.base_types[type]

    def find_lexem(self, lex) -> Optional[SymbolTableEntry]:
        """
        Получить указатель на запись в таблице символов с лексемой lexem (если есть)
        """
        if lex in self.orders:
            return self.entries[self.orders[lex]]
        return None

    def add_lexem(self, lex):
        """
        Добавить лексему
        """
        if lex in self.orders:
            return self.entries[self.orders[lex]]
        entry = SymbolTableEntry(lex)
        self.orders[lex] = len(self.entries)
        self.entries.append(entry)
        return entry

    def add_type(self, st_pointer: SymbolTableEntry, category: Category, new_type: SymbolTableEntry):
        """
        Добавить тип уже существующей лексеме
        """
        if st_pointer.category != Category.catNoCat:
            if st_pointer.category != Category.catConst:
                Type_Error(1, f"Идентификатор {st_pointer.lexem} должен быть уникальным")

        st_pointer.category = category
        st_pointer.type = new_type.type
        st_pointer.type.type_ptr = new_type
        if new_type.type.type_code not in self.base_types.keys():
            self.record_types[new_type.lexem] = new_type

        if category == Category.catVarName:
            while self.next_addr % new_type.type.width != 0:
                self.next_addr += 1
            st_pointer.address = self.next_addr
            self.next_addr += new_type.type.width

            # обработка структур
            if new_type.type.type_code == TypeCode.typeRecord:
                self.next_addr -= new_type.type.width
                for field in new_type.fields:
                    pnt = self.add_lexem(f'{st_pointer.lexem}.{field.lexem.split(".")[-1]}')
                    if field.type.type_code in self.base_types.keys():
                        self.add_type(pnt, Category.catVarName, self.get_base_type(field.type.type_code))
                    else:
                        self.add_type(pnt, Category.catVarName, self.get_record_type(field.type.type_ptr.lexem))
                    pnt.type.type_ptr = field
                    pnt.address = st_pointer.address + field.offset

                    if st_pointer.fields is None:
                        st_pointer.fields = [pnt]
                    else:
                        st_pointer.fields.append(pnt)

    def add_temp_var(self, var_type: SymbolTableEntry) -> SymbolTableEntry:
        """
        Создать временную переменную
        """
        temp_name = f't{self.temp_var_name}'
        self.temp_var_name += 1
        entry = self.add_lexem(temp_name)
        self.add_type(entry, Category.catVarName, var_type)

        return entry

    def add_field(self, record:SymbolTableEntry, field:SymbolTableEntry):
        """
        Привязать поле к структуре
        """
        base_addr = record.type.width
        while base_addr % field.type.width != 0:
            base_addr += 1
        field.offset = base_addr
        if record.fields is None:
            record.fields = [field]
        else:
            record.fields.append(field)
        record.type.width = base_addr + field.type.width

    def add_types(self):
        """
        Инициализировать таблицу базовыми типами
        """
        base_types = [TypeCode.typeInt, TypeCode.typeFloat, TypeCode.typeBool, TypeCode.typeVoid]
        type_words = ["Int", "Float", "Boolean", "Void"]
        for i in range(len(base_types)):
            pnt = self.add_lexem(type_words[i])
            pnt.category = Category.catTypeName
            pnt.type = Type(base_types[i])
            self.base_types[base_types[i]] = pnt

    def add_constants(self):
        """
        Инициализировать таблицу булевыми константами
        """
        constants = ["true", "false"]
        for i in range(len(constants)):
            pnt = self.add_lexem(constants[i])
            self.add_type(pnt, category=Category.catConst,
                                  new_type=self.get_base_type(TypeCode.typeBool))

    def form_variables_info(self):
        """
        Сформировать текстовое представление записей (для вывода на экран)
        """
        text = ""
        variables = []
        for entry in self.entries:
            if entry.address != -1:
                variables.append(entry)
        variables.sort(key=lambda e: e.address)

        for entry in variables:
            if entry.type.type_code == TypeCode.typeRecord and entry.type.type_ptr is not None:
                record_name = entry.type.type_ptr.lexem
            else:
                record_name = ""

            sep1 = '\t' * (entry.lexem.count('.'))
            sep2 = '\t' * (entry.lexem.count('.') + 1)

            text += f'{sep1}{str(entry.address).zfill(4)}: {entry.lexem}\n' \
                    f'{sep2}type = {entry.type.type_code} {record_name}\n' \
                    f'{sep2}size = {entry.type.width}\n\n'
        return text



