from __future__ import annotations

from dataclasses import dataclass, field

_GRID = 2.54


@dataclass
class KiCadSymbolInfo:
    """Maps a SPICE component to its KiCad library symbol."""

    lib_id: str
    pin_numbers: list[str]
    pin_offsets: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class PlacedComponent:
    """A component with assigned schematic position."""

    component: "ParsedComponent"
    x: float
    y: float
    rotation: float
    symbol_info: KiCadSymbolInfo


@dataclass
class Wire:
    """A schematic wire segment."""

    start: tuple[float, float]
    end: tuple[float, float]


from app.core.kicad_export.parser import ParsedComponent  # noqa: E402
