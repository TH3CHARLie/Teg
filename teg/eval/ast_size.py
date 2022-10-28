from teg import (
    ITeg,
    Const,
    Var,
    Add,
    Mul,
    IfElse,
    Teg,
    Tup,
    LetIn,
    Bool,
    And,
    Or,
    Invert,
    SmoothFunc
)

def get_ast_size(expr: ITeg):
    if isinstance(expr, (Const, Var)):
        return 1

    elif isinstance(expr, (Add, Mul)):
        size = 1
        for e in expr.children:
            size += get_ast_size(e)
        return size

    elif isinstance(expr, SmoothFunc):
        return 1 + get_ast_size(expr.expr)

    elif isinstance(expr, Invert):
        return 1 + get_ast_size(expr.child)

    elif isinstance(expr, IfElse):
        return 1 + get_ast_size(expr.cond) + get_ast_size(expr.if_body) + get_ast_size(expr.else_body)

    elif isinstance(expr, Teg):
        return 1 + get_ast_size(expr.lower) + get_ast_size(expr.upper) + get_ast_size(expr.body) + get_ast_size(expr.dvar)

    elif isinstance(expr, Tup):
        size = 1
        for e in expr:
            size += get_ast_size(e)
        return size

    elif isinstance(expr, LetIn):
        size = 1
        for var, e in zip(expr.new_vars, expr.new_exprs):
            size += get_ast_size(var)
            size += get_ast_size(e)
        size += get_ast_size(expr.expr)
        return size

    elif {'FwdDeriv', 'RevDeriv'} & {t.__name__ for t in type(expr).__mro__}:
        return 1 + get_ast_size(expr.__getattribute__('deriv_expr'))

    elif isinstance(expr, (Bool, And, Or)):
        return 1 + get_ast_size(expr.left_expr) + get_ast_size(expr.right_expr)

    else:
        raise ValueError(f'The type of the expr "{type(expr)}" does not have a supported ast size.')

    assert False, f'Error getting ast size for expression {expr}'
    return -1
