from sut.enums import TypeCode


class Type:
    def __init__(self, type_code: TypeCode, width=0):
        self.type_code = type_code
        match type_code:
            case TypeCode.typeInt:
                self.width = 4
            case TypeCode.typeFloat:
                self.width = 8
            case TypeCode.typeBool:
                self.width = 1
            case _:
                self.width = width
        self.type_ptr = None





