import os
os.environ["OPENCODE_API_KEY"] = "sk-sTBd4QJMOGiHKueXMIqYgK8Hr22rStTPb0SreUz29rfSh9WBAECJxmG3zrO9aBIt"
from app.services.circuit_planner import Planner
from app.services.netlist_synthesizer import SpecialistSynthesizer
from app.core.blueprint_validator import validate_circuit_blueprint
# Step 1: Create plan
planner = Planner()
blueprint = planner.create_plan("RC low pass filter with 1k resistor and 1uF capacitor")
print(f"Summary: {blueprint.summary}")
print(f"Components: {blueprint.components}")
# Step 2: Validate
blueprint_dict = {
    "circuit_id": blueprint.circuit_id,
    "description": blueprint.description,
    "input_nodes": blueprint.input_nodes,
    "output_nodes": blueprint.output_nodes,
    "ground_node": blueprint.ground_node,
    "components": [
        {"component_type": c.component_type, "name": c.name, 
         "nodes": c.nodes, "parameters": c.parameters, "model": c.model}
        for c in blueprint.components
    ],
    "analyses": blueprint.analyses,
    "constraints": blueprint.constraints,
    "topology_notes": blueprint.topology_notes,
    "design_decisions": blueprint.design_decisions,
}
validation = validate_circuit_blueprint(blueprint_dict)
print(f"Valid: {validation.is_valid}")
# Step 3: Synthesize netlist
synth = SpecialistSynthesizer()
result = synth.synthesize(validation.validated_blueprint)
print(f"Netlist:\n{result.netlist}")