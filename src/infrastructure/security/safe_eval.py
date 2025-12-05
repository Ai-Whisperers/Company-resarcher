"""Safe expression evaluation without using eval() or exec().

This module provides safe alternatives to eval() and exec() for evaluating
mathematical expressions and simple conditions. It uses AST parsing to
prevent code injection attacks.

Example usage:
    from src.infrastructure.security.safe_eval import SafeExpressionEvaluator, SafeConditionEvaluator

    # Math expressions
    expr_eval = SafeExpressionEvaluator()
    result = expr_eval.evaluate("x + y * 2", {"x": 10, "y": 5})  # 20

    # Conditions
    cond_eval = SafeConditionEvaluator()
    result = cond_eval.evaluate("x > 5 and y < 10", {"x": 6, "y": 8})  # True
"""

import ast
import math
import operator
from typing import Any, Callable, Dict, List, Optional


class SafeEvalError(Exception):
    """Exception raised for safe evaluation errors."""

    pass


class UnsupportedOperationError(SafeEvalError):
    """Raised when an unsupported operation is attempted."""

    pass


class SafeExpressionEvaluator:
    """Safely evaluate mathematical expressions using AST parsing.

    This class provides a secure alternative to eval() for mathematical
    expressions. It parses the expression into an AST and only allows
    whitelisted operations.

    Supported operations:
        - Arithmetic: +, -, *, /, //, %, **
        - Comparisons: <, <=, >, >=, ==, !=
        - Unary: +, -
        - Functions: abs, min, max, round, sum, sqrt, log, exp, sin, cos, tan, sign

    Example:
        evaluator = SafeExpressionEvaluator()
        result = evaluator.evaluate("close / open - 1", {"close": 110, "open": 100})
    """

    # Binary operators
    BINARY_OPS: Dict[type, Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
    }

    # Comparison operators
    COMPARE_OPS: Dict[type, Callable[[Any, Any], bool]] = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }

    # Unary operators
    UNARY_OPS: Dict[type, Callable[[Any], Any]] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        ast.Invert: operator.invert,
    }

    # Boolean operators
    BOOL_OPS: Dict[type, Callable[[List[bool]], bool]] = {
        ast.And: all,
        ast.Or: any,
    }

    # Safe functions
    SAFE_FUNCTIONS: Dict[str, Callable] = {
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "sum": sum,
        "len": len,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "ceil": math.ceil,
        "floor": math.floor,
        "pow": pow,
        "sign": lambda x: 1 if x > 0 else (-1 if x < 0 else 0),
        "isnan": math.isnan,
        "isinf": math.isinf,
    }

    # Safe constants
    SAFE_CONSTANTS: Dict[str, Any] = {
        "pi": math.pi,
        "e": math.e,
        "inf": float("inf"),
        "nan": float("nan"),
        "True": True,
        "False": False,
        "None": None,
    }

    def __init__(
        self,
        additional_functions: Optional[Dict[str, Callable]] = None,
        additional_constants: Optional[Dict[str, Any]] = None,
        max_expression_length: int = 1000,
    ):
        """Initialize the evaluator.

        Args:
            additional_functions: Extra safe functions to allow.
            additional_constants: Extra constants to allow.
            max_expression_length: Maximum allowed expression length.
        """
        self.functions = dict(self.SAFE_FUNCTIONS)
        if additional_functions:
            self.functions.update(additional_functions)

        self.constants = dict(self.SAFE_CONSTANTS)
        if additional_constants:
            self.constants.update(additional_constants)

        self.max_expression_length = max_expression_length

    def evaluate(
        self,
        expression: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate a mathematical expression safely.

        Args:
            expression: The expression to evaluate.
            variables: Variable values to use in evaluation.

        Returns:
            The result of the expression.

        Raises:
            SafeEvalError: If the expression is invalid or uses unsafe operations.
        """
        if not expression or not expression.strip():
            raise SafeEvalError("Empty expression")

        if len(expression) > self.max_expression_length:
            raise SafeEvalError(
                f"Expression too long (max {self.max_expression_length} chars)"
            )

        variables = variables or {}

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise SafeEvalError(f"Syntax error in expression: {e}") from e

        try:
            return self._eval_node(tree.body, variables)
        except SafeEvalError:
            raise
        except ZeroDivisionError:
            return float("nan")
        except (ValueError, TypeError, OverflowError) as e:
            raise SafeEvalError(f"Evaluation error: {e}") from e
        except Exception as e:
            raise SafeEvalError(f"Unexpected error: {e}") from e

    def _eval_node(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        # Numbers
        if isinstance(node, ast.Constant):
            return node.value

        # For Python < 3.8 compatibility
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s

        # Variables/Names
        if isinstance(node, ast.Name):
            name = node.id
            if name in variables:
                return variables[name]
            if name in self.constants:
                return self.constants[name]
            if name in self.functions:
                return self.functions[name]
            raise SafeEvalError(f"Unknown variable or function: {name}")

        # Binary operations
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.BINARY_OPS:
                raise UnsupportedOperationError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left, variables)
            right = self._eval_node(node.right, variables)
            return self.BINARY_OPS[op_type](left, right)

        # Unary operations
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.UNARY_OPS:
                raise UnsupportedOperationError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval_node(node.operand, variables)
            return self.UNARY_OPS[op_type](operand)

        # Comparisons
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, variables)
            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in self.COMPARE_OPS:
                    raise UnsupportedOperationError(f"Unsupported comparison: {op_type.__name__}")
                right = self._eval_node(comparator, variables)
                if not self.COMPARE_OPS[op_type](left, right):
                    return False
                left = right
            return True

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in self.BOOL_OPS:
                raise UnsupportedOperationError(f"Unsupported boolean operator: {op_type.__name__}")
            values = [self._eval_node(v, variables) for v in node.values]
            return self.BOOL_OPS[op_type](values)

        # Function calls
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func, variables)
            if not callable(func):
                raise SafeEvalError(f"Not a callable: {func}")
            if func not in self.functions.values():
                # Check if it's a known safe function
                func_name = getattr(node.func, "id", None)
                if func_name not in self.functions:
                    raise SafeEvalError(f"Function not allowed: {func_name}")

            args = [self._eval_node(arg, variables) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value, variables) for kw in node.keywords}
            return func(*args, **kwargs)

        # Ternary (conditional) expression
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, variables)
            if test:
                return self._eval_node(node.body, variables)
            return self._eval_node(node.orelse, variables)

        # List literals
        if isinstance(node, ast.List):
            return [self._eval_node(elem, variables) for elem in node.elts]

        # Tuple literals
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem, variables) for elem in node.elts)

        # Dictionary literals
        if isinstance(node, ast.Dict):
            return {
                self._eval_node(k, variables): self._eval_node(v, variables)
                for k, v in zip(node.keys, node.values)
            }

        # Subscript (indexing)
        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, variables)
            if isinstance(node.slice, ast.Index):  # Python < 3.9
                index = self._eval_node(node.slice.value, variables)
            else:
                index = self._eval_node(node.slice, variables)
            return value[index]

        # Attribute access (limited)
        if isinstance(node, ast.Attribute):
            raise UnsupportedOperationError(
                "Attribute access not allowed for security reasons"
            )

        raise UnsupportedOperationError(f"Unsupported expression type: {type(node).__name__}")

    def validate(self, expression: str) -> tuple[bool, str]:
        """Validate an expression without evaluating it.

        Args:
            expression: The expression to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            if len(expression) > self.max_expression_length:
                return False, f"Expression too long (max {self.max_expression_length} chars)"

            tree = ast.parse(expression, mode="eval")
            self._validate_node(tree.body)
            return True, "Valid expression"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except SafeEvalError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"

    def _validate_node(self, node: ast.AST) -> None:
        """Validate that a node only uses safe operations."""
        if isinstance(node, (ast.Constant, ast.Num, ast.Str)):
            return

        if isinstance(node, ast.Name):
            return

        if isinstance(node, ast.BinOp):
            if type(node.op) not in self.BINARY_OPS:
                raise UnsupportedOperationError(f"Unsupported operator: {type(node.op).__name__}")
            self._validate_node(node.left)
            self._validate_node(node.right)
            return

        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.UNARY_OPS:
                raise UnsupportedOperationError(f"Unsupported unary operator")
            self._validate_node(node.operand)
            return

        if isinstance(node, ast.Compare):
            self._validate_node(node.left)
            for comparator in node.comparators:
                self._validate_node(comparator)
            return

        if isinstance(node, ast.BoolOp):
            for value in node.values:
                self._validate_node(value)
            return

        if isinstance(node, ast.Call):
            self._validate_node(node.func)
            for arg in node.args:
                self._validate_node(arg)
            for kw in node.keywords:
                self._validate_node(kw.value)
            return

        if isinstance(node, ast.IfExp):
            self._validate_node(node.test)
            self._validate_node(node.body)
            self._validate_node(node.orelse)
            return

        if isinstance(node, (ast.List, ast.Tuple)):
            for elem in node.elts:
                self._validate_node(elem)
            return

        if isinstance(node, ast.Dict):
            for k in node.keys:
                if k is not None:
                    self._validate_node(k)
            for v in node.values:
                self._validate_node(v)
            return

        if isinstance(node, ast.Subscript):
            self._validate_node(node.value)
            if isinstance(node.slice, ast.Index):
                self._validate_node(node.slice.value)
            else:
                self._validate_node(node.slice)
            return

        if isinstance(node, ast.Attribute):
            raise UnsupportedOperationError("Attribute access not allowed")

        raise UnsupportedOperationError(f"Unsupported expression type: {type(node).__name__}")


class SafeConditionEvaluator(SafeExpressionEvaluator):
    """Evaluate boolean conditions safely.

    This is a specialized version of SafeExpressionEvaluator for
    evaluating conditions in if/else statements.

    Example:
        evaluator = SafeConditionEvaluator()
        result = evaluator.evaluate("x > 5 and y < 10", {"x": 6, "y": 8})
    """

    def evaluate(
        self,
        condition: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate a condition and return a boolean.

        Args:
            condition: The condition to evaluate.
            variables: Variable values to use in evaluation.

        Returns:
            The boolean result of the condition.
        """
        result = super().evaluate(condition, variables)
        return bool(result)


# Singleton instances for convenience
_expr_evaluator: Optional[SafeExpressionEvaluator] = None
_cond_evaluator: Optional[SafeConditionEvaluator] = None


def get_expression_evaluator() -> SafeExpressionEvaluator:
    """Get singleton expression evaluator."""
    global _expr_evaluator
    if _expr_evaluator is None:
        _expr_evaluator = SafeExpressionEvaluator()
    return _expr_evaluator


def get_condition_evaluator() -> SafeConditionEvaluator:
    """Get singleton condition evaluator."""
    global _cond_evaluator
    if _cond_evaluator is None:
        _cond_evaluator = SafeConditionEvaluator()
    return _cond_evaluator


def safe_eval(expression: str, variables: Optional[Dict[str, Any]] = None) -> Any:
    """Convenience function for safe expression evaluation.

    Args:
        expression: The expression to evaluate.
        variables: Variable values to use.

    Returns:
        The result of the expression.
    """
    return get_expression_evaluator().evaluate(expression, variables)


def safe_eval_condition(condition: str, variables: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function for safe condition evaluation.

    Args:
        condition: The condition to evaluate.
        variables: Variable values to use.

    Returns:
        The boolean result.
    """
    return get_condition_evaluator().evaluate(condition, variables)
