# Netlist Generation Pipeline — Before vs. After

This document explains how the netlist generation pipeline in the SPICY/SPACY
platform was restructured, what each stage does, and how the new design
differs from the previous one.

The old version was a single linear "plan → validate → ask an LLM to write
Python → execute that Python → return the netlist" path. The new version is
a multi-stage pipeline that reuses the validated JSON blueprint to perform
synthesis, simulation, repair, explanation, and modification in a safe and
deterministic way.

---

## 1. High-Level Comparison

| Concern | Old (git HEAD) | New (current) |
|---|---|---|
| Pipeline shape | Single linear endpoint | Multi-stage pipeline with branching |
| Netlist synthesis | LLM writes Python → `exec()` | Deterministic renderers (no LLM, no exec) |
| Netlist source | Generated Python code string | Validated blueprint + renderers |
| Python execution | Yes — `exec(compile(...))` | **Removed** |
| Simulation | Not integrated | Full ngspice simulation stage |
| Simulation repair | None | LLM-based resolver with retry loop |
| Intent handling | Always "create" | Routes to CREATE / MODIFY / EXPLAIN |
| Clarification | None | Heuristic + LLM clarification engine |
| Blueprint normalization | Done inside `Planner._apply_safety_fixes` | Dedicated `BlueprintNormalizer` |
| Blueprint validation | Yes | Yes + new floating-node / disconnected-subgraph checks |
| Modification | Not supported | `ModifyService` re-plans the blueprint |
| Explanation | Not supported | `ExplainService` (LLM with deterministic fallback) |
| Session state | None | `CircuitSession` DB model with full history |
| Typed result objects | Plain dicts | `PipelineResult`, `SimulationResult`, `ResolverResult`, etc. |
| Number of files | 1 monolithic synthesizer | 11 focused service files |

---

## 2. Architecture Diagram

### Old flow

```
User prompt
   │
   ▼
Planner.create_plan()        ──► JSON blueprint (with safety fixes)
   │
   ▼
validate_circuit_blueprint() ──► validated_blueprint dict
   │
   ▼
SpecialistSynthesizer
   ├── generate_python_code (LLM)
   ├── CodeValidator (AST scan)
   ├── RepairEngine (LLM repair)
   └── RestrictedExecutor (exec the Python) ──► netlist string
   │
   ▼
Return: netlist + python_code
```

### New flow

```
User prompt
   │
   ▼
IntentClassifier ──► CREATE | MODIFY | EXPLAIN
   │
   ├── EXPLAIN ──► ExplainService.explain(blueprint, netlist)
   │
   ├── MODIFY  ──► ModifyService.modify(existing_blueprint, prompt)
   │                 │
   │                 ▼
   │              validate → normalize → DeterministicSynthesizer
   │
   └── CREATE  ──► ClarificationEngine.analyze(prompt)
                     │  (asks questions if info missing)
                     ▼
                  Planner.create_plan_strict(prompt)
                     │
                     ▼
                  validate_circuit_blueprint()
                     │
                     ▼
                  BlueprintNormalizer.normalize()
                     │
                     ▼
                  DeterministicSynthesizer.synthesize()  ──► netlist
                     │
                     ▼
                  SimulationStage.run(netlist)  ──► SimulationResult
                     │  (ngspice via run_ngspice_once)
                     ▼
                  SimulationResolver.resolve()  (if sim failed, retry)
                     │
                     ▼
                  PipelineResult  (success / clarifications / error)
```

---

## 3. What the New Pipeline Adds

### 3.1 Intent classification

`backend/app/services/intent_classifier.py`

Before any work starts, the prompt is classified into one of three intents:

- `CREATE_CIRCUIT` — the user wants a new circuit.
- `MODIFY_CIRCUIT` — the user wants to change an existing one.
- `EXPLAIN_CIRCUIT` — the user is asking a question.

The classifier is rule-based (regex patterns on create / modify / explain
verbs and question words) and falls back to an LLM call only when the rules
are unsure. The old pipeline always assumed CREATE.

### 3.2 Clarification engine

`backend/app/services/clarification_engine.py`

If the prompt is missing a source, ground reference, component values, or
an analysis type, the pipeline returns a list of questions to the caller
instead of guessing. There is also an LLM-based path
(`llm_clarify`) that uses a partial blueprint as additional context.

### 3.3 Planner with strict mode

`backend/app/services/circuit_planner.py`

The planner now exposes two entry points:

- `create_plan(description)` — applies safety fixes (defaults for missing
  parameters).
- `create_plan_strict(description)` — returns the raw LLM output without
  silent patching. The pipeline uses strict mode so that validation
  catches every missing field.

The new code only added `create_plan_strict`; the rest of the planner
remains as before.

### 3.4 Blueprint validation improvements

`backend/app/core/blueprint_validator.py`

Two new checks were added to `NodeValidator`:

- **Floating nodes** — a node that connects to only one component.
- **Disconnected subgraphs** — a component that has no path to the
  ground node.

Both are reported as warnings, not errors, so the pipeline can still
proceed while flagging the issue.

### 3.5 Blueprint normalizer

`backend/app/services/blueprint_normalizer.py`

A dedicated normalization step applies defaults for components
(`dc_value`, `resistance`, `capacitance`, `w`, `l`, …) and analyses
(start/stop/step ranges). It also assigns default models
(`NMOS`, `NPN`, `DEFAULT`) for active devices and ensures
`ground_node`, `input_nodes`, `output_nodes` are present.

This logic used to live inside `Planner._apply_safety_fixes`; the new
pipeline runs the normalizer *after* validation, so validation operates
on the raw LLM output and can report the real cause of a failure.

### 3.6 Deterministic synthesis (the key change)

`backend/app/services/deterministic_synthesizer.py` +
`backend/app/services/renderers/`

This replaces the entire LLM-Python-exec chain.

- A `CircuitBuilder` is instantiated once.
- For each component in the blueprint, a renderer is looked up in
  `_RENDERER_MAP` and called:

  | Component | Renderer |
  |---|---|
  | resistor, capacitor, inductor | `ResistorRenderer` / `CapacitorRenderer` / `InductorRenderer` |
  | voltage_source, current_source, diode | `SourceRenderer` |
  | mosfet, bjt | `TransistorRenderer` |
  | opamp | `OpAmpRenderer` |
  | analyses (.ac, .tran, .dc, .op) | `AnalysisRenderer` |

- Values are converted with `format_spice_value` (1k, 1u, 1n, …) before
  being passed to the builder.
- The output is a SPICE netlist string, with no LLM involvement and no
  `exec()` call.

### 3.7 Simulation stage

`backend/app/services/simulation_stage.py`

If `run_simulation=True` (the default for the API), the netlist is run
through ngspice:

- Validates the netlist is non-empty and ngspice is on `PATH`.
- Uses `detect_analyses` and `extract_analysis_lines` from
  `app/core/netlist_pipeline.py` to find analysis directives.
- Calls `run_ngspice_once` per analysis and parses results via
  `app/core/raw_parser.py`.
- Returns a `SimulationResult` with `success`, analyses run, raw
  results, stdout, stderr, diagnostics, and convergence failures.

The old pipeline never ran a simulation.

### 3.8 Simulation resolver

`backend/app/services/simulation_resolver.py`

If the simulation fails, the resolver asks the LLM to produce a minimal
patch — either a patched blueprint or a patched netlist — and the
pipeline re-validates, re-normalizes, re-synthesizes, and re-simulates.
The loop runs up to `max_resolver_retries` (default 2).

### 3.9 Explain service

`backend/app/services/explain_service.py`

Used when the intent is `EXPLAIN_CIRCUIT`. With an LLM available it
produces a 2–5 paragraph natural-language explanation. With no LLM it
falls back to a deterministic description of the blueprint.

### 3.10 Modify service

`backend/app/services/modify_service.py`

Used when the intent is `MODIFY_CIRCUIT`. Takes the current blueprint
and a modification request, asks the LLM to produce an updated
blueprint (preserving everything not explicitly changed), and runs it
through validate → normalize → synthesize.

### 3.11 Pipeline orchestrator

`backend/app/services/netlist_generation_pipeline.py`

`NetlistGenerationPipeline.run()` is the single entry point. It:

1. Classifies intent.
2. Routes to `_handle_explain`, `_handle_modify`, or `_handle_create`.
3. Returns a fully typed `PipelineResult` with optional
   `intent`, `blueprint`, `validation`, `synthesis`, `simulation`,
   `resolution`, `title`, `summary`, `clarifications`, and `error`.

### 3.12 Typed data models

`backend/app/models/pipeline_models.py`

New dataclasses replace ad-hoc dicts:

- `IntentType` enum + `IntentResult`
- `SynthesisResult` (netlist, time, component count, warnings)
- `SimulationDiagnostic` + `SimulationResult` (analyses, results, stdout,
  stderr, diagnostics, convergence failures)
- `ResolverResult` (patched blueprint / netlist, description, errors)
- `PipelineResult` (the full bundle returned to the caller)
- `ClarificationResult`
- `SessionState`
- `format_spice_value` / `parse_spice_value_to_float` helpers used by
  the renderers

### 3.13 Session model

`backend/app/models/session.py`

A new `CircuitSession` table stores the latest blueprint, latest
netlist, simulation history, retry history, and conversation history
per session id (and optionally per user).

### 3.14 New API surface

`backend/app/api/routes/netlist_gen.py`

The endpoint contract is now:

```
POST /generate-netlist
{
  "prompt": "...",
  "api_key": "...",
  "api_base": "...",
  "model": "...",
  "run_simulation": true
}

→ {
  "success": bool,
  "title": "...",
  "netlist": "...",
  "summary": "...",
  "blueprint": {...},
  "simulation": { "success": bool, "analyses": [...], "results": [...], ... } | null,
  "clarifications": ["..."] | [],
  "error": "..." | null
}
```

The `python_code` field is gone — the new pipeline does not produce
Python.

---

## 4. File-by-File Diff Summary

### Files removed

| File | Why |
|---|---|
| `backend/app/services/netlist_synthesizer.py` | Replaced by the deterministic synthesizer + renderers. The whole LLM-Python-`exec` chain was removed. |

### Files modified

| File | Change |
|---|---|
| `backend/app/api/routes/netlist_gen.py` | Calls the new `NetlistGenerationPipeline`; response includes `blueprint`, `simulation`, and `clarifications`; no more `python_code`. |
| `backend/app/core/blueprint_validator.py` | Adds floating-node and disconnected-subgraph checks. |
| `backend/app/services/circuit_planner.py` | Adds `create_plan_strict()` for the pipeline; keeps the legacy `create_plan()` path. |

### Files added

| File | Purpose |
|---|---|
| `backend/app/models/pipeline_models.py` | Typed dataclasses for the entire pipeline. |
| `backend/app/models/session.py` | DB model for `CircuitSession`. |
| `backend/app/services/blueprint_normalizer.py` | Fills in defaults for components and analyses. |
| `backend/app/services/clarification_engine.py` | Detects missing info and asks the user. |
| `backend/app/services/deterministic_synthesizer.py` | Renders a validated blueprint to a SPICE netlist. |
| `backend/app/services/explain_service.py` | Plain-English explanation of a circuit. |
| `backend/app/services/intent_classifier.py` | Routes the prompt to CREATE / MODIFY / EXPLAIN. |
| `backend/app/services/modify_service.py` | Re-plans an existing blueprint based on a user change request. |
| `backend/app/services/netlist_generation_pipeline.py` | Orchestrator that wires all stages together. |
| `backend/app/services/simulation_resolver.py` | LLM-based retry loop on simulation failure. |
| `backend/app/services/simulation_stage.py` | Runs ngspice and parses raw output. |
| `backend/app/services/renderers/__init__.py` | Renderer package. |
| `backend/app/services/renderers/resistor_renderer.py` | R/C/L passive components. |
| `backend/app/services/renderers/source_renderer.py` | V/I sources and diodes. |
| `backend/app/services/renderers/transistor_renderer.py` | MOSFETs and BJTs. |
| `backend/app/services/renderers/opamp_renderer.py` | Op-amps. |
| `backend/app/services/renderers/analysis_renderer.py` | `.ac`, `.tran`, `.dc`, `.op` directives. |

---

## 5. The Single Most Important Change

The previous implementation **generated Python code via an LLM and
executed it with `exec()`** to produce the netlist. That meant every
circuit build had to:

1. Call an LLM to write Python.
2. Parse the Python with an AST-based `CodeValidator` (forbidden imports,
   forbidden attributes, required `CircuitBuilder` calls, required
   `netlist = ...` assignment).
3. Optionally call the LLM again in a `RepairEngine` to fix the code.
4. Run the code in a `RestrictedExecutor` with restricted builtins and
   a hard-coded `_ALLOWED_BUILTINS` allowlist.
5. Extract the `netlist` string from the executed namespace.

The new implementation **never generates or executes Python at all**.
The LLM only produces JSON, the JSON is validated and normalized, and
deterministic Python renderers turn it into a netlist. The LLM is now
used only for things that actually require language understanding:

- Producing the blueprint (Planner).
- Routing the user's intent (IntentClassifier fallback).
- Asking clarifying questions (ClarificationEngine).
- Explaining a circuit (ExplainService).
- Modifying a circuit (ModifyService).
- Repairing a failed simulation (SimulationResolver).

The build path is now safe, reproducible, and does not depend on
runtime code execution.
