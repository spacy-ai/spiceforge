from app.core.netlist_builder import CircuitBuilder
from app.models.pipeline_models import format_spice_value
from app.services.deterministic_synthesizer import DeterministicSynthesizer
from app.services.renderers import (
    ResistorRenderer,
    CapacitorRenderer,
    InductorRenderer,
    SourceRenderer,
    TransistorRenderer,
    AnalysisRenderer,
)
from app.services.renderers.opamp_renderer import OpAmpRenderer


def test_resistor_renderer():
    builder = CircuitBuilder()
    ResistorRenderer.render(builder, {
        "name": "R1", "nodes": ["in", "out"], "parameters": {"resistance": 1000}
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "R1 in out 1k" in netlist


def test_capacitor_renderer():
    builder = CircuitBuilder()
    CapacitorRenderer.render(builder, {
        "name": "C1", "nodes": ["out", "0"], "parameters": {"capacitance": 1e-6}
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "C1 out 0 1u" in netlist


def test_inductor_renderer():
    builder = CircuitBuilder()
    InductorRenderer.render(builder, {
        "name": "L1", "nodes": ["in", "out"], "parameters": {"inductance": 10e-3}
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "L1 in out 10m" in netlist


def test_voltage_source_renderer():
    builder = CircuitBuilder()
    SourceRenderer.render(builder, {
        "component_type": "voltage_source",
        "name": "V1", "nodes": ["in", "0"], "parameters": {"dc_value": 5},
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "V1 in 0 DC 5.0" in netlist


def test_current_source_renderer():
    builder = CircuitBuilder()
    SourceRenderer.render(builder, {
        "component_type": "current_source",
        "name": "I1", "nodes": ["in", "0"], "parameters": {"dc_value": 0.001},
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "I1 in 0 DC 0.001" in netlist


def test_diode_renderer():
    builder = CircuitBuilder()
    SourceRenderer.render_diode(builder, {
        "name": "D1", "nodes": ["anode", "cathode"], "model": "1N4148",
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "D1 anode cathode 1N4148" in netlist


def test_mosfet_renderer():
    builder = CircuitBuilder()
    TransistorRenderer.render_mosfet(builder, {
        "name": "M1",
        "nodes": ["d", "g", "s", "b"],
        "parameters": {"w": 10e-6, "l": 1e-6},
        "model": "NMOS",
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "M1 d g s b NMOS" in netlist
    assert "W=1e-05" in netlist
    assert "L=1e-06" in netlist


def test_bjt_renderer():
    builder = CircuitBuilder()
    TransistorRenderer.render_bjt(builder, {
        "name": "Q1", "nodes": ["c", "b", "e"], "parameters": {}, "model": "NPN",
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "Q1 c b e NPN" in netlist


def test_opamp_renderer():
    builder = CircuitBuilder()
    OpAmpRenderer.render(builder, {
        "name": "U1", "nodes": ["Vout", "ninv", "nnoninv"], "model": "OP07",
    })
    builder.operating_point()
    netlist = builder.netlist()
    assert "U1 Vout ninv nnoninv 0 0 OP07" in netlist


def test_ac_analysis_renderer():
    builder = CircuitBuilder()
    builder.resistor("1", "in", "out", "1k")
    AnalysisRenderer.render(builder, {
        "type": "ac", "parameters": {"start_freq": 1, "stop_freq": 1e6, "num_points": 100}
    })
    netlist = builder.netlist()
    assert ".ac dec 100 1.0 1000000.0" in netlist


def test_transient_analysis_renderer():
    builder = CircuitBuilder()
    builder.resistor("1", "in", "out", "1k")
    AnalysisRenderer.render(builder, {
        "type": "transient", "parameters": {"tstart": 0, "tstop": 0.01, "tstep": 1e-5}
    })
    netlist = builder.netlist()
    assert ".tran 1e-05 0.01 0.0" in netlist


def test_op_analysis_renderer():
    builder = CircuitBuilder()
    builder.resistor("1", "in", "out", "1k")
    AnalysisRenderer.render(builder, {"type": "op", "parameters": {}})
    netlist = builder.netlist()
    assert ".op" in netlist


def test_dc_sweep_renderer():
    builder = CircuitBuilder()
    builder.resistor("1", "in", "out", "1k")
    AnalysisRenderer.render(builder, {
        "type": "dc_sweep",
        "parameters": {"sweep_variable": "V1", "start": 0, "stop": 5, "step": 0.1},
    })
    netlist = builder.netlist()
    assert ".dc V1 0.0 5.0 0.1" in netlist


def test_deterministic_synthesizer_full():
    synth = DeterministicSynthesizer()
    blueprint = {
        "title": "RC Low Pass Filter",
        "description": "Test circuit",
        "components": [
            {"component_type": "voltage_source", "name": "V1", "nodes": ["Vin", "0"],
             "parameters": {"dc_value": 5}, "model": None},
            {"component_type": "resistor", "name": "R1", "nodes": ["Vin", "Vout"],
             "parameters": {"resistance": 1000}, "model": None},
            {"component_type": "capacitor", "name": "C1", "nodes": ["Vout", "0"],
             "parameters": {"capacitance": 1e-6}, "model": None},
        ],
        "analyses": [
            {"type": "ac", "parameters": {"start_freq": 1, "stop_freq": 100000, "num_points": 50}}
        ],
    }
    result = synth.synthesize(blueprint)
    assert result.netlist is not None
    assert result.component_count == 3
    assert "R1" in result.netlist
    assert "C1" in result.netlist
    assert "V1" in result.netlist
    assert ".ac" in result.netlist
    assert result.synthesis_time_ms >= 0


def test_deterministic_synthesizer_stable_output():
    synth = DeterministicSynthesizer()
    blueprint = {
        "title": "Test",
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"],
             "parameters": {"resistance": 1000}, "model": None},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["in", "0"],
             "parameters": {"dc_value": 5}, "model": None},
        ],
        "analyses": [{"type": "op", "parameters": {}}],
    }
    r1 = synth.synthesize(blueprint)
    r2 = synth.synthesize(blueprint)
    assert r1.netlist == r2.netlist


def test_deterministic_synthesizer_empty_components():
    synth = DeterministicSynthesizer()
    blueprint = {"title": "Empty", "components": [], "analyses": [{"type": "op"}]}
    result = synth.synthesize(blueprint)
    assert result.component_count == 0
    assert ".op" in result.netlist


def test_format_spice_value_consistency():
    test_values = [1, 10, 100, 1000, 4700, 10000, 1e6, 2.2e6, 1e-3, 1e-6, 4.7e-6, 1e-9, 1e-12, 0.5, 0]
    for v in test_values:
        formatted = format_spice_value(v)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
