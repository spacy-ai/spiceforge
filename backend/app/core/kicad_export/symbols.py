from __future__ import annotations

from app.core.kicad_export.types import KiCadSymbolInfo

_SYMBOL_MAP: dict[str, KiCadSymbolInfo] = {
    "R": KiCadSymbolInfo("Device:R", ["1", "2"], [(0, -3.81), (0, 3.81)]),
    "C": KiCadSymbolInfo("Device:C", ["1", "2"], [(0, -2.54), (0, 2.54)]),
    "L": KiCadSymbolInfo("Device:L", ["1", "2"], [(0, -3.81), (0, 3.81)]),
    "D": KiCadSymbolInfo("Device:D", ["K", "A"], [(0, -2.54), (0, 2.54)]),
    "V": KiCadSymbolInfo("Simulation_SPICE:VDC", ["1", "2"], [(0, -3.81), (0, 3.81)]),
    "I": KiCadSymbolInfo("Simulation_SPICE:IDC", ["1", "2"], [(0, -3.81), (0, 3.81)]),
    "Q_NPN": KiCadSymbolInfo(
        "Device:Q_NPN_BCE",
        ["B", "C", "E"],
        [(-2.54, 0), (0, -2.54), (0, 2.54)],
    ),
    "Q_PNP": KiCadSymbolInfo(
        "Device:Q_PNP_BCE",
        ["B", "C", "E"],
        [(-2.54, 0), (0, -2.54), (0, 2.54)],
    ),
    "M_NMOS": KiCadSymbolInfo(
        "Device:Q_NMOS_GDS",
        ["G", "D", "S"],
        [(-2.54, 0), (0, -2.54), (0, 2.54)],
    ),
    "M_PMOS": KiCadSymbolInfo(
        "Device:Q_PMOS_GDS",
        ["G", "D", "S"],
        [(-2.54, 0), (0, -2.54), (0, 2.54)],
    ),
}


def resolve_symbol_info(comp_type: str, value: str) -> KiCadSymbolInfo:
    if comp_type == "Q":
        if "pnp" in value.lower():
            return _SYMBOL_MAP["Q_PNP"]
        return _SYMBOL_MAP["Q_NPN"]
    if comp_type == "M":
        if "pmos" in value.lower():
            return _SYMBOL_MAP["M_PMOS"]
        return _SYMBOL_MAP["M_NMOS"]
    if comp_type == "X":
        pin_numbers = [str(i + 1) for i in range(10)]
        return KiCadSymbolInfo(
            "Simulation_SPICE:SUBCKT",
            pin_numbers,
            [(0, i * 2.54) for i in range(10)],
        )
    if comp_type in _SYMBOL_MAP:
        return _SYMBOL_MAP[comp_type]
    return KiCadSymbolInfo("Device:R", ["1", "2"], [(0, -3.81), (0, 3.81)])


_LIB_SYMBOL_TEMPLATES: dict[str, str] = {
    "Device:R": """
    (symbol \"Device:R\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"R\" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Value\" \"R\" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"R_0_1\"
        (rectangle (start -1.016 -3.81) (end 1.016 3.81)
          (stroke (width 0) (type default)) (fill (type none))
        )
      )
      (symbol \"R_1_1\"
        (pin passive line (at 0 3.81 270) (length 0) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 0) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:C": """
    (symbol \"Device:C\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"C\" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Value\" \"C\" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"C_0_1\"
        (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))
          (stroke (width 0.3048) (type default)) (fill (type none))
        )
        (polyline (pts (xy -1.524 0.508) (xy 1.524 0.508))
          (stroke (width 0.3048) (type default)) (fill (type none))
        )
      )
      (symbol \"C_1_1\"
        (pin passive line (at 0 2.54 270) (length 2.032) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -2.54 90) (length 2.032) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:L": """
    (symbol \"Device:L\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"L\" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Value\" \"L\" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"L_0_1\"
        (arc (start 0 -3.81) (mid 0.6323 -3.1777) (end 0 -2.54)
          (stroke (width 0) (type default)) (fill (type none))
        )
        (arc (start 0 -2.54) (mid 0.6323 -1.9077) (end 0 -1.27)
          (stroke (width 0) (type default)) (fill (type none))
        )
        (arc (start 0 -1.27) (mid 0.6323 -0.6377) (end 0 0)
          (stroke (width 0) (type default)) (fill (type none))
        )
        (arc (start 0 0) (mid 0.6323 0.6323) (end 0 1.27)
          (stroke (width 0) (type default)) (fill (type none))
        )
        (arc (start 0 1.27) (mid 0.6323 1.9023) (end 0 2.54)
          (stroke (width 0) (type default)) (fill (type none))
        )
        (arc (start 0 2.54) (mid 0.6323 3.1723) (end 0 3.81)
          (stroke (width 0) (type default)) (fill (type none))
        )
      )
      (symbol \"L_1_1\"
        (pin passive line (at 0 3.81 270) (length 0) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 0) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:D": """
    (symbol \"Device:D\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"D\" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property \"Value\" \"D\" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"D_0_1\"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy -1.27 0) (xy 1.27 0))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 1.27 -1.27) (xy -1.27 0) (xy 1.27 1.27) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol \"D_1_1\"
        (pin passive line (at -2.54 0 0) (length 2.54) (name \"K\" (effects (font (size 1.27 1.27)))) (number \"K\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 0 180) (length 2.54) (name \"A\" (effects (font (size 1.27 1.27)))) (number \"A\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Simulation_SPICE:VDC": """
    (symbol \"Simulation_SPICE:VDC\" (pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"V\" (at 2.54 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"VDC\" (at 2.54 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"VDC_0_1\"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
        (polyline (pts (xy -0.762 1.27) (xy 0.762 1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0 0.762) (xy 0 1.778))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0 -1.778) (xy 0 -0.762))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol \"VDC_1_1\"
        (pin passive line (at 0 3.81 270) (length 1.27) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Simulation_SPICE:IDC": """
    (symbol \"Simulation_SPICE:IDC\" (pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"I\" (at 2.54 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"IDC\" (at 2.54 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"IDC_0_1\"
        (circle (center 0 0) (radius 2.54)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
        (polyline (pts (xy 0 -1.778) (xy 0 1.778))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy -0.508 1.016) (xy 0 1.778) (xy 0.508 1.016))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol \"IDC_1_1\"
        (pin passive line (at 0 3.81 270) (length 1.27) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name \"~\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:Q_NPN_BCE": """
    (symbol \"Device:Q_NPN_BCE\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"Q\" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"Q_NPN_BCE\" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"Q_NPN_BCE_0_1\"
        (polyline (pts (xy 0.635 0.635) (xy 2.54 2.54))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.635 -0.635) (xy 2.54 -2.54))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.635 1.905) (xy 0.635 -1.905))
          (stroke (width 0.3048) (type default)) (fill (type none))
        )
        (polyline (pts (xy 1.27 -1.524) (xy 2.286 -2.286) (xy 1.778 -0.762))
          (stroke (width 0) (type default)) (fill (type outline))
        )
      )
      (symbol \"Q_NPN_BCE_1_1\"
        (pin passive line (at -2.54 0 0) (length 3.175) (name \"B\" (effects (font (size 1.27 1.27)))) (number \"B\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 2.54 270) (length 2.54) (name \"C\" (effects (font (size 1.27 1.27)))) (number \"C\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -2.54 90) (length 2.54) (name \"E\" (effects (font (size 1.27 1.27)))) (number \"E\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:Q_PNP_BCE": """
    (symbol \"Device:Q_PNP_BCE\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"Q\" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"Q_PNP_BCE\" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"Q_PNP_BCE_0_1\"
        (polyline (pts (xy 0.635 0.635) (xy 2.54 2.54))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.635 -0.635) (xy 2.54 -2.54))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.635 1.905) (xy 0.635 -1.905))
          (stroke (width 0.3048) (type default)) (fill (type none))
        )
        (polyline (pts (xy 2.286 1.524) (xy 1.778 -0.762) (xy 1.27 1.524))
          (stroke (width 0) (type default)) (fill (type outline))
        )
      )
      (symbol \"Q_PNP_BCE_1_1\"
        (pin passive line (at -2.54 0 0) (length 3.175) (name \"B\" (effects (font (size 1.27 1.27)))) (number \"B\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 2.54 270) (length 2.54) (name \"C\" (effects (font (size 1.27 1.27)))) (number \"C\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -2.54 90) (length 2.54) (name \"E\" (effects (font (size 1.27 1.27)))) (number \"E\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:Q_NMOS_GDS": """
    (symbol \"Device:Q_NMOS_GDS\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"Q\" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"Q_NMOS_GDS\" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"Q_NMOS_GDS_0_1\"
        (polyline (pts (xy 0.254 0) (xy -2.54 0))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol \"Q_NMOS_GDS_1_1\"
        (pin passive line (at -2.54 0 0) (length 2.794) (name \"G\" (effects (font (size 1.27 1.27)))) (number \"G\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 2.54 270) (length 2.54) (name \"D\" (effects (font (size 1.27 1.27)))) (number \"D\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -2.54 90) (length 2.54) (name \"S\" (effects (font (size 1.27 1.27)))) (number \"S\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Device:Q_PMOS_GDS": """
    (symbol \"Device:Q_PMOS_GDS\" (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"Q\" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Value\" \"Q_PMOS_GDS\" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property \"Footprint\" \"\" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"Q_PMOS_GDS_0_1\"
        (polyline (pts (xy 0.254 0) (xy -2.54 0))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol \"Q_PMOS_GDS_1_1\"
        (pin passive line (at -2.54 0 0) (length 2.794) (name \"G\" (effects (font (size 1.27 1.27)))) (number \"G\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 2.54 270) (length 2.54) (name \"D\" (effects (font (size 1.27 1.27)))) (number \"D\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -2.54 90) (length 2.54) (name \"S\" (effects (font (size 1.27 1.27)))) (number \"S\" (effects (font (size 1.27 1.27)))))
      )
    )""",
    "Simulation_SPICE:SUBCKT": """
    (symbol \"Simulation_SPICE:SUBCKT\" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"X\" (at 0 1.27 0) (effects (font (size 1.27 1.27))))
      (property \"Value\" \"SUBCKT\" (at 0 -1.27 0) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"~\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"SUBCKT_0_1\"
        (rectangle (start -5.08 -7.62) (end 5.08 7.62)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol \"SUBCKT_1_1\"
        (pin passive line (at -7.62 5.08 0) (length 2.54) (name \"1\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 2.54 0) (length 2.54) (name \"2\" (effects (font (size 1.27 1.27)))) (number \"2\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 0 0) (length 2.54) (name \"3\" (effects (font (size 1.27 1.27)))) (number \"3\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 -2.54 0) (length 2.54) (name \"4\" (effects (font (size 1.27 1.27)))) (number \"4\" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 -5.08 0) (length 2.54) (name \"5\" (effects (font (size 1.27 1.27)))) (number \"5\" (effects (font (size 1.27 1.27)))))
      )
    )""",
}


def build_lib_symbols(used_lib_ids: set[str]) -> str:
    parts: list[str] = []
    parts.append("  (lib_symbols")
    for lib_id in sorted(used_lib_ids):
        if lib_id in _LIB_SYMBOL_TEMPLATES:
            parts.append(_LIB_SYMBOL_TEMPLATES[lib_id])
    parts.append("  )")
    return "\n".join(parts)


GND_LIB_SYMBOL = """
    (symbol \"power:GND\" (power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property \"Reference\" \"#PWR\" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Value\" \"GND\" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property \"Footprint\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property \"Datasheet\" \"\" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol \"GND_0_1\"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
          (stroke (width 0) (type default)) (fill (type none))
        )
      )
      (symbol \"GND_1_1\"
        (pin power_in line (at 0 0 270) (length 0) (name \"GND\" (effects (font (size 1.27 1.27)))) (number \"1\" (effects (font (size 1.27 1.27)))))
      )
    )"""
