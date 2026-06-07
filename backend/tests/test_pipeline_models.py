from app.models.pipeline_models import (
    IntentResult,
    IntentType,
    SynthesisResult,
    SimulationResult,
    SimulationDiagnostic,
    ResolverResult,
    PipelineResult,
    ClarificationResult,
    format_spice_value,
    parse_spice_value_to_float,
)


def test_intent_result_defaults():
    result = IntentResult(intent=IntentType.CREATE_CIRCUIT)
    assert result.intent == IntentType.CREATE_CIRCUIT
    assert result.is_question is False
    assert result.validation_questions == []
    assert result.confidence == 1.0


def test_intent_result_explain():
    result = IntentResult(intent=IntentType.EXPLAIN_CIRCUIT, is_question=True, confidence=0.8)
    assert result.intent == IntentType.EXPLAIN_CIRCUIT
    assert result.is_question is True
    assert result.confidence == 0.8


def test_synthesis_result():
    r = SynthesisResult(netlist=".op\n.end\n", component_count=2)
    assert r.netlist == ".op\n.end\n"
    assert r.component_count == 2
    assert r.synthesis_time_ms == 0.0
    assert r.warnings == []


def test_simulation_result_success():
    r = SimulationResult(success=True)
    assert r.success is True
    assert r.error is None
    assert r.diagnostics == []


def test_simulation_result_failure():
    r = SimulationResult(
        success=False,
        error="ngspice failed",
        diagnostics=[SimulationDiagnostic(category="error", message="ngspice failed", severity="error")],
        convergence_failures=["op: singular matrix"],
    )
    assert r.success is False
    assert r.error == "ngspice failed"
    assert len(r.diagnostics) == 1
    assert r.convergence_failures == ["op: singular matrix"]


def test_resolver_result():
    r = ResolverResult(resolved=True, patch_description="Fixed convergence", retry_count=1)
    assert r.resolved is True
    assert r.patch_description == "Fixed convergence"
    assert r.retry_count == 1


def test_resolver_result_failed():
    r = ResolverResult(
        resolved=False,
        retry_count=2,
        errors_remaining=["Max retries exceeded"],
    )
    assert r.resolved is False
    assert r.retry_count == 2
    assert r.errors_remaining == ["Max retries exceeded"]


def test_pipeline_result():
    r = PipelineResult(
        success=True,
        title="RC Filter",
        summary="An RC low-pass filter",
    )
    assert r.success is True
    assert r.title == "RC Filter"
    assert r.summary == "An RC low-pass filter"


def test_pipeline_result_with_clarifications():
    r = PipelineResult(
        success=False,
        error="Additional information required",
        clarifications=["What type of source?", "What analysis?"],
    )
    assert r.success is False
    assert len(r.clarifications) == 2


def test_clarification_result():
    r = ClarificationResult(
        needs_clarification=True,
        questions=["What source voltage?"],
    )
    assert r.needs_clarification is True
    assert r.questions == ["What source voltage?"]


def test_format_spice_value_k():
    assert format_spice_value(1000) == "1k"
    assert format_spice_value(4700) == "4.7k"
    assert format_spice_value(10000) == "10k"


def test_format_spice_value_meg():
    assert format_spice_value(1_000_000) == "1meg"
    assert format_spice_value(2_200_000) == "2.2meg"


def test_format_spice_value_u():
    assert format_spice_value(1e-6) == "1u"
    assert format_spice_value(0.000001) == "1u"
    assert format_spice_value(4.7e-6) == "4.7u"


def test_format_spice_value_n():
    assert format_spice_value(1e-9) == "1n"
    assert format_spice_value(100e-9) == "100n"


def test_format_spice_value_p():
    assert format_spice_value(1e-12) == "1p"


def test_format_spice_value_m():
    assert format_spice_value(0.001) == "1m"
    assert format_spice_value(0.01) == "10m"


def test_format_spice_value_unit():
    assert format_spice_value(1) == "1"
    assert format_spice_value(100) == "100"
    assert format_spice_value(0.5) == "0.5"


def test_format_spice_value_zero():
    assert format_spice_value(0) == "0"


def test_parse_spice_value_to_float():
    assert parse_spice_value_to_float("1k") == 1000.0
    assert parse_spice_value_to_float("1u") == 1e-6
    assert parse_spice_value_to_float("10meg") == 10_000_000.0
    assert parse_spice_value_to_float("100") == 100.0
    assert abs(parse_spice_value_to_float("4.7k") - 4700.0) < 1e-9


def test_simulation_diagnostic():
    d = SimulationDiagnostic(category="convergence", message="singular matrix", severity="error")
    assert d.category == "convergence"
    assert d.message == "singular matrix"
    assert d.severity == "error"
