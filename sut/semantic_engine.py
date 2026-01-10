from sut.enums import Category, TypeCode, OpCode
from sut.symbol_table import SymbolTableEntry, SymbolTable, ST_Var, ST_Type
from sut.error import Type_Error
from typing import Any
from sut.instructions import IntructionTable


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
        self.symbol_table.add_type(ident, Category.catProgName,
                                   self.symbol_table.get_base_type(TypeCode.typeVoid))  # добавить тип программы

    def A2(self, ident):
        self.check_cat(ident, Category.catNoCat, 1, f"Имя переменной {ident.lexem} должно быть уникальным")
        self.push(ident)  # поместить в стек указатель на имя переменной

    def A3(self, token):
        t_type = self.pop()  # тип переменной
        t_var = self.pop()  # переменная
        self.symbol_table.add_type(t_var, Category.catVarName, t_type)  # установить тип для переменной

    def A4(self, token):
        t_type = self.pop()  # тип переменной
        t_var = self.pop()  # переменная
        self.symbol_table.add_type(t_var, Category.catVarName, t_type)  # установить тип для переменной
        self.push(t_type)  # передать тип дальше

    def A5(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catTypeName, 2,
                       f"Идентификатор {ident.lexem} должен быть именем известного типа (базового или производного)")
        self.push(ident)  # поместить в стек указатель на тип

    def A6(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1, f"Идентификатор {ident.lexem} должен быть уникальным")
        r_ident = self.symbol_table.add_record_type(ident)  # добавить тип структуры
        self.push(r_ident)  # поместить в стек указатель на тип структуры

    def A7(self, token):
        self.pop()  # извлечь указатель на тип структуры после завершения инициализации типа структуры

    def A8(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1, f"Идентификатор {ident.lexem} должен быть уникальным")
        self.push(ident)  # поместить в стек указатель на поле

    def A9(self, t_type:SymbolTableEntry):
        self.check_cat(t_type, Category.catTypeName, 2,
                       f"Идентификатор {t_type.lexem} должен быть именем известного типа (базового или производного)")
        t_field = self.pop()  # поле
        t_record = self.pop()  # тип родительской структуры

        f_ident = self.symbol_table.add_field_type(t_field, t_record, t_type)  # добавить в таблицу тип поля

        self.push(t_record)  # вернуть тип структуры в стек

    def A10(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3,
                       f"Операнд для присваивания {ident.lexem} должен быть именем переменной")
        self.push(ident)  # поместить в стек указатель на переменную-приёмник

    def A11(self, ident:SymbolTableEntry):
        t1 = self.pop()  # результат выражения присваивания (источник)
        t2 = self.pop()  # приёмник
        if t2.type.type_code != t1.type.type_code:
            Type_Error(4, f"Несовпадение типов в операции присваивания: {t2.type.type_code} ({t2.lexem}) и "
                          f"{t1.type.type_code} ({t1.lexem})")
        self.instruction_table.generate_instruction(OpCode.opAss, t1, -1, t2)  # сгенерировать операцию присваивания

    def A12(self, ident:SymbolTableEntry):
        parent_record_id:SymbolTableEntry = self.pop()  # идентификатор структуры
        assert isinstance(parent_record_id, ST_Var)  # убедиться, что работаем с переменной

        f_type = self.symbol_table.find_lexem(f"{parent_record_id.type.lexem}.{ident.lexem}")
        # находим указатель на тип поля структуры, которому необходимо что-то присвоить

        if not f_type or f_type.category != Category.catTypeName:  # проверяем, что такое поле определено
            Type_Error(5, f"Идентификатор поля {ident.lexem} должен быть определён")
        fields = parent_record_id.fields

        if not fields:  # проверяем что у типа родительской структуры есть поля
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        if ident.lexem not in [field.lexem.split(".")[-1] for field in fields]:
            # проверяем что у типа родительской структуры есть именно такое поле
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")

        # находим указатель на поле конкретной переменной-структуры и заменяем её в стеке
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem}')
        self.push(new_ident)

    def A13(self, token):
        self.push(token)  # поместить в стек операцию

    def A14(self, token):
        t1 = self.pop()  # первый аргумент операции
        t2 = self.pop()  # тип операции
        t3 = self.pop()  # второй аргумент операции
        if t3.type.type_code != t1.type.type_code:
            Type_Error(4, f"Несовпадение типов в операции {t2}: {t3.type.type_code} ({t3.lexem}) и "
                          f"{t1.type.type_code} ({t1.lexem})")

        t4 = self.symbol_table.add_temp_var(t1.type)  # создаём временную переменную с результатом
        if t2 in self.symbol_table.relation_codes:  # если операция логическая, выставляем логический тип
            t4.type = self.symbol_table.get_base_type(TypeCode.typeBool)

        assert isinstance(t4, ST_Var)
        self.push(t4)  # поместить в стек результат операции
        self.instruction_table.generate_instruction(t2, t3, t1, t4)  # сгенерировать операцию

    def A15(self, token):
        self.A13(token)

    def A16(self, token):
        self.A14(token)

    def A17(self, token):
        self.A13(token)

    def A18(self, token):
        self.A14(token)

    def A19(self, ident:SymbolTableEntry):
        assert isinstance(ident, ST_Var)
        self.push(ident)  # поместить в стек идентификатор

    def A20(self, ident):
        self.A19(ident)

    def A21(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3, f"Идентификатор {ident.lexem} должен быть именем переменной")
        assert isinstance(ident, ST_Var)
        self.push(ident)  # поместить в стек идентификатор

    def A22(self, ident):
        t1 = self.pop()  # переменная для операции not
        if t1.type.type_code != TypeCode.typeBool:
            Type_Error(6, f"Несовпадение типов в операции {OpCode.opNot}: {t1.type.type_code} ({t1.lexem}) и {TypeCode.typeBool}")
        t = self.symbol_table.add_temp_var(self.symbol_table.get_base_type(TypeCode.typeBool))
        # создаём временную переменную с результатом
        assert isinstance(t, ST_Var)
        self.instruction_table.generate_instruction(OpCode.opNot, t1, -1, t)  # генерируем операцию
        self.push(t)  # поместить в стек результат операции

    def A23(self, token):
        expr_type = self.pop()  # результат выражения в условии
        if expr_type.type.type_code != TypeCode.typeBool:
            Type_Error(7, f"Выражение в условном операторе должно иметь тип bool (текущий тип - {expr_type.type.type_code})")
        instruction = self.instruction_table.generate_instruction(OpCode.opGotoFalse, -1, -1, -1)
        # генерируем условный переход после if
        falselist = self.instruction_table.make_list(instruction)
        self.push(falselist)  # поместить в стек для backpatching

    def A24(self, token):
        instruction_goto = self.instruction_table.generate_instruction(OpCode.opGoto, -1, -1, -1)
        # генерируем безусловный переход c перепрыгиыванием else в конце if
        instruction = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        # генерируем метку после else
        falselist = self.pop()
        self.instruction_table.backpatch(falselist, instruction.result)
        # устаналиваем метку в переход после if
        self.push(self.instruction_table.make_list(instruction_goto))

    def A25(self, token):
        label = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        # генерируем метку после else
        falselist = self.pop()
        self.instruction_table.backpatch(falselist, label.result)
        # устанавливаем метку в переход в конце блока if

    def A26(self, token):
        falselist = self.pop()
        # обработка случая if без else
        label = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        self.instruction_table.backpatch(falselist, label.result)

    def A27(self, ident):
        # подмена идентификатора структуры в стеке на идентификатор поля в выражении

        parent_record_id = self.pop() # идентификатор структуры
        assert isinstance(parent_record_id, ST_Var)  # убедиться, что работаем с переменной

        f_type = self.symbol_table.find_lexem(f"{parent_record_id.type.lexem}.{ident.lexem}")
        # находим указатель на тип поля структуры, которое будет участвовать в выражении

        if not f_type or f_type.category != Category.catTypeName:  # проверяем, что такое поле определено
            Type_Error(5, f"Идентификатор поля {ident.lexem} должен быть определён")
        fields = parent_record_id.fields

        if not fields: # проверяем что у типа родительской структуры есть поля
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")
        if not ident.lexem.split(".")[-1] in [field.lexem.split(".")[-1] for field in fields]:
            # проверяем что у типа родительской структуры есть именно такое поле
            Type_Error(6, f"Поле {ident.lexem.split('.')[-1]} для структуры {parent_record_id.type.lexem} не определено")

        # находим указатель на поле конкретной переменной-структуры и заменяем её в стеке
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem.split(".")[-1]}')
        assert isinstance(new_ident, ST_Var)
        self.push(new_ident)
