from app.models.pipeline_models import (
    IntentType,
    PipelineResult,
    ResolverResult,
    SimulationDiagnostic,
    SimulationResult,
    SynthesisResult,
)
from app.services.netlist_generation_pipeline import NetlistGenerationPipeline


def test_pipeline_creation():
    pipeline = NetlistGenerationPipeline()
    assert pipeline is not None
    assert pipeline._intent_classifier is not None
    assert pipeline._synthesizer is not None
    assert pipeline._resolver is not None


def test_pipeline_handle_create_missing_info():
    pipeline = NetlistGenerationPipeline()
    from app.models.pipeline_models import IntentResult
    intent = IntentResult(intent=IntentType.CREATE_CIRCUIT)
    result = pipeline._handle_create(
        prompt="filter",
        intent=intent,
        run_simulation=False,
        enable_resolver=False,
        max_resolver_retries=2,
        simulation_timeout=30,
    )
    assert isinstance(result, PipelineResult)
    assert result.clarifications is not None


def test_pipeline_routes_explain():
    pipeline = NetlistGenerationPipeline()
    from app.models.pipeline_models import IntentResult
    intent = IntentResult(intent=IntentType.EXPLAIN_CIRCUIT, is_question=True)
    result = pipeline._handle_explain("What is an RC filter?", intent, None)
    assert result.intent.intent == IntentType.EXPLAIN_CIRCUIT


def test_pipeline_routes_modify_no_blueprint():
    pipeline = NetlistGenerationPipeline()
    from app.models.pipeline_models import IntentResult
    intent = IntentResult(intent=IntentType.MODIFY_CIRCUIT)
    result = pipeline._handle_modify("Change R1 to 10k", intent, None)
    assert result.success is False
    assert "no existing blueprint" in result.error.lower()


def test_pipeline_routes_modify_with_blueprint():
    pipeline = NetlistGenerationPipeline()
    from app.models.pipeline_models import IntentResult
    intent = IntentResult(intent=IntentType.MODIFY_CIRCUIT)
    existing = {
        "title": "Test",
        "components": [
            {"component_type": "resistor", "name": "R1", "nodes": ["in", "out"],
             "parameters": {"resistance": 1000}},
        ],
        "analyses": [{"type": "op"}],
    }
    result = pipeline._handle_modify("Change R1 to 10k", intent, existing)
    assert result is not None


def test_resolver_no_llm():
    from app.services.simulation_resolver import SimulationResolver
    resolver = SimulationResolver(llm_client=None)
    sim_result = SimulationResult(
        success=False,
        error="ngspice failed",
        diagnostics=[SimulationDiagnostic("error", "ngspice failed", "error")],
    )
    result = resolver.resolve(
        blueprint={"components": []},
        simulation_result=sim_result,
        previous_netlist="",
        retry_count=0,
    )
    assert result.resolved is False
    assert result.errors_remaining == ["No LLM available for resolver"]


def test_resolver_max_retries():
    from app.services.simulation_resolver import SimulationResolver
    resolver = SimulationResolver(llm_client=None)
    sim_result = SimulationResult(success=False, error="failed")
    result = resolver.resolve(
        blueprint={"components": []},
        simulation_result=sim_result,
        retry_count=2,
    )
    assert result.resolved is False
    assert "Max retries exceeded" in result.errors_remaining


def test_resolver_success_no_action():
    from app.services.simulation_resolver import SimulationResolver
    resolver = SimulationResolver(llm_client=None)
    sim_result = SimulationResult(success=True)
    result = resolver.resolve(
        blueprint={"components": []},
        simulation_result=sim_result,
    )
    assert result.resolved is True
    assert result.retry_count == 0


def test_pipeline_result_serializable():
    result = PipelineResult(
        success=True,
        title="Test Circuit",
        summary="A test",
        synthesis=SynthesisResult(netlist=".op\n.end\n"),
        simulation=SimulationResult(success=True),
    )
    assert result.success is True
    assert result.title == "Test Circuit"
    assert result.synthesis.netlist == ".op\n.end\n"
    assert result.simulation.success is True


def test_pipeline_result_with_resolution():
    result = PipelineResult(
        success=True,
        resolution=ResolverResult(
            resolved=True,
            patch_description="Fixed convergence by reducing tstep",
            retry_count=1,
        ),
    )
    assert result.success is True
    assert result.resolution.resolved is True
    assert result.resolution.retry_count == 1
