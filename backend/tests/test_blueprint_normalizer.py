from app.services.blueprint_normalizer import normalize_blueprint


def test_normalize_empty_blueprint():
    bp = normalize_blueprint({})
    assert bp["ground_node"] == "0"
    assert bp["components"] == []
    assert bp["analyses"] == []


def test_normalize_component_defaults():
    bp = normalize_blueprint({
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"], "parameters": {}},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["in", "0"], "parameters": {}},
        ],
    })
    assert bp["components"][0]["parameters"]["resistance"] == 1000
    assert bp["components"][1]["parameters"]["dc_value"] == 5


def test_normalize_preserves_explicit_values():
    bp = normalize_blueprint({
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"],
             "parameters": {"resistance": 4700}},
        ],
    })
    assert bp["components"][0]["parameters"]["resistance"] == 4700


def test_normalize_analysis_defaults_ac():
    bp = normalize_blueprint({
        "components": [],
        "analyses": [{"type": "ac", "parameters": {}}],
    })
    a = bp["analyses"][0]
    assert a["type"] == "ac"
    assert a["parameters"]["start_freq"] == 1
    assert a["parameters"]["stop_freq"] == 1_000_000
    assert a["parameters"]["num_points"] == 100


def test_normalize_analysis_defaults_op():
    bp = normalize_blueprint({
        "components": [],
        "analyses": [{"type": "op", "parameters": {}}],
    })
    a = bp["analyses"][0]
    assert a["type"] == "op"
    assert a["parameters"] == {}


def test_normalize_analysis_preserves_explicit():
    bp = normalize_blueprint({
        "components": [],
        "analyses": [{"type": "transient", "parameters": {"tstop": 0.1, "tstep": 1e-6, "tstart": 0}}],
    })
    a = bp["analyses"][0]
    assert a["parameters"]["tstop"] == 0.1
    assert a["parameters"]["tstep"] == 1e-6


def test_normalize_mosfet_defaults():
    bp = normalize_blueprint({
        "components": [
            {"component_type": "mosfet", "name": "M1", "nodes": ["d", "g", "s", "b"], "parameters": {}},
        ],
    })
    c = bp["components"][0]
    assert c["parameters"]["w"] == 10e-6
    assert c["parameters"]["l"] == 1e-6
    assert c.get("model") == "NMOS"


def test_normalize_lowercases_types():
    bp = normalize_blueprint({
        "components": [
            {"component_type": "RESISTOR", "name": "R1", "nodes": ["in", "out"], "parameters": {}},
        ],
    })
    assert bp["components"][0]["component_type"] == "resistor"


def test_normalize_input_output_nodes():
    bp = normalize_blueprint({
        "components": [],
        "input_nodes": ["Vin"],
        "output_nodes": ["Vout"],
    })
    assert bp["input_nodes"] == ["Vin"]
    assert bp["output_nodes"] == ["Vout"]


def test_normalize_preserves_model():
    bp = normalize_blueprint({
        "components": [
            {"component_type": "bjt", "name": "Q1", "nodes": ["c", "b", "e"],
             "parameters": {}, "model": "BC547"},
        ],
    })
    assert bp["components"][0]["model"] == "BC547"


def test_normalize_ground_default():
    bp = normalize_blueprint({"components": []})
    assert bp["ground_node"] == "0"
