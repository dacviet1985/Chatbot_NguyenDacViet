from __future__ import annotations

import ast
import logging
import operator
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


@dataclass(slots=True)
class ToolResult:
    name: str
    input_text: str
    output_text: str
    sources: list[dict[str, object]] | None = None


class CalculatorTool:
    """Safely evaluates simple arithmetic expressions."""

    name = "calculator"

    def can_handle(self, text: str) -> bool:
        normalized = text.lower().strip()
        if not normalized:
            return False
        if re.fullmatch(r"[\d\s\+\-\*\/\(\)\.\%]+", normalized):
            return True
        keywords = ("tính", "calculate", "bao nhiêu", "tong", "sum", "nhân", "chia")
        return any(keyword in normalized for keyword in keywords) and bool(re.search(r"\d", normalized))

    def extract_expression(self, text: str) -> str:
        cleaned = text.lower()
        replacements = {
            "x": "*",
            "nhân": "*",
            "chia": "/",
            "cộng": "+",
            "trừ": "-",
        }
        for source, target in replacements.items():
            cleaned = cleaned.replace(source, target)
        match = re.findall(r"[\d\s\+\-\*\/\(\)\.\%]+", cleaned)
        expression = "".join(match).strip()
        return expression

    def run(self, text: str) -> ToolResult:
        expression = self.extract_expression(text)
        if not expression:
            raise ValueError("Không tìm thấy biểu thức hợp lệ cho calculator.")
        result = self._evaluate(expression)
        logger.info("[TOOL] calculator | input=%s | result=%s", expression, result)
        return ToolResult(name=self.name, input_text=expression, output_text=str(result))

    def _evaluate(self, expression: str) -> float | int:
        node = ast.parse(expression, mode="eval")
        return self._eval_node(node.body)

    def _eval_node(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return _ALLOWED_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
            operand = self._eval_node(node.operand)
            return _ALLOWED_OPERATORS[type(node.op)](operand)
        raise ValueError("Biểu thức không được hỗ trợ.")
