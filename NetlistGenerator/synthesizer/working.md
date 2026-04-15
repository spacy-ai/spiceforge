# SPACY Synthesizer Module Documentation

## Overview

The **Synthesizer module** is responsible for converting a validated circuit blueprint into a **fully executable SPICE netlist**.

It implements a **multi-stage, safety-aware synthesis pipeline** combining:

* LLM-based code generation (flexible reasoning)
* Static validation (AST-based safety checks)
* Incremental repair (targeted corrections)
* Sandboxed execution (controlled runtime)
* Deterministic netlist construction (via `CircuitBuilder`)

---

## Architecture

```text
Blueprint (Planner)
        ↓
LLM Code Generation (SpecialistSynthesizer)
        ↓
AST Validation (CodeValidator)
        ↓
Repair Loop (RepairEngine, if needed)
        ↓
Sandbox Execution (RestrictedExecutor)
        ↓
CircuitBuilder (builder.py)
        ↓
SPICE Netlist (Final Output)
```

---

## File Responsibilities

### 1. `synthesizer.py`

This file implements the **intelligent synthesis pipeline**.

#### Responsibilities:

* Interacts with LLM (via OpenCode)
* Generates Python code from blueprint
* Validates generated code (AST-based)
* Repairs invalid code incrementally
* Executes code in restricted environment
* Returns final netlist + metadata

---

### 2. `builder.py`

This file provides the **deterministic backend engine**.

#### Responsibilities:

* Converts method calls → SPICE syntax
* Maintains internal lists:

  * components
  * models
  * analyses
* Produces final `.net` string via `netlist()`

#### Example:

```python
builder.resistor("R1", "in", "out", "10k")
```

→ Generates:

```
R1 in out 10k
```

---

## Core Pipeline (Detailed Flow)

---

### Step 1 — Input: Circuit Blueprint

Input comes from the Planner:

```python
blueprint: dict
```

This is:

* structured
* LLM-generated
* already validated at planning level

---

### Step 2 — Code Generation (LLM)

```python
python_code = generate_python_code(blueprint)
```

The LLM:

* Receives blueprint as structured input
* Outputs **Python code using CircuitBuilder API**

#### Example output:

```python
builder = CircuitBuilder()
builder.resistor("R1", "in", "out", "10k")
builder.capacitor("C1", "out", "0", "1u")
netlist = builder.netlist()
```

#### Key Design Constraint:

* LLM does **NOT generate SPICE directly**
* It generates structured Python → reduces syntax errors

---

### Step 3 — Code Validation (AST)

```python
errors = CodeValidator.validate(python_code)
```

#### Validation includes:

1. **Syntax Check**

   * Uses `ast.parse()`

2. **Forbidden Constructs**

   * Blocks:

     * `import`, `from ... import`
     * `eval`, `exec`, `open`, `system`
     * dangerous attributes (`__builtins__`, etc.)

3. **Required API Usage**

   * Must include:

     * `CircuitBuilder()`
     * `.netlist()`

4. **Netlist Assignment**

   * Must assign:

     ```python
     netlist = ...
     ```

---

### Step 4 — Repair Engine (If Validation Fails)

```python
python_code, errors = RepairEngine.repair(...)
```

#### Strategy:

* Does NOT regenerate full code
* Applies **targeted fixes**

#### Process:

1. Classify errors:

   * `ast`
   * `api`
   * `missing_netlist`
   * `runtime`

2. Build repair prompt:

   * includes original code
   * includes error list
   * includes hints

3. Call LLM again

4. Accept patch ONLY if:

   * error count decreases

5. Retry up to:

```python
max_repair_attempts = 2
```

---

### Step 5 — Sandboxed Execution

```python
netlist = RestrictedExecutor.execute(python_code)
```

#### Security Model:

* No full Python access
* Only safe builtins allowed:

```python
print, str, int, float, len, range, ...
```

* `CircuitBuilder` injected manually:

```python
namespace["CircuitBuilder"] = CircuitBuilder
```

#### Blocked capabilities:

* File I/O
* OS/system calls
* Imports
* dynamic execution

---

### Step 6 — Runtime Error Handling

If execution fails:

```python
runtime_error → RepairEngine → retry
```

* One additional repair attempt is made
* Prevents full pipeline failure

---

### Step 7 — Netlist Generation (Builder)

Inside executed code:

```python
netlist = builder.netlist()
```

`CircuitBuilder.netlist()` constructs:

```text
* Title

R1 in out 10k
C1 out 0 1u

.tran 1u 1m

.end
```

---

### Step 8 — Final Output

```python
SynthesisResult(
    python_code=...,
    netlist=...,
    synthesis_metadata=...,
    repair_attempts=...
)
```

---

## Key Design Principles

---

### 1. Two-Layer Architecture

| Layer          | Role                             |
| -------------- | -------------------------------- |
| LLM            | Reasoning + structure generation |
| CircuitBuilder | Deterministic SPICE generation   |

#### Benefit:

* Avoids direct SPICE hallucination
* Guarantees syntactic correctness

---

### 2. Compiler-Like Pipeline

This system behaves like a compiler:

| Stage          | Equivalent                       |
| -------------- | -------------------------------- |
| Blueprint      | Intermediate Representation (IR) |
| LLM Output     | Source Code                      |
| AST Validator  | Static Analysis                  |
| Repair Engine  | Error Correction                 |
| Executor       | Runtime                          |
| CircuitBuilder | Codegen Backend                  |

---

### 3. Safety-First Execution

* AST filtering before execution
* Restricted builtins
* No imports allowed
* Controlled namespace

---

### 4. Incremental Repair (Not Regeneration)

* Preserves working logic
* Fixes only broken parts
* Reduces token usage and instability

---

## Integration with Other Modules

---

### Planner → Synthesizer

```text
Planner → CircuitBlueprint → Synthesizer
```

---

### Synthesizer → Validator / Simulator (future)

```text
Synthesizer → Netlist → SPICE Simulator
                         ↓
                     Error Feedback
                         ↓
                      Repair Loop
```

---

## Summary

The Synthesizer module implements a **robust, safe, and extensible circuit generation pipeline**:

* LLM for reasoning
* AST for safety
* Repair engine for resilience
* Sandbox for execution
* Builder for correctness

This design ensures:

* high reliability
* reduced hallucination risk
* production-ready behavior

---

## Developer Mental Model

```text
Blueprint → Python Code → Validation → Repair → Execution → Netlist
```

---

## Entry Point

```python
synthesize_circuit(blueprint: dict) -> SynthesisResult
```

---

This is the **only function external modules need to call**.


## Extra Note:

### AST - AST stands for Abstract Syntax Tree. It is a hierarchical data structure that represents the logical structure of source code.

In this specific script, `ast` is used as a security sandbox and validator.
Since the code being executed is likely generated by an LLM (which can be unpredictable or malicious), the CodeValidator class uses the ast module to "inspect the luggage" of the code before allowing it to run.
Here is the breakdown of how it’s being used:
## 1. Static Analysis (Safety Inspection)
Instead of running the code to see what it does, the script uses ast.parse(code) to turn the raw string into a tree. It then "walks" that tree to find dangerous instructions:

* Blocking Imports: It checks for ast.Import and ast.ImportFrom. This prevents the generated code from importing dangerous modules like os or subprocess to delete files or hack the system.
* Blocking Dangerous Keywords: It looks for ast.Global or ast.Async... nodes to ensure the code stays simple and doesn't try to manipulate the Python environment in complex ways.
* Filtering Attributes: In _check_forbidden_attrs, it looks for ast.Attribute nodes to block access to "under-the-hood" Python secrets like __class__ or __globals__, which could be used to bypass the sandbox.

## 2. API Enforcement
The script uses the AST to ensure the LLM actually followed instructions.

* Checking for Calls: _check_required_calls scans the tree for ast.Call nodes to verify that CircuitBuilder() was actually used.
* Verifying Results: _check_netlist_assignment looks for ast.Assign nodes to confirm that the code ends with a variable named netlist.

## 3. Syntax Pre-checking
Before the code ever reaches the exec() command, ast.parse acts as a first line of defense. If the LLM generated "broken" code with typos, ast catches the SyntaxError and reports the exact line number via the ValidationError class.
## Summary
In short, ast here acts as a X-ray machine. It allows the CodeValidator to understand the intent and structure of the code without actually running it, ensuring it is safe and complete before the RestrictedExecutor takes the risk of executing it.
Do you want to see how to add a new restriction to this validator (e.g., blocking while loops to prevent infinite execution)?

