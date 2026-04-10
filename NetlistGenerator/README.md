# SPACY - SPICE Circuit Agent with Y

Core Reasoning Agent (Planner) - Task 1

## Overview

The Planner is the central reasoning engine in the SPACY multi-agent pipeline.
It converts natural language circuit descriptions into structured circuit blueprints
that are validated by the Validator before being synthesized into Python code.

## Components

- `planner.py` - Core Planner class with state management and blueprint generation
- `llm_client.py` - LLM client interface for OpenCode endpoint integration  
- `server.py` - FastAPI server exposing Planner endpoints
- `__init__.py` - Module exports

## Architecture

```
User Description → Planner → Circuit Blueprint → Validator → Specialist → Python Builder
                                    ↑                                              |
                                    └────────── Repair Feedback ──────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plan` | POST | Create circuit plan from description |
| `/plan/{circuit_id}/repair` | POST | Update plan based on simulator feedback |
| `/plan/{circuit_id}` | GET | Retrieve specific plan |
| `/history` | GET | Get history of all plans |
| `/reset` | POST | Reset planner state |
| `/store-netlist` | POST | Store netlist for reference |

## Usage

```python
from spacy.planner import Planner, CircuitBlueprint

# Initialize planner
planner = Planner()

# Create circuit plan
description = "Design a two-stage CMOS amplifier"
blueprint = planner.create_plan(description)

# Get blueprint details
print(f"Circuit ID: {blueprint.circuit_id}")
print(f"Components: {len(blueprint.components)}")
print(f"Analyses: {blueprint.analyses}")

# Update with repair feedback
feedback = {"error_type": "convergence", "message": "DC solution failed"}
updated = planner.update_plan(blueprint, feedback)
```

## Running the Server

```bash
python -m spacy.planner.server
```

Server runs on `http://localhost:8000` with API docs at `/docs`.

## Integration Notes

- LLM calls use OpenCode endpoints (2-4 API calls per request)
- Planner maintains state for repair loop integration
- Output feeds directly into Validator module
- Compatible with LTspice netlist format