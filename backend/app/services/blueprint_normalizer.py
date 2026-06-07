from __future__ import annotations


class BlueprintNormalizer:
    ANALYSIS_DEFAULTS = {
        "ac": {"start_freq": 1, "stop_freq": 1e6, "num_points": 100},
        "transient": {"tstart": 0, "tstop": 1e-3, "tstep": 1e-6},
        "dc": {"source": "V1", "start": 0, "stop": 5, "step": 0.1},
        "dc_sweep": {"sweep_variable": "V1", "start": 0, "stop": 5, "step": 0.1},
        "op": {},
    }

    COMPONENT_DEFAULTS = {
        "voltage_source": {"dc_value": 5},
        "current_source": {"dc_value": 0.001},
        "resistor": {"resistance": 1000},
        "capacitor": {"capacitance": 1e-6},
        "inductor": {"inductance": 1e-3},
        "mosfet": {"w": 10e-6, "l": 1e-6},
        "bjt": {},
        "opamp": {},
        "diode": {},
    }

    @classmethod
    def normalize(cls, blueprint: dict) -> dict:
        result = dict(blueprint)

        components = list(result.get("components", []))
        result["components"] = [cls._normalize_component(c) for c in components]

        analyses = list(result.get("analyses", []))
        result["analyses"] = [cls._normalize_analysis(a) for a in analyses]

        result.setdefault("ground_node", "0")
        result.setdefault("input_nodes", [])
        result.setdefault("output_nodes", [])

        return result

    @classmethod
    def _normalize_component(cls, comp: dict) -> dict:
        comp = dict(comp)
        comp_type = comp.get("component_type", "").lower()
        comp["component_type"] = comp_type

        params = dict(comp.get("parameters", {}))
        defaults = cls.COMPONENT_DEFAULTS.get(comp_type, {})
        for key, val in defaults.items():
            params.setdefault(key, val)

        if comp_type == "mosfet" and "model" not in comp and "model" not in params:
            comp["model"] = "NMOS"
        if comp_type == "bjt" and "model" not in comp and "model" not in params:
            comp["model"] = "NPN"
        if comp_type == "diode" and "model" not in comp and "model" not in params:
            comp["model"] = "DEFAULT"

        comp["parameters"] = params
        return comp

    @classmethod
    def _normalize_analysis(cls, analysis: dict) -> dict:
        analysis = dict(analysis)
        atype = analysis.get("type", "").lower()
        analysis["type"] = atype

        params = dict(analysis.get("parameters", {}))
        defaults = cls.ANALYSIS_DEFAULTS.get(atype, {})
        for key, val in defaults.items():
            params.setdefault(key, val)

        analysis["parameters"] = params
        return analysis


def normalize_blueprint(blueprint: dict) -> dict:
    return BlueprintNormalizer.normalize(blueprint)
