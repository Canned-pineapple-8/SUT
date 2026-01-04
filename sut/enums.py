from enum import Enum


class Category(Enum):
    catNoCat = 0
    catProgName = 1
    catTypeName = 2
    catVarName = 3
    catConst = 4


class TypeCode(Enum):
    typeVoid = 0
    typeInt = 1
    typeFloat = 2
    typeBool = 3
    typeRecord = 4


class OpCode(Enum):
    opAdd = 0
    opSub = 1
    opMult = 2
    opDiv = 3
    opAss = 4
    opGoto = 5
    opGotoFalse = 6
    opIfRel = 7

    opEq = 8
    opNotEq = 9
    opGreat = 10
    opGreatEq = 11
    opLess = 12
    opLessEq = 13
    opAnd = 14
    opOr = 15
    opNot = 16

    label = 17





