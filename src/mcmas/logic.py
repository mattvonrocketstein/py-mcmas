"""
mcmas.logic.
"""

from typing import Any

import sympy
from pydantic_core import core_schema
from sympy import Eq as _Eq

# from sympy.logic.boolalg import BooleanFunction
from sympy.printing.str import StrPrinter

# from sympy import And, Or, Not, Eq, Lt, Gt
# from sympy.abc import *
# from sympy.printing.str import StrPrinter


class Function(sympy.Function):
    pass


class And(Function):
    def __str__(self):
        return " and ".join([str(x) for x in self._sorted_args])


class Or(Function):
    def __str__(self):
        return " or ".join([str(x) for x in self._sorted_args])


class Grouping(Function):
    def __str__(self):
        tmp = " ".join([str(x) for x in self._sorted_args])
        return f"({tmp})"


class If(Function):
    def __str__(self):
        if len(self._sorted_args) == 1:
            return f"if {self._sorted_args[0]}"
        else:
            assert len(self._sorted_args) == 2, "multiclause if not supported yet"
            return f"{self._sorted_args[0]} if {self._sorted_args[1]}"


class Eq(_Eq):
    def __str__(expr):
        return f"{expr.lhs}={expr.rhs}"


Equal = Eq


class Symbol(sympy.core.symbol.Symbol):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa
        handler,  # noqa
    ) -> core_schema.CoreSchema:
        """
        Return a Pydantic core schema for Symbol validation.

        This schema accepts: 1. Existing Symbol instances (passthrough)
        2. String names to create new Symbols 3. Dictionaries with
        'name' and optional symbol properties
        """

        def validate_symbol(value: Any) -> "Symbol":
            """
            Validate and convert input to Symbol.
            """
            if isinstance(value, sympy.core.symbol.Symbol):
                # If it's already a Symbol, return as-is (or convert to our class)
                if isinstance(value, cls):
                    return value
                else:
                    # Convert base Symbol to our extended Symbol
                    return cls(value.name, **value.assumptions0)
            elif isinstance(value, str):
                # Create Symbol from string name
                return cls(value)
            elif isinstance(value, dict):
                # Create Symbol from dictionary
                if "name" not in value:
                    raise ValueError("Dictionary must contain 'name' field")
                name = value["name"]
                # Extract symbol assumptions (like real=True, positive=True, etc.)
                assumptions = {k: v for k, v in value.items() if k != "name"}
                return cls(name, **assumptions)
            else:
                raise ValueError(
                    f"Cannot convert {type(value).__name__} to Symbol. "
                    f"Expected Symbol, str, or dict with 'name' field."
                )

        # Create the core schema (simplified version without custom serialization)
        return core_schema.no_info_plain_validator_function(validate_symbol)

    def __eq__(self, other):
        if isinstance(other, str):
            # Compare with symbol name
            return self.name == other
        elif isinstance(other, (int, float)):
            return False  # Symbols typically don't equal numbers
        return super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        # Maintain the parent's hash behavior
        return super().__hash__()

    def __and__(self, other):
        return self.__class__(f"{self.name} and {other}")

    def __or__(self, other):
        return self.__class__(f"{self.name} or {other}")

    def __rshift__(self, other):
        # return If(self, other)
        return self.__class__(f"{self.name} if {other}")

    def __imul__(self, other):
        return self.__class__(f"{self.name}={other}")

    def __add__(self, other):
        return self.__class__(f"{self.name}+{other}")

    def __lt__(self, other):
        return self.__class__(f"{self.name}<{other}")

    def __lte__(self, other):
        return self.__class__(f"{self.name}<={other}")

    def __gt__(self, other):
        return self.__class__(f"{self.name}>{other}")

    def __gte__(self, other):
        return self.__class__(f"{self.name}>={other}")

    def __call__(self, other):
        return self.__class__(f"{self.name}({other})")

    def __getattribute__(self, name):
        # Always try to get the actual attribute first
        try:
            attr = super().__getattribute__(name)
            # If it exists and is callable, return it
            if callable(attr):
                return attr
            # If it exists and is not callable, return it
            return attr
        except AttributeError:
            # Only create new symbols for names that don't exist as attributes
            # and don't start with underscore (to avoid internal methods)
            if not name.startswith("_"):
                current_name = super().__getattribute__("name")
                if current_name:
                    new_name = f"{current_name}.{name}"
                else:
                    new_name = f"{name}"
                return self.__class__(new_name)
            # If it starts with underscore, re-raise the AttributeError
            raise


class CustomStrPrinter(StrPrinter):
    def _print_Equality(self, expr):
        return f"{expr.lhs}={expr.rhs}"


printer = CustomStrPrinter()
sympy2ispl = printer.doprint

symbols = Symbol("")
true = symbols.true
false = symbols.false
Environment = symbols.Environment

# Temporal Operators / CTL
# EF φ	There exists a path where eventually φ holds
# AF φ	On all paths, eventually φ holds (φ is inevitable)
# EG φ	There exists a path where φ holds forever
# AG φ	On all paths, φ holds globally (φ is always true)
AF = symbols.AF
AG = symbols.AG
EF = symbols.EF
EG = symbols.EG

# Epistemic	Operators
# K(i, φ)	Agent i knows φ
# CK(G, φ)  Group Knowledge; φ is common knowledge in group G
K = symbols.K
CK = symbols.CK

# ATL <<G >>F φ	Group G can enforce φ eventually
