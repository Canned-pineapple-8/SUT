from sut.enums import Category, TypeCode, OpCode
from sut.symbol_table import SymbolTableEntry, SymbolTable, ST_Var, ST_Type
from sut.error import Type_Error
from typing import Any
from sut.instructions import IntructionTable
from sut.base_type import Type

class SemanticEngine:
    """
    Семантический движок (содержит все семантические действия)
    """
    def __init__(self, symbol_table: SymbolTable, instruction_table:IntructionTable):
        self.attr_stack = []  # стек атрибутов
        self.symbol_table = symbol_table  # указатель на таблицу символов
        self.instruction_table = instruction_table  # указатель на таблицу команд

    def push(self, value: Any):
        """
        Поместить атрибут в стек
        """
        self.attr_stack.append(value)

    def pop(self) -> Any:
        """
        Извлечь атрибут из стека
        """
        if not self.attr_stack:
            raise RuntimeError("Стек поврежден")
        return self.attr_stack.pop()

    def check_cat(self, pnt:SymbolTableEntry, expected_cat:Category, err_code:int, message:str = None):
        """
        Метод для проверки категории
        """
        if pnt.category != expected_cat:
            Type_Error(err_code, message)

    def execute(self, action_code: str, token):
        """
        Выполнить семантическое действие
        """
        method_name = f"A{action_code}"
        method = getattr(self, method_name, None)
        if not method:
            raise NotImplementedError(f"Семантическое действие {action_code} не определено")
        return method(token)

    # <-------- семантические действия -------->

    def A1(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1, f"Имя программы {ident.lexem} должно быть уникальным")
        self.symbol_table.add_type(ident, Category.catProgName, self.symbol_table.get_base_type(TypeCode.typeVoid))

    def A2(self, ident):
        self.check_cat(ident, Category.catNoCat, 1, f"Имя переменной {ident.lexem} должно быть уникальным")
        self.push(ident)

    def A3(self, token):
        t_type = self.pop()
        t_var = self.pop()
        self.symbol_table.add_type(t_var, Category.catVarName, t_type)

    def A4(self, token):
        t_type = self.pop()
        t_var = self.pop()
        self.symbol_table.add_type(t_var, Category.catVarName, t_type)
        self.push(t_type)

    def A5(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catTypeName, 2,
                       f"Идентификатор {ident.lexem} должен быть именем известного типа (базового или производного)")
        self.push(ident) # кладём указатель на тип

    def A6(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1, f"Идентификатор {ident.lexem} должен быть уникальным")
        r_ident = self.symbol_table.add_record_type(ident)
        self.push(r_ident)

    def A7(self, token):
        self.pop()

    def A8(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1, f"Идентификатор {ident.lexem} должен быть уникальным")
        self.push(ident)

    def A9(self, t_type:SymbolTableEntry):
        self.check_cat(t_type, Category.catTypeName, 2,
                       f"Идентификатор {t_type.lexem} должен быть именем известного типа (базового или производного)")
        t_field = self.pop()  # указатель на лексему поля
        t_record = self.pop()  # указатель на тип структуры

        f_ident = self.symbol_table.add_field_type(t_field, t_record, t_type)

        self.push(t_record)

    def A10(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3,
                       f"Операнд для присваивания {ident.lexem} должен быть именем переменной")
        self.push(ident)

    def A11(self, ident:SymbolTableEntry):
        t1 = self.pop()
        t2 = self.pop()
        t3 = self.pop()
        if t3.type.type_code != t2.type.type_code:
            Type_Error(4, f"Несовпадение типов в операции присваивания: {t3.type.type_code} ({t3.lexem}) и "
                          f"{t2.type.type_code} ({t2.lexem})")
        self.instruction_table.generate_instruction(OpCode.opAss, t1[0], -1, t3)

    def A12(self, ident:SymbolTableEntry):
        # self.check_cat(ident, Category.catTypeName, 5, f"Идентификатор поля {ident.lexem} должен быть определён")
        parent_record_id:SymbolTableEntry = self.pop()
        assert isinstance(parent_record_id, ST_Var)
        f_type = self.symbol_table.find_lexem(f"{parent_record_id.type.lexem}.{ident.lexem}")
        if not f_type or f_type.category != Category.catTypeName:
            Type_Error(5, f"Идентификатор поля {ident.lexem} должен быть определён")
        fields = parent_record_id.fields
        if not fields:
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        if not ident.lexem in [field.lexem.split(".")[-1] for field in fields]:
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem}')
        self.push(new_ident)

    def A13(self, ident:SymbolTableEntry):
        pass

    def A14(self, token):
        pass

    def A15(self, token):
        self.push(token)

    def A16(self, token):
        t1 = self.pop()
        t2 = self.pop()
        t3 = self.pop()
        t4 = self.pop()
        t5 = self.pop()
        if t5.type.type_code != t2.type.type_code:
            Type_Error(4, f"Несовпадение типов в операции {t3}: {t5.type.type_code} ({t5.lexem}) и "
                          f"{t2.type.type_code} ({t2.lexem})")
        t6 = self.symbol_table.add_temp_var(t2.type)
        if t3 in self.symbol_table.relation_codes:
            t6.type = self.symbol_table.get_base_type(TypeCode.typeBool)
        assert isinstance(t6, ST_Var)
        self.push(t6)
        self.push((t6, t6.address))
        self.instruction_table.generate_instruction(t3, t4[0], t1[0], t6)

    def A17(self, token):
        self.A15(token)

    def A18(self, token):
        self.A16(token)

    def A19(self, token):
        self.A15(token)

    def A20(self, token):
        self.A16(token)

    def A21(self, ident:SymbolTableEntry):
        assert isinstance(ident, ST_Var)
        self.push(ident)
        self.push((ident, ident.address))

    def A22(self, ident):
        self.A21(ident)

    def A23(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3, f"Идентификатор {ident.lexem} должен быть именем переменной")
        assert isinstance(ident, ST_Var)
        self.push(ident)
        self.push((ident, ident.address))

    def A24(self, ident):
        t1 = self.pop()
        t2 = self.pop()
        if t2.type.type_code != TypeCode.typeBool:
            Type_Error(6, f"Несовпадение типов в операции {OpCode.opNot}: {t2.type.type_code} ({t2.lexem}) и {TypeCode.typeBool}")
        t = self.symbol_table.add_temp_var(self.symbol_table.get_base_type(TypeCode.typeBool))
        assert isinstance(t, ST_Var)
        self.instruction_table.generate_instruction(OpCode.opNot, t1[0], -1, t)
        self.push(t2)
        self.push((t, t.address))

    def A25(self, token):
        expr_addr = self.pop()
        expr_type = self.pop()
        if expr_type.type.type_code != TypeCode.typeBool:
            Type_Error(7, f"Выражение в условном операторе должно иметь тип bool (текущий тип - {expr_type.type.type_code})")
        instruction = self.instruction_table.generate_instruction(OpCode.opGotoFalse, -1, -1, -1)
        falselist = self.instruction_table.make_list(instruction)
        self.push(falselist)

    def A26(self, token):
        instruction_goto = self.instruction_table.generate_instruction(OpCode.opGoto, -1, -1, -1)
        instruction = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        falselist = self.pop()
        self.instruction_table.backpatch(falselist, instruction.result)
        self.push(self.instruction_table.make_list(instruction_goto))

    def A27(self, token):
        label = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        falselist = self.pop()
        self.instruction_table.backpatch(falselist, label.result)

    def A28(self, token):
        falselist = self.pop()
        label = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        self.instruction_table.backpatch(falselist, label.result)

    def A29(self, ident):
        parent_record_id = self.pop()[0]
        assert isinstance(parent_record_id, ST_Var)
        f_type = self.symbol_table.find_lexem(f"{parent_record_id.type.lexem}.{ident.lexem}")
        if not f_type or f_type.category != Category.catTypeName:
            Type_Error(5, f"Идентификатор поля {ident.lexem} должен быть определён")
        factor_typ = self.pop()
        fields = parent_record_id.fields
        if not fields:
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        if not ident.lexem.split(".")[-1] in [field.lexem.split(".")[-1] for field in fields]:
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem.split(".")[-1]}')
        assert isinstance(new_ident, ST_Var)
        self.push(new_ident)
        self.push((new_ident, new_ident.address))