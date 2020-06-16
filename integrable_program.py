from typing import *
import torch
import operator
import torch.nn as nn
import numpy as np


class Teg:

    def __init__(self, children, sign=1):
        super(Teg, self).__init__()
        self.children = children
        self.sign = sign
        self.value = None

    def __add__(self, other):
        return TegAdd([self, other])

    def __mul__(self, other):
        return TegMul([self, other])

    def __radd__(self, other):
        return other + self

    def __rmul__(self, other):
        return other * self

    def __iter__(self):
        yield self
        yield from (node for child in self.children for node in child)

    def __str__(self):
        children = [str(child) for child in self.children]
        return f'{self.name}({", ".join(children)})'

    def __neg__(self):
        return type(self)(children=self.children, sign=self.sign*-1)

    def eval(self, num_samples=50, ignore_cache=False) -> float:
        if self.value is None or ignore_cache:
            # Cache results as you go
            self.value = self.sign * self.operation(*[child.eval(num_samples, ignore_cache) for child in self.children])
        return self.value

    # def forward(self, num_samples=50, ignore_cache=False):
    #     return self.eval(num_samples, ignore_cache)

    def bind_variable(self, var_name: str, value: float) -> None:
        [child.bind_variable(var_name, value) for child in self.children]

    def unbind_variable(self, var_name: str) -> None:
        self.bind_variable(var_name, None)

    def backward(self):
        self.value.backward()

    @property
    def grad(self):
        return self.value.grad


class TegVariable(Teg):

    def __init__(self, name: str, value: float = None, sign: int = 1):
        super(TegVariable, self).__init__(children=[], sign=sign)
        self.name = name
        self.value = value

    def __add__(self, other):
        return TegAdd([self.clone(), other])

    def __mul__(self, other):
        return TegMul([self.clone(), other])

    def clone(self):
        return TegVariable(self.name, self.value, self.sign)

    def __lt__(self, other):
        return self.value < other

    def __iter__(self):
        yield self

    def __str__(self):
        value = '' if self.value is None else f'={self.value}'
        return f"{'-' if self.sign == -1 else ''}{self.name}{value}"

    def __repr__(self):
        return f'TegVariable(name={self.name}, value={self.value}, sign={self.sign})'

    def __neg__(self):
        return type(self)(name=self.name, value=self.value, sign=self.sign*-1)

    def eval(self, num_samples=50, ignore_cache=False) -> float:
        assert self.value is not None, f'The variable "{self.name}" must be bound to a value prior to evaluation.'
        return self.sign * self.value

    def bind_variable(self, var_name: str, value: float) -> None:
        if self.name == var_name:
            self.value = value


class TegAdd(Teg):
    name = "add"
    operation = operator.add


class TegMul(Teg):
    name = "mul"
    operation = operator.mul


class TegIntegral(Teg):
    name = "integral"

    def __init__(self, lower: Teg, upper: Teg, body: Teg, dvar: TegVariable):
        super(TegIntegral, self).__init__(children=[lower, upper, body, dvar])
        self.lower = lower
        self.upper = upper
        self.body = body
        self.dvar = dvar

    def __str__(self):
        return f'int_{{{str(self.lower)}}}^{{{str(self.upper)}}} {str(self.body)} d{self.dvar.name}'

    def __iter__(self):
        yield self

    def bind_variable(self, var_name: str, value: float):
        # If the integration variable is the same as the variable being bound
        # bind the variable in the bounds and leave the body alone.
        self.lower.bind_variable(var_name, value)
        self.upper.bind_variable(var_name, value)

        # Otherwise, bind the body and dump the cache (since a value changed) 
        if self.dvar.name != var_name:
            self.body.bind_variable(var_name, value)
            self.value = None

    def eval(self, num_samples=50, ignore_cache=False) -> float:
        if self.value is None or ignore_cache:
            lower = self.lower.eval(num_samples, ignore_cache)
            upper = self.upper.eval(num_samples, ignore_cache)
            sign = self.sign * (1 if lower < upper else -1)

            self.dvar.value = None

            # Sample different values of the variable (dvar) and evaluate
            # Currently do NON-DIFFERENTIABLE uniform sampling 
            def compute_samples(var_sample):
                self.body.bind_variable(self.dvar.name, var_sample)
                val = self.body.eval(num_samples, ignore_cache=True)
                return val

            var_samples, step = np.linspace(lower, upper, num_samples, retstep=True)
            body_at_samples = np.vectorize(compute_samples)(var_samples)

            # Trapezoidal rule
            y_left = body_at_samples[:-1]  # left endpoints
            y_right = body_at_samples[1:]  # right endpoints
            self.value = sign * (step / 2) * np.sum(y_left + y_right)
        return self.value


class TegConditional(Teg):
    name = 'conditional'

    def __init__(self, var: TegVariable, const: TegVariable, if_body: Teg, else_body: Teg):
        super(TegConditional, self).__init__(children=[var, const, if_body, else_body])
        self.var = var
        self.const = const
        self.if_body = if_body
        self.else_body = else_body

    def __str__(self):
        return f'if({self.var} < {self.const}): {self.if_body} else {self.else_body}'

    def __iter__(self):
        yield self

    def bind_variable(self, var_name: str, value: float):
        self.var.bind_variable(var_name, value)
        self.if_body.bind_variable(var_name, value)
        self.else_body.bind_variable(var_name, value)

    def eval(self, num_samples=50, ignore_cache=False) -> float:
        if self.value is None or ignore_cache:
            if self.var < self.const:
                self.value = self.if_body.eval(num_samples, ignore_cache)
            else:
                self.value = self.else_body.eval(num_samples, ignore_cache)
        return self.value
