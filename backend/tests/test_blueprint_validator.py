from app.core.blueprint_validator import validate_circuit_blueprint


def test_valid_complete_blueprint():
    bp = {
        "circuit_id": "test",
        "description": "A test circuit",
        "title": "Test Circuit",
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"],
             "parameters": {"resistance": 1000}},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["in", "0"],
             "parameters": {"dc_value": 5}},
            {"component_type": "capacitor", "name": "C1", "nodes": ["out", "0"],
             "parameters": {"capacitance": 1e-6}},
        ],
        "analyses": [{"type": "ac", "parameters": {"start_freq": 1, "stop_freq": 100000, "num_points": 100}}],
        "ground_node": "0",
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is True
    assert len(result.issues) == 0


def test_empty_blueprint():
    result = validate_circuit_blueprint({})
    assert result.is_valid is False
    assert any("empty" in i.message.lower() for i in result.issues)


def test_missing_components():
    bp = {"circuit_id": "test", "components": [], "analyses": [{"type": "op"}]}
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is False
    assert any("no components" in i.message.lower() for i in result.issues)


def test_invalid_component_type():
    bp = {
        "components": [
            {"component_type": "quantum_computer", "name": "Q1", "nodes": ["a", "b"],
             "parameters": {"qbits": 10}},
        ],
        "analyses": [{"type": "op"}],
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is False
    assert any("unknown" in i.message.lower() for i in result.issues)


def test_missing_required_params():
    bp = {
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["a", "b"], "parameters": {}},
        ],
        "analyses": [{"type": "op"}],
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is False
    assert any("missing required parameter" in i.message for i in result.issues)


def test_missing_analysis():
    bp = {
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["a", "0"],
             "parameters": {"resistance": 1000}},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["a", "0"],
             "parameters": {"dc_value": 5}},
        ],
        "analyses": [],
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is False
    assert any("no analysis" in i.message.lower() for i in result.issues)


def test_analysis_param_out_of_range():
    bp = {
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"],
             "parameters": {"resistance": 1000}},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["in", "0"],
             "parameters": {"dc_value": 5}},
        ],
        "analyses": [{"type": "ac", "parameters": {"start_freq": -1, "stop_freq": 100000, "num_points": 100}}],
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is True  # out-of-range is warning, not error
    assert any("outside recommended range" in i.message for i in result.issues)


def test_disconnected_from_ground():
    bp = {
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["A", "B"],
             "parameters": {"resistance": 1000}},
        ],
        "analyses": [{"type": "op"}],
    }
    result = validate_circuit_blueprint(bp)
    assert result.is_valid is True  # warnings, not errors


def test_wrong_prefix_warning():
    bp = {
        "components": [
            {"component_type": "resistor", "name": "X1", "nodes": ["in", "out"],
             "parameters": {"resistance": 1000}},
            {"component_type": "voltage_source", "name": "V1", "nodes": ["in", "0"],
             "parameters": {"dc_value": 5}},
        ],
        "analyses": [{"type": "op"}],
    }
    result = validate_circuit_blueprint(bp)
    assert any("should start with" in i.message for i in result.issues)
