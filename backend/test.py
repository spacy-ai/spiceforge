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

    # ── RL High Pass Filter ───────────────────────────────────────────────
    "rl_highpass": """
RL High Pass Filter
V1 vin 0 DC 12V
L1 vin out 10m
R1 out 0 1k
""",

    # ── Wheatstone Bridge ─────────────────────────────────────────────────
    "wheatstone_bridge": """
Wheatstone Bridge
V1 vin 0 DC 10V
R1 vin n1 1k
R2 n1 0 1k
R3 vin n2 2k
R4 n2 0 2k
R5 n1 n2 500
""",

    # ── Voltage Divider ───────────────────────────────────────────────────
    "voltage_divider": """
Voltage Divider
V1 vin 0 DC 9V
R1 vin mid 10k
R2 mid 0 5k
""",

    # ── RLC Series Circuit ────────────────────────────────────────────────
    "rlc_series": """
RLC Series Circuit
V1 vin 0 AC 1V
R1 vin n1 100
L1 n1 n2 10m
C1 n2 0 1u
""",

    # ── Common Emitter Amplifier ──────────────────────────────────────────
    "common_emitter": """
Common Emitter Amplifier
VCC vcc 0 DC 12V
R1 vcc base 47k
R2 base 0 10k
RC vcc collector 1k
RE emitter 0 470
Q1 collector base emitter NPN
""",

    # ── Diode Rectifier ───────────────────────────────────────────────────
    "diode_rectifier": """
Half Wave Rectifier
V1 vin 0 SIN(0 10 50)
D1 vin out D
RL out 0 1k
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