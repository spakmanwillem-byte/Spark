"""
v6_capability_reken_001 — Veilige Nederlandse rekenmachine voor Spark.

Doel: zin als "hoeveel is 1 plus 1" / "12 keer 7" / "wortel van 81" / "1+1"
omzetten naar (uitdrukking, antwoord). Geen eval() — gebruikt ast met
whitelist van operators voor veiligheid.

Ondersteund:
  - getallen: 12, 3.14, 3,14 (NL-komma), -5
  - operators: + - * / % ** //
  - NL-woorden: plus, min, keer, maal, gedeeld door, gedeeld_door, modulo, kwadraat, wortel van
  - haakjes: ( )

Niet ondersteund (express): functies, variabelen, imports.
"""
from __future__ import annotations

import ast
import operator
import re
from typing import Optional, Tuple

import math

# Toegestane AST-nodes/operators voor veilige eval
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):  # py3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("alleen getallen toegestaan")
    if isinstance(node, ast.Num):  # legacy
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        # Beperkte set unaire functies
        fname = node.func.id
        if fname == "sqrt" and len(node.args) == 1:
            return math.sqrt(_safe_eval(node.args[0]))
        raise ValueError(f"functie {fname!r} niet toegestaan")
    raise ValueError(f"node {type(node).__name__} niet toegestaan")


# Word-to-symbol mapping. Volgorde belangrijk: meerwoord-patronen eerst.
_REPLACEMENTS = [
    # multi-word eerst zodat "gedeeld door" niet half blijft staan
    (r"\bgedeeld\s+door\b", "/"),
    (r"\bwortel\s+van\b", "sqrt"),
    (r"\bin\s+het\s+kwadraat\b", "**2"),
    (r"\bkwadraat\b", "**2"),
    (r"\bmodulo\b", "%"),
    (r"\bplus\b", "+"),
    (r"\bmin\b", "-"),
    (r"\bminus\b", "-"),
    (r"\bkeer\b", "*"),
    (r"\bmaal\b", "*"),
    (r"\bvermenigvuldigd\s+met\b", "*"),
    (r"\bgedeeld\b", "/"),
    (r"\bdelen\s+door\b", "/"),
    # v13d_math_word_numbers_001 (sessie 55) — Willem: "twee plus 5" faalde.
    # NL cijfer-woorden 0..20 + tientallen. Multi-word ("een en twintig") niet
    # gedekt maar de meest gangbare vormen wel.
    (r"\bnul\b", "0"),
    (r"\b(een|één)\b", "1"),
    (r"\btwee\b", "2"),
    (r"\bdrie\b", "3"),
    (r"\bvier\b", "4"),
    (r"\bvijf\b", "5"),
    (r"\bzes\b", "6"),
    (r"\bzeven\b", "7"),
    (r"\bacht\b", "8"),
    (r"\bnegen\b", "9"),
    (r"\btien\b", "10"),
    (r"\belf\b", "11"),
    (r"\btwaalf\b", "12"),
    (r"\bdertien\b", "13"),
    (r"\bveertien\b", "14"),
    (r"\bvijftien\b", "15"),
    (r"\bzestien\b", "16"),
    (r"\bzeventien\b", "17"),
    (r"\bachttien\b", "18"),
    (r"\bnegentien\b", "19"),
    (r"\btwintig\b", "20"),
    (r"\bdertig\b", "30"),
    (r"\bveertig\b", "40"),
    (r"\bvijftig\b", "50"),
    (r"\bzestig\b", "60"),
    (r"\bzeventig\b", "70"),
    (r"\btachtig\b", "80"),
    (r"\bnegentig\b", "90"),
    (r"\bhonderd\b", "100"),
    (r"\bduizend\b", "1000"),
    # vraagstellings-prefixen
    (r"^(hoeveel\s+is\s+|wat\s+is\s+|reken\s+(uit\s+)?|bereken\s+)", ""),
    # antwoord-suffix
    (r"\s*=\s*\??$", ""),
    (r"\s*\?+$", ""),
]


def _normalize(text: str) -> str:
    t = text.lower().strip()
    for pat, repl in _REPLACEMENTS:
        t = re.sub(pat, repl, t)
    # NL decimaal-komma → punt (alleen tussen cijfers)
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)
    # verwijder alles dat geen getal/operator/spatie/haakje/sqrt is
    t = re.sub(r"[^0-9+\-*/%().\s\^a-z]", " ", t)
    # ^ → ** als gebruiker dat typt
    t = t.replace("^", "**")
    # collapse spaties
    t = re.sub(r"\s+", "", t)
    # sqrt zonder haakjes: sqrt81 → sqrt(81), sqrt81+9 → sqrt(81)+9
    t = re.sub(r"sqrt(\d+(?:\.\d+)?)", r"sqrt(\1)", t)
    return t


# Pattern: tekst bevat ten minste 1 cijfer + 1 operator-of-NL-keyword
_KEYWORDS = re.compile(
    r"(\d.*[+\-*/%^].*\d|\bplus\b|\bmin\b|\bminus\b|\bkeer\b|\bmaal\b|"
    r"\bgedeeld(\s+door)?\b|\bdelen\s+door\b|\bkwadraat\b|\bwortel\s+van\b|\bmodulo\b|"
    r"\bvermenigvuldigd\b|\bbereken\b|\breken\s+uit\b|hoeveel\s+is\s+|wat\s+is\s+\d)",
    re.IGNORECASE,
)


def looks_like_math(text: str) -> bool:
    """Snelle filter — heeft de zin überhaupt iets rekenkundig in zich?"""
    if not text or len(text) > 200:
        return False
    if not re.search(r"\d", text):
        return False
    return bool(_KEYWORDS.search(text))


def try_evaluate(text: str) -> Optional[Tuple[str, float]]:
    """Probeer text → (genormaliseerde uitdrukking, resultaat).

    Returnt None als het geen geldige rekensom is.
    """
    if not looks_like_math(text):
        return None
    expr = _normalize(text)
    if not expr or len(expr) > 200:
        return None
    # Veiligheid: alleen toegestane characters in expr
    if not re.fullmatch(r"[0-9+\-*/%().sqrt\s]+", expr):
        return None
    try:
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree)
        if isinstance(result, complex):
            return None
        return expr, float(result)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None


def format_answer(text: str) -> Optional[str]:
    """Bouw een chat-vriendelijke regel met sommetje + antwoord.
    Returnt None als geen som."""
    res = try_evaluate(text)
    if not res:
        return None
    expr, value = res
    # Mooie weergave: int als heel, anders 4 decimalen
    if abs(value - round(value)) < 1e-9:
        v_str = str(int(round(value)))
    else:
        v_str = f"{value:.4f}".rstrip("0").rstrip(".")
    # NL: punt → komma in output
    v_str_nl = v_str.replace(".", ",")
    # Toon de genormaliseerde expr ook in NL-stijl voor leesbaarheid
    return f"🧮 `{expr}` = **{v_str_nl}**"
