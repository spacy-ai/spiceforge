from __future__ import annotations

import re
from typing import Dict, List

from app.schema.simulation import AnalysisType

ANALYSIS_RE = re.compile(r"^\s*\.(ac|tran|op|dc)\b", re.IGNORECASE)
END_RE = re.compile(r"^\s*\.end\s*$", re.IGNORECASE)

_ANALYSIS_PATTERNS = [
    (AnalysisType.op, re.compile(r"^\.op\b", re.IGNORECASE)),
    (AnalysisType.ac, re.compile(r"^\.ac\b", re.IGNORECASE)),
    (AnalysisType.dc, re.compile(r"^\.dc\b", re.IGNORECASE)),
    (AnalysisType.tran, re.compile(r"^\.tran\b", re.IGNORECASE)),
    (AnalysisType.tf, re.compile(r"^\.tf\b", re.IGNORECASE)),
    (AnalysisType.noise, re.compile(r"^\.noise\b", re.IGNORECASE)),
    (AnalysisType.pz, re.compile(r"^\.pz\b", re.IGNORECASE)),
]


def detect_analyses(netlist: str) -> List[AnalysisType]:
    analyses: List[AnalysisType] = []
    for line in netlist.splitlines():
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        for analysis, pattern in _ANALYSIS_PATTERNS:
            if pattern.search(line):
                analyses.append(analysis)
                break
    return analyses


def extract_analysis_lines(netlist: str) -> Dict[AnalysisType, str]:
    lines: Dict[AnalysisType, str] = {}
    for raw_line in netlist.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue
        for analysis, pattern in _ANALYSIS_PATTERNS:
            if pattern.search(line) and analysis not in lines:
                lines[analysis] = line
                break
    return lines


def validate_netlist_text(netlist: str) -> None:
    if not netlist.strip():
        raise ValueError("Netlist is empty.")
    if ".end" not in netlist.lower():
        raise ValueError("Netlist missing .end line.")
    if not detect_analyses(netlist):
        raise ValueError("No analysis command found in netlist.")


def prepare_netlist(netlist: str, analysis_line: str) -> str:
    lines = []
    for line in netlist.splitlines():
        if ANALYSIS_RE.match(line):
            continue
        if END_RE.match(line):
            continue
        lines.append(line)
    lines.append(analysis_line)
    lines.append(".end")
    return "\n".join(lines) + "\n"
