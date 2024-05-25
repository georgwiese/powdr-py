import os
import subprocess
from typing import Callable, Dict, Generator, List, Optional, Tuple, Union
from abc import ABC, abstractmethod

class Expression:
    def __init__(self):
        pass

    def subexpressions(self) -> List['Expression']:
        return []

    def visit(self, visitor: Callable[['Expression'], None]) -> None:
        visitor(self)
        for subexpression in self.subexpressions():
            subexpression.visit(visitor)

    def __eq__(self, other: Union['Expression', int]) -> 'PolynomialIdentity':
        if isinstance(other, int):
            other = NumberExpression(other)
        if isinstance(other, Expression):
            return PolynomialIdentity(self, other)
        else:
            raise TypeError("Operand must be an Expression or an integer")

    def __add__(self, other: Union['Expression', int]) -> 'AddExpression':
        if isinstance(other, int):
            other = NumberExpression(other)
        if isinstance(other, Expression):
            return AddExpression(self, other)
        else:
            raise TypeError("Operand must be an Expression or an integer")

    def __radd__(self, other: int) -> 'AddExpression':
        return self.__add__(other)

    def __sub__(self, other: Union['Expression', int]) -> 'SubExpression':
        if isinstance(other, int):
            other = NumberExpression(other)
        if isinstance(other, Expression):
            return SubExpression(self, other)
        else:
            raise TypeError("Operand must be an Expression or an integer")

    def __rsub__(self, other: int) -> 'SubExpression':
        return SubExpression(NumberExpression(other), self)

    def __mul__(self, other: Union['Expression', int]) -> 'MulExpression':
        if isinstance(other, int):
            other = NumberExpression(other)
        if isinstance(other, Expression):
            return MulExpression(self, other)
        else:
            raise TypeError("Operand must be an Expression or an integer")

    def __rmul__(self, other: int) -> 'MulExpression':
        return self.__mul__(other)

class NumberExpression(Expression):
    def __init__(self, number: int):
        super().__init__()
        self.number = number

    def __str__(self):
        return str(self.number)

class AddExpression(Expression):
    def __init__(self, left: 'Expression', right: 'Expression'):
        super().__init__()
        self.left = left
        self.right = right

    def subexpressions(self) -> List['Expression']:
        return [self.left, self.right]

    def __str__(self):
        return f"({str(self.left)} + {str(self.right)})"

class SubExpression(Expression):
    def __init__(self, left: 'Expression', right: 'Expression'):
        super().__init__()
        self.left = left
        self.right = right

    def subexpressions(self) -> List['Expression']:
        return [self.left, self.right]

    def __str__(self):
        return f"({str(self.left)} - {str(self.right)})"

class MulExpression(Expression):
    def __init__(self, left: 'Expression', right: 'Expression'):
        super().__init__()
        self.left = left
        self.right = right
    
    def subexpressions(self) -> List['Expression']:
        return [self.left, self.right]

    def __str__(self):
        return f"({str(self.left)} * {str(self.right)})"


class Column(ABC):

    @property
    @abstractmethod
    def declaration(self):
        pass


class WitnessColumn(Expression, Column):
    def __init__(self, name: str, is_next=False):
        super().__init__()
        self.name = name
        self.is_next = is_next

    @property
    def n(self):
        assert not self.is_next
        return WitnessColumn(self.name, is_next=True)
    
    @property
    def declaration(self):
        return f"col witness {self.name};"

    def __str__(self):
        return self.name + ("'" if self.is_next else "")

class FixedColumn(Expression, Column):
    def __init__(self, name: str, values: 'ConstantList', is_next=False):
        super().__init__()
        self.name = name
        self.values = values
        self.is_next = is_next

    @property
    def n(self):
        assert not self.is_next
        return FixedColumn(self.name, self.values, is_next=True)
    
    @property
    def declaration(self):
        return f"col fixed {self.name} = {self.values};"

    def __str__(self):
        return self.name + ("'" if self.is_next else "")
    
class IntermediateColumn(Expression, Column):
    def __init__(self, name: str, definition: 'Expression', is_next=False):
        super().__init__()
        self.name = name
        self.definition = definition
        self.is_next = is_next

    @property
    def n(self):
        assert not self.is_next
        return IntermediateColumn(self.name, self.declaration, is_next=True)
    
    @property
    def declaration(self):
        return f"col {self.name} = {self.definition};"
    
    def subexpressions(self) -> List[Expression]:
        return [self.definition]

    def __str__(self):
        return self.name + ("'" if self.is_next else "")
    
class Identity(ABC):
    @abstractmethod
    def collect_columns(self) -> Dict[str, Column]:
        pass

class PolynomialIdentity(Identity):
    def __init__(self, left: 'Expression', right: 'Expression'):
        super().__init__()
        self.left = left
        self.right = right
    
    def collect_columns(self) -> Dict[str, Column]:
        columns = {}
        self.left.visit(lambda expression: columns.update({expression.name: expression}) if isinstance(expression, Column) else None)
        self.right.visit(lambda expression: columns.update({expression.name: expression}) if isinstance(expression, Column) else None)
        return columns

    def __str__(self):
        return f"{str(self.left)} = {str(self.right)};"
    
class LookupIdentity(Identity):
    def __init__(self, left_selector: Optional['Expression'], left_expressions: List['Expression'], right_selector: Optional['Expression'], right_expressions: List['Expression']):
        super().__init__()
        self.left_selector = left_selector
        self.left_expressions = left_expressions
        self.right_selector = right_selector
        self.right_expressions = right_expressions
    
    def collect_columns(self) -> Dict[str, Column]:
        columns = {}
        if self.left_selector is not None:
            self.left_selector.visit(lambda expression: columns.update({expression.name: expression}) if isinstance(expression, Column) else None)
        if self.right_selector is not None:
            self.right_selector.visit(lambda expression: columns.update({expression.name: expression}) if isinstance(expression, Column) else None)
        for expression in self.left_expressions + self.right_expressions:
            expression.visit(lambda expression: columns.update({expression.name: expression}) if isinstance(expression, Column) else None)
        return columns
    
    def __str__(self):
        left_selector = "" if self.left_selector is None else f"{self.left_selector} "
        right_selector = "" if self.right_selector is None else f"{self.right_selector} "
        return f"{left_selector}{{ {', '.join(map(str, self.left_expressions))} }} in {right_selector}{{ {', '.join(map(str, self.right_expressions))} }};"

def lookup(left: Union[List['Expression'], Tuple['Expression', List['Expression']]], 
           right: Union[List['Expression'], Tuple['Expression', List['Expression']]]) -> LookupIdentity:
    
    left_selector, left_expressions = (left[0], left[1]) if isinstance(left, tuple) else (None, left)
    right_selector, right_expressions = (right[0], right[1]) if isinstance(right, tuple) else (None, right)
    
    return LookupIdentity(left_selector, left_expressions, right_selector, right_expressions)

class ConstantList:

    def __add__(self, other):
        if isinstance(other, list):
            return ConcatenatedList([self, other])
        elif isinstance(other, ConcatenatedList):
            return ConcatenatedList([self] + other.elements)
        else:
            raise TypeError("Operand must be a list or a ConcatenatedList")

    def __radd__(self, other):
        if isinstance(other, list):
            return ConcatenatedList([other, self])
        elif isinstance(other, ConcatenatedList):
            return ConcatenatedList(other.elements + [self])
        else:
            raise TypeError("Operand must be a list or a ConcatenatedList")


class StarredList(ConstantList):
    def __init__(self, elements):
        self.elements = elements

    def __str__(self):
        return f"[{', '.join(map(str, self.elements))}]*"

def star(elements):
    return StarredList(elements)
    
class ConcatenatedList(ConstantList):
    def __init__(self, elements=None):
        if elements is None:
            self.elements = []
        else:
            self.elements = elements

    def __str__(self):
        return ' + '.join(map(str, self.elements))

PIL = Generator[Identity, None, None]

def generate_pil(generator: Callable[[], PIL], n: int) -> str:

    constraints = list(generator())

    columns = {}
    for constraint in constraints:
        columns.update(constraint.collect_columns())
    
    pil = f"namespace Main({n}); \n"
    for column in columns.values():
        pil += f"    {column.declaration}\n"
    
    for constraint in constraints:
        pil += f"    {constraint}\n"
    
    return pil

def run(
    generator: Callable[[], PIL],
    n: int,
    field: str,
    powdr_cmd: list[str] = ["powdr"],
) -> None:
    pil = generate_pil(generator, n)
    filename = f"output/{generator.__name__}.pil"

    if not os.path.exists("output"):
        os.makedirs("output")

    with open(filename, "w") as file:
        file.write(pil)

    prover = "halo2-mock" if field == "bn254" else "estark-starky"

    subprocess.run(powdr_cmd + ["pil", filename, "-o", "output", "-f", "--field", field, "--prove-with", prover])

class Witness:
    def __init__(self):
        pass

class Fixed:
    def __init__(self, values: 'ConstantList'):
        self.values = values

class Circuit:
    def __setattr__(self, name, value):
        if isinstance(value, list):
            transformed_value = []
            for i, item in enumerate(value):
                if isinstance(item, Fixed):
                    transformed_value.append(FixedColumn(f"name_{i}", item.values))
                elif isinstance(item, Witness):
                    transformed_value.append(WitnessColumn(f"name_{i}"))
                else:
                    raise TypeError("List elements must be Fixed or Witness")
            self.__dict__[name] = transformed_value
        elif isinstance(value, Fixed):
            self.__dict__[name] = FixedColumn(name, value.values)
        elif isinstance(value, Witness):
            self.__dict__[name] = WitnessColumn(name)
        else:
            super().__setattr__(name, value)

