from __future__ import annotations


def parse_spice_value(text: str) -> float:
    suffixes = {
        "t": 1e12,
        "g": 1e9,
        "meg": 1e6,
        "k": 1e3,
        "m": 1e-3,
        "u": 1e-6,
        "n": 1e-9,
        "p": 1e-12,
        "f": 1e-15,
    }
    token = text.strip().lower()
    for suffix, multiplier in sorted(suffixes.items(), key=lambda item: -len(item[0])):
        if token.endswith(suffix):
            return float(token[: -len(suffix)]) * multiplier
    return float(token)
