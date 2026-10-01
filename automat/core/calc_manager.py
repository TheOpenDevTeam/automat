"""
CalcManager — safe arithmetic calculator with recursive descent parser.
Extracted from AutomatApp._parse_expr / _eval_calc.
"""


class CalcManager:
    """Safe arithmetic expression evaluator (no eval, no builtins)."""

    OPERATORS = set("+-*/().% ")

    @staticmethod
    def evaluate(text: str) -> float:
        """Parse and evaluate a safe arithmetic expression."""
        text = text.strip()
        if not text:
            raise ValueError("Empty expression")

        allowed = set("0123456789+-*/().% ")
        if not all(ch in allowed for ch in text):
            raise ValueError(f"Invalid character in expression")

        tokens = CalcManager._tokenize(text)
        pos = [0]

        def peek():
            return tokens[pos[0]] if pos[0] < len(tokens) else None

        def consume(expected=None):
            t = peek()
            if expected and (t is None or t[1] != expected):
                raise ValueError(f"Expected {expected}, got {t}")
            pos[0] += 1
            return t

        def parse_atom():
            t = peek()
            if t is None:
                raise ValueError("Unexpected end")
            if t[0] == 'num':
                consume()
                return float(t[1])
            if t[1] == '(':
                consume('(')
                val = parse_addsub()
                consume(')')
                return val
            if t[1] == '-':
                consume('-')
                return -parse_atom()
            raise ValueError(f"Unexpected token: {t}")

        def parse_muldiv():
            val = parse_atom()
            while True:
                t = peek()
                if t and t[0] == 'op' and t[1] in '*/%':
                    op = consume()[1]
                    right = parse_atom()
                    if op == '*':
                        val *= right
                    elif op == '/':
                        if right == 0:
                            raise ZeroDivisionError("Division by zero")
                        val /= right
                    elif op == '%':
                        if right == 0:
                            raise ZeroDivisionError("Division by zero")
                        val %= right
                else:
                    break
            return val

        def parse_addsub():
            val = parse_muldiv()
            while True:
                t = peek()
                if t and t[0] == 'op' and t[1] in '+-':
                    op = consume()[1]
                    right = parse_muldiv()
                    if op == '+':
                        val += right
                    else:
                        val -= right
                else:
                    break
            return val

        result = parse_addsub()
        if pos[0] != len(tokens):
            raise ValueError("Unexpected trailing tokens")
        return result

    @staticmethod
    def _tokenize(text: str) -> list:
        tokens = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch in " \t":
                i += 1
                continue
            if ch.isdigit() or ch == '.':
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                num_str = text[i:j]
                if num_str.count('.') > 1 or num_str == '.':
                    raise ValueError(f"Invalid number: {num_str}")
                try:
                    float(num_str)
                except ValueError:
                    raise ValueError(f"Invalid number: {num_str}")
                tokens.append(('num', num_str))
                i = j
                continue
            if ch in '+-*/()%':
                tokens.append(('op', ch))
                i += 1
                continue
            raise ValueError(f"Unexpected char: {ch}")
        return tokens

    @staticmethod
    def is_valid(text: str) -> bool:
        """Check if expression is valid without evaluating."""
        try:
            CalcManager.evaluate(text)
            return True
        except Exception:
            return False
