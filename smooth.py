"""
    Declares popularly used smooth functions.
"""

from integrable_program import (
    ITeg,
    Const,
    Var,
    TegVar,
    SmoothFunc,
    Add,
    Mul,
    Invert,
    IfElse,
    Teg,
    Tup,
    LetIn,
    Ctx,
    ITegBool,
    Bool,
    And,
    Or,
    true,
    false,
)

import numpy as np


class Sqrt(SmoothFunc):
    """
        y = sqrt(x)
        TODO: Do we need bounds checks?
    """
    def __init__(self, expr:ITeg, name:str = "Sqrt"):
        super(Sqrt, self).__init__(expr = expr, name = name)

    def fwd_deriv(self, in_deriv_expr: ITeg):
        return Const(2) * Sqrt(self.expr) * in_deriv_expr

    def rev_deriv(self, out_deriv_expr: ITeg):
        return out_deriv_expr * Const(2) * Sqrt(self.expr)

    def operation(self, in_value):
        return np.sqrt(in_value)



class Sqr(SmoothFunc):
    """
        y = x**2
    """
    def __init__(self, expr:ITeg, name:str = "Sqr"):
        super(Sqr, self).__init__(expr = expr, name = name)

    def fwd_deriv(self, in_deriv_expr: ITeg):
        return Const(2) * self.expr * in_deriv_expr

    def rev_deriv(self, out_deriv_expr: ITeg):
        return out_deriv_expr * Const(2) * self.expr

    def operation(self, in_value):
        return in_value * in_value