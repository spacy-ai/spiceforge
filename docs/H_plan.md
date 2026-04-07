GOAL: PROMPT - NETLIST EXPORT - REPAIR LOOP
TASK 1 — Core Architecture Blueprint
Produce a working architecture file describing the 3-layer agent system (Planner, Validator, Specialist) plus the Simulator Backend and Memory. This must include module boundaries, function signatures, and data flow.

TASK 2 — Planner (Reasoning Engine) Skeleton
Implement the initial Planner module with functions for: prompt parsing, goal creation, and task routing. No full reasoning yet; focus on scaffolding and internal data structures.

TASK 3 — Validator Engine (Syntax + Structure Checker)
Develop the validator that can: fix component names, detect missing nodes, detect missing .end, enforce consistent grounding, and return corrected intermediate representations. This should run independently.

TASK 4 — Specialist SLM Integration
Integrate a pre-trained small LLM/SLM for SPICE syntax generation. Build the interface wrapper so you can send component-level data and receive structured netlists

TASK 5 — Simulation Backend (+ Error Extraction)
Set up ngspice execution from Python and parse: stdout errors, .raw results, and node values. The output should be structured so the Planner can use it for reasoning-repair.

TASK 6 — End-to-End Mini Pipeline Prototype
Connect Planner → Specialist → Validator → Simulator. Target: generate and simulate a simple RC low-pass filter netlist successfully. This is your minimal working demonstration.
