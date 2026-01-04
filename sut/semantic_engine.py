from sut.enums import Category, TypeCode, OpCode
from sut.symbol_table import SymbolTableEntry, SymbolTable
from sut.error import Type_Error
from typing import Any
from sut.instructions import IntructionTable
from sut.base_type import Type


class SemanticEngine:
    def __init__(self, symbol_table: SymbolTable, instruction_table:IntructionTable):
        self.attr_stack = []             # стек атрибутов
        self.symbol_table = symbol_table
        self.instruction_table = instruction_table

    # стек атрибутов
    def push(self, value: Any):
        self.attr_stack.append(value)

    def pop(self) -> Any:
        if not self.attr_stack:
            raise RuntimeError("Стек поврежден")
        return self.attr_stack.pop()

    # базовые вспомогательные методы
    def check_cat(self, pnt:SymbolTableEntry, expected_cat:Category, err_code:int):
        if pnt.category != expected_cat:
            Type_Error(err_code)

    # семантические действия
    def execute(self, action_code: str, token):
        method_name = f"A{action_code}"
        method = getattr(self, method_name, None)
        if not method:
            raise NotImplementedError(f"Семантическое действие {action_code} не определено")
        return method(token)

    def A1(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1)
        self.symbol_table.add_type(ident, Category.catProgName, self.symbol_table.get_base_type(TypeCode.typeVoid))

    def A2(self, ident):
        self.check_cat(ident, Category.catNoCat, 1)
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
        self.check_cat(ident, Category.catTypeName, 2)
        self.push(ident) # кладём указатель на тип

    def A6(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1)
        type_pnt = self.symbol_table.add_lexem("temp_type")
        type_pnt.type = Type(TypeCode.typeRecord)
        self.symbol_table.add_type(ident, Category.catTypeName, type_pnt)
        self.push(ident)

    def A7(self, token):
        self.pop()

    def A8(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catNoCat, 1)
        self.push(ident)

    def A9(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catTypeName, 2)
        field = self.pop()  # указатель на лексему поля (age)
        record = self.pop()  # указатель на тип Person

        self.symbol_table.add_type(field, Category.catTypeName, ident)
        field.lexem = f"{record.lexem}.{field.lexem}"
        # возможно убрать лексему "age"

        self.symbol_table.add_field(record, field)
        self.push(record)

    def A10(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3)
        self.push(ident)

    def A11(self, ident:SymbolTableEntry):
        t1 = self.pop()
        t2 = self.pop()
        t3 = self.pop()
        if t3.type.type_code != t2.type.type_code:
            Type_Error(4)
        self.instruction_table.generate_instruction(OpCode.opAss, t1[0], -1, t3)

    def A12(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catTypeName, 5)
        parent_record_id:SymbolTableEntry = self.pop()
        fields = self.symbol_table.find_lexem(parent_record_id.lexem).fields
        if not fields:
            Type_Error(6)
        if not ident.lexem.split(".")[-1] in [field.lexem.split(".")[-1] for field in fields]:
            Type_Error(6)
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem.split(".")[-1]}')
        # self.push(parent_record_id)
        self.push(new_ident)

    def A13(self, ident:SymbolTableEntry):
        pass

    def A14(self, token):
        pass
        #ident = self.pop()
        #address = (ident[0], ident[1])
        #self.push(ident[0].type)
        #self.push(address)

    def A15(self, token):
        self.push(token)

    def A16(self, token):
        t1 = self.pop()
        t2 = self.pop()
        t3 = self.pop()
        t4 = self.pop()
        t5 = self.pop()
        if t5.type.type_code != t2.type.type_code:
            Type_Error(4)
        if t3 in self.symbol_table.relation_codes:
            self.push(self.symbol_table.get_base_type(TypeCode.typeBool))
        else:
            self.push(t2)
        t6 = self.symbol_table.add_temp_var(t2)
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
        self.push(ident)
        self.push((ident, ident.address))

    def A22(self, ident):
        self.A21(ident)

    def A23(self, ident:SymbolTableEntry):
        self.check_cat(ident, Category.catVarName, 3)
        self.push(ident)
        self.push((ident, ident.address))

    def A24(self, ident):
        t1 = self.pop()
        t2 = self.pop()
        if t2.type.type_code != TypeCode.typeBool:
            Type_Error(6)
        t = self.symbol_table.add_temp_var(self.symbol_table.get_base_type(TypeCode.typeBool))
        self.instruction_table.generate_instruction(OpCode.opNot, t1[0], -1, t)
        self.push(t2)
        self.push((t, t.address))

    def A25(self, token):
        expr_addr = self.pop()
        expr_type = self.pop()
        instruction = self.instruction_table.generate_instruction(OpCode.opGotoFalse, -1, -1, -1)
        falselist = self.instruction_table.make_list(instruction)
        self.push(falselist)

    def A26(self, token):
        instruction_goto = self.instruction_table.generate_instruction(OpCode.opGoto, -1, -1, -1)
        instruction = self.instruction_table.generate_instruction(OpCode.label, -1, -1, -1)
        falselist = self.pop()
        self.instruction_table.backpatch(falselist, instruction.result)
        self.push(self.instruction_table.make_list(instruction_goto))
        pass

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
        factor_typ = self.pop()
        fields = self.symbol_table.find_lexem(parent_record_id.lexem).fields
        if not fields:
            Type_Error(6)
        if not ident.lexem.split(".")[-1] in [field.lexem.split(".")[-1] for field in fields]:
            Type_Error(6)
        new_ident = self.symbol_table.find_lexem(f'{parent_record_id.lexem}.{ident.lexem.split(".")[-1]}')
        self.push(new_ident)
        self.push((new_ident, new_ident.address))
