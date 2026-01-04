from sut.enums import Category, OpCode
from sut.base_type import Type, TypeCode
from sut.error import Type_Error
from typing import Dict, List, Optional


class SymbolTableEntry:
    def __init__(self, lex):
        self.lexem = lex
        self.category = Category.catNoCat
        self.type = None
        self.fields = None
        self.address = -1
        self.offset = -1


    def __str__(self):
        return f"{self.lexem}: {self.category}, {self.type}, {self.address}, {self.offset}"

class SymbolTable:
    def __init__(self):
        self.entries:List[SymbolTableEntry] = []
        self.orders:Dict[str, int] = {}

        self.next_addr = 0
        self.temp_var_name = 0
        self.base_types = {}
        self.record_types = {}
        self.relation_codes = [ OpCode.opEq,  OpCode.opNotEq, OpCode.opGreat,
                   OpCode.opGreatEq, OpCode.opLess, OpCode.opLessEq,
                   OpCode.opAnd, OpCode.opOr, OpCode.opNot]

    def __str__(self):
        text = ''
        for entry in self.entries:
            text += str(entry) + '\n'
        return text

    def get_record_type(self, lexem:str) -> Optional[SymbolTableEntry]:
        if lexem in self.record_types.keys():
            return self.record_types[lexem]
        return None

    def get_base_type(self, type:TypeCode) -> SymbolTableEntry:
        return self.base_types[type]

    def find_lexem(self, lex) -> Optional[SymbolTableEntry]:
        if lex in self.orders:
            return self.entries[self.orders[lex]]
        return None

    def add_lexem(self, lex):
        if lex in self.orders:
            return self.entries[self.orders[lex]]
        entry = SymbolTableEntry(lex)
        self.orders[lex] = len(self.entries)
        self.entries.append(entry)
        return entry

    def add_type(self, st_pointer: SymbolTableEntry, category: Category, new_type: SymbolTableEntry):
        if st_pointer.category != Category.catNoCat:
            if st_pointer.category != Category.catConst:
                Type_Error(1)

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

            if new_type.type.type_code == TypeCode.typeRecord:
                for field in new_type.fields:
                    pnt = self.add_lexem(f'{st_pointer.lexem}.{field.lexem.split(".")[-1]}')
                    # тут нужно передавать не type, а указатель на структуру либо базовый тип (расширить метод таблицы символов, хранить все типы и искать по лексемам)
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
        temp_name = f't{self.temp_var_name}'
        self.temp_var_name += 1
        entry = self.add_lexem(temp_name)
        self.add_type(entry, Category.catVarName, var_type)

        return entry

    def add_field(self, record:SymbolTableEntry, field:SymbolTableEntry):
        base_addr = record.type.width
        while base_addr % field.type.width != 0:
            base_addr += 1
        field.offset = base_addr
        if record.fields is None:
            record.fields = [field]
        else:
            record.fields.append(field)
        record.type.width = base_addr + field.type.width



