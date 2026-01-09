from sut.enums import Category, OpCode
from sut.base_type import Type, TypeCode
from sut.error import Type_Error
from typing import Dict, List, Optional


class SymbolTableEntry:
    """
    Базовая запись таблицы символов
    """
    def __init__(self, lexem: str, category:Category = Category.catNoCat):
        self.lexem = lexem
        self.category = category

    def __str__(self):
        return self.lexem


class ST_Var(SymbolTableEntry):
    def __init__(self, lexem: str, category:Category = Category.catVarName):
        super().__init__(lexem, category)

        self.type: Optional["ST_Type"] = None
        self.fields: Optional[List["ST_Var"]] = None
        self.address: int = -1
        self.offset: int = -1

    @classmethod
    def from_base(cls, entry: SymbolTableEntry) -> "ST_Var":
        var = cls(entry.lexem, entry.category)
        return var


class ST_Type(SymbolTableEntry):
    def __init__(self, lexem: str, category: Category = Category.catTypeName):
        super().__init__(lexem, category)

        self.width: Optional[int] = None
        self.type_code: Optional[TypeCode] = None

        self.fields: Optional[List["ST_Type"]] = None
        self.offset: Optional[int] = None
        self.type: Optional["ST_Type"] = None

    @classmethod
    def from_base(cls, entry: SymbolTableEntry) -> "ST_Type":
        t = cls(entry.lexem, entry.category)
        t.width = 0
        return t


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

    def replace_entry(self, old_entry:SymbolTableEntry, new_entry:SymbolTableEntry) -> Optional[int]:
        if old_entry.lexem not in self.orders:
            return None
        self.entries[self.orders[old_entry.lexem]] = new_entry
        self.orders[new_entry.lexem] = self.orders[old_entry.lexem]
        if old_entry.lexem != new_entry.lexem:
            self.orders.pop(old_entry.lexem)

        return self.orders[new_entry.lexem]

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

    def add_record_type(self, st_pointer: SymbolTableEntry) -> SymbolTableEntry:
        """
        Добавить в таблицу символов тип структуры по идентификатору
        :param st_pointer: указатель на идентификатор
        :return: указатель на добавленный тип
        """
        r_type_pointer = ST_Type.from_base(st_pointer)
        r_type_pointer.category = Category.catTypeName
        r_type_pointer.type_code = TypeCode.typeRecord
        self.replace_entry(st_pointer, r_type_pointer)
        self.record_types[r_type_pointer.lexem] = r_type_pointer
        return r_type_pointer

    def add_field_type(self, st_pointer: SymbolTableEntry, r_type_pointer:SymbolTableEntry, f_base_type_pointer:SymbolTableEntry) -> SymbolTableEntry:
        assert isinstance(f_base_type_pointer, ST_Type)
        f_type_pointer = ST_Type.from_base(st_pointer)
        f_type_pointer.category = Category.catTypeName

        f_type_pointer.lexem = f"{r_type_pointer.lexem}.{st_pointer.lexem}"  # поменяли лексему на "структура.поле"
        f_type_pointer.width = f_base_type_pointer.width  # скопировали размер базового типа
        f_type_pointer.type_code = TypeCode.typeField  # выставили тип - поле

        f_type_pointer.type = f_base_type_pointer  # выставили указатель на базовый тип

        self.bind_field(f_type_pointer, r_type_pointer)  # рассчитали смещение и обновили размер структуры

        self.replace_entry(st_pointer, f_type_pointer)
        self.record_types[f_type_pointer.lexem] = f_type_pointer
        return f_type_pointer

    def bind_field(self, field:SymbolTableEntry, record:SymbolTableEntry):
        """
        Привязать поле к структуре
        """
        assert isinstance(field, ST_Type)
        assert isinstance(record, ST_Type)

        base_addr = record.width
        while base_addr % field.width != 0:
            base_addr += 1
        field.offset = base_addr
        if record.fields is None:
            record.fields = [field]
        else:
            record.fields.append(field)
        record.width = base_addr + field.width


    def add_type(self, st_pointer: SymbolTableEntry, category: Category, new_type: SymbolTableEntry):
        """
        Добавить тип уже существующей лексеме
        """
        assert isinstance(new_type, ST_Type)
        if st_pointer.category != Category.catNoCat and st_pointer.category != Category.catConst:
            Type_Error(1, f"Идентификатор {st_pointer.lexem} должен быть уникальным")

        var_pointer = ST_Var.from_base(st_pointer)
        var_pointer.category = category
        var_pointer.type = new_type

        if category == Category.catVarName:

            while self.next_addr % new_type.width != 0:
                self.next_addr += 1
            var_pointer.address = self.next_addr
            self.next_addr += new_type.width

            if new_type.type_code == TypeCode.typeRecord:
                self.next_addr -= new_type.width
                for t_field in new_type.fields:
                    v_field = self.add_lexem(f'{var_pointer.lexem}.{t_field.lexem.split(".")[-1]}')
                    if t_field.type.type_code in self.base_types.keys():
                        self.add_type(v_field, Category.catVarName, self.get_base_type(t_field.type.type_code))
                    else:
                        self.add_type(v_field, Category.catVarName, self.get_record_type(t_field.type.lexem))
                    v_field.type = t_field
                    v_field.address = var_pointer.address + t_field.offset
                    v_field.offset = t_field.offset

                    if var_pointer.fields is None:
                        var_pointer.fields = [v_field]
                    else:
                        var_pointer.fields.append(v_field)

        self.replace_entry(st_pointer, var_pointer)
        return var_pointer


    def add_temp_var(self, var_type: SymbolTableEntry) -> SymbolTableEntry:
        """
        Создать временную переменную
        """
        temp_name = f't{self.temp_var_name}'
        self.temp_var_name += 1
        entry = self.add_lexem(temp_name)
        t_temp_var = self.add_type(entry, Category.catVarName, var_type)
        return t_temp_var


    def add_types(self):
        """
        Инициализировать таблицу базовыми типами
        """
        base_types = [TypeCode.typeInt, TypeCode.typeFloat, TypeCode.typeBool, TypeCode.typeVoid]
        base_width = [4, 8, 1, 0]
        type_words = ["Int", "Float", "Boolean", "Void"]
        for i in range(len(base_types)):
            pnt = self.add_lexem(type_words[i])
            t_pnt = ST_Type.from_base(pnt)
            t_pnt.category = Category.catTypeName
            t_pnt.width = base_width[i]
            t_pnt.type_code = base_types[i]
            self.replace_entry(pnt, t_pnt)
            self.base_types[base_types[i]] = t_pnt

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
            if isinstance(entry, ST_Var) and entry.address is not None and entry.address != -1:
                variables.append(entry)
        variables.sort(key=lambda e: e.address)

        for entry in variables:
            if entry.type.type_code == TypeCode.typeRecord and entry.type is not None:
                record_name = entry.type.lexem
            else:
                record_name = ""

            sep1 = '\t' * (entry.lexem.count('.'))
            sep2 = '\t' * (entry.lexem.count('.') + 1)

            text += f'{sep1}{str(entry.address).zfill(4)}: {entry.lexem}\n' \
                    f'{sep2}type = {entry.type.type_code} {record_name}\n' \
                    f'{sep2}size = {entry.type.width}\n\n'
        return text



