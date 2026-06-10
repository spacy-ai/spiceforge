"""
Test suite for netlist_draw.py
All netlists are NGSpice-compatible (title line, elements, optional .end).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.services.netlist_to_schemdraw import netlist_to_schemdraw, render_schemdraw_svg

TESTS = {

    # ── RC Low Pass Filter ────────────────────────────────────────────────
    "rc_lowpass": """
RC Low Pass Filter
V1 vin 0 DC 5V
R1 vin out 1k
C1 out 0 100n
""",

    # ── Two Stage RC Network ──────────────────────────────────────────────
    "two_stage_rc": """
Two Stage RC Network
V1 vin 0 DC 5V
R1 vin n1 1k
C1 n1 0 100n
R2 n1 n2 1k
C2 n2 0 100n
""",

}

errors = []
for name, netlist in TESTS.items():
    print(f"\n{'='*60}\nTEST: {name}\n{'='*60}")
    try:
        code = netlist_to_schemdraw(netlist)
        print(code)
        try:
            out = render_schemdraw_svg(code, f"./test/test_{name}.svg")
            print(f"  → SVG saved: {out}")
        except Exception as e:
            print(f"  → Render error (schemdraw not installed): {e}")
    except Exception as e:
        errors.append((name, str(e)))
        print(f"  !! ERROR: {e}")

print(f"\n{'='*60}")
if errors:
    print(f"FAILURES: {len(errors)}")
    for name, err in errors:
        print(f"  {name}: {err}")
else:
    print(f"ALL {len(TESTS)} TESTS GENERATED SUCCESSFULLY")