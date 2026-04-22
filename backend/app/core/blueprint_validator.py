from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    category: str
    message: str
    component_name: Optional[str] = None
    node: Optional[str] = None


@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    validated_blueprint: Optional[dict] = None

    def add_error(
        self,
        category: str,
        message: str,
        component: Optional[str] = None,
        node: Optional[str] = None,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=category,
                message=message,
                component_name=component,
                node=node,
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        category: str,
        message: str,
        component: Optional[str] = None,
        node: Optional[str] = None,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=category,
                message=message,
                component_name=component,
                node=node,
            )
        )

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                    "component_name": i.component_name,
                    "node": i.node,
                }
                for i in self.issues
            ],
            "validated_blueprint": self.validated_blueprint,
        }


class ComponentValidator:
    ALLOWED_COMPONENT_TYPES = {
        "resistor",
        "capacitor",
        "inductor",
        "mosfet",
        "bjt",
        "opamp",
        "voltage_source",
        "current_source",
        "diode",
    }

    REQUIRED_PARAMS = {
        "resistor": ["resistance"],
        "capacitor": ["capacitance"],
        "inductor": ["inductance"],
        "mosfet": ["w", "l", "model"],
        "bjt": ["model"],
        "opamp": ["model"],
        "voltage_source": ["dc_value"],
        "current_source": ["dc_value"],
        "diode": ["model"],
    }

    COMPONENT_PREFIXES = {
        "resistor": "R",
        "capacitor": "C",
        "inductor": "L",
        "mosfet": "M",
        "bjt": "Q",
        "opamp": "U",
        "voltage_source": "V",
        "current_source": "I",
        "diode": "D",
    }

    MIN_NODES = {
        "resistor": 2,
        "capacitor": 2,
        "inductor": 2,
        "mosfet": 4,
        "bjt": 3,
        "opamp": 5,
        "voltage_source": 2,
        "current_source": 2,
        "diode": 2,
    }

    @classmethod
    def validate_component(cls, comp: dict) -> list[ValidationIssue]:
        issues = []
        comp_type = comp.get("component_type", "").lower()
        name = comp.get("name", "")

        if not comp_type:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="missing_field",
                    message="Component missing 'component_type' field",
                    component_name=name,
                )
            )
            return issues

        if comp_type not in cls.ALLOWED_COMPONENT_TYPES:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="invalid_component_type",
                    message=f"Unknown component type '{comp_type}'",
                    component_name=name,
                )
            )
            return issues

        if not name:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="missing_field",
                    message="Component missing 'name' field",
                    component_name=name,
                )
            )
        else:
            expected_prefix = cls.COMPONENT_PREFIXES.get(comp_type, "")
            if expected_prefix and not name.upper().startswith(expected_prefix):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="naming_convention",
                        message=f"Component name '{name}' should start with '{expected_prefix}'",
                        component_name=name,
                    )
                )

        nodes = comp.get("nodes", [])
        min_nodes = cls.MIN_NODES.get(comp_type, 2)
        if len(nodes) < min_nodes:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="insufficient_nodes",
                    message=f"Component '{name}' has {len(nodes)} nodes, requires at least {min_nodes}",
                    component_name=name,
                )
            )

        params = comp.get("parameters", {})
        if not isinstance(params, dict):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="invalid_parameters",
                    message=f"Component '{name}' parameters must be a dictionary",
                    component_name=name,
                )
            )
        else:
            required = cls.REQUIRED_PARAMS.get(comp_type, [])
            for req_param in required:
                if req_param not in params:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="missing_parameter",
                            message=f"Component '{name}' missing required parameter '{req_param}'",
                            component_name=name,
                        )
                    )

        return issues


class NodeValidator:
    NODE_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

    @classmethod
    def validate_nodes(
        cls, components: list[dict], ground_node: str
    ) -> list[ValidationIssue]:
        issues = []
        referenced_nodes: set[str] = set()
        defined_nodes: set[str] = set()

        for comp in components:
            name = comp.get("name", "unknown")
            nodes = comp.get("nodes", [])

            for node in nodes:
                if not node:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="invalid_node",
                            message=f"Component '{name}' has empty node reference",
                            component_name=name,
                        )
                    )
                    continue

                if not cls.NODE_PATTERN.match(node):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="invalid_node",
                            message=f"Invalid node name '{node}' in component '{name}'",
                            component_name=name,
                            node=node,
                        )
                    )
                    continue

                referenced_nodes.add(node)
                defined_nodes.add(node)

        all_nodes = referenced_nodes | defined_nodes

        if ground_node not in all_nodes and ground_node != "0":
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="missing_ground",
                    message=f"Ground node '{ground_node}' is defined but not connected to any component",
                )
            )

        if "0" not in all_nodes and ground_node != "0":
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="missing_ground",
                    message="No connection to ground node '0' found",
                )
            )

        for node in referenced_nodes:
            if node != ground_node and node not in defined_nodes:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="unconnected_node",
                        message=f"Node '{node}' referenced but not connected to any component",
                        node=node,
                    )
                )

        return issues


class AnalysisValidator:
    ALLOWED_ANALYSIS_TYPES = {"ac", "dc", "transient", "op", "dc_sweep"}

    REQUIRED_PARAMS = {
        "ac": ["start_freq", "stop_freq", "num_points"],
        "dc": ["source", "start", "stop", "increment"],
        "transient": ["tstart", "tstop", "tstep"],
        "op": [],
        "dc_sweep": ["sweep_variable", "start", "stop", "increment"],
    }

    @classmethod
    def validate_analyses(cls, analyses: list[dict]) -> list[ValidationIssue]:
        issues = []

        if not analyses:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="missing_analysis",
                    message="No analysis directive specified - at least one required",
                )
            )
            return issues

        for i, analysis in enumerate(analyses):
            analysis_type = analysis.get("type", "").lower()

            if not analysis_type:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="missing_field",
                        message=f"Analysis {i} missing 'type' field",
                    )
                )
                continue

            if analysis_type not in cls.ALLOWED_ANALYSIS_TYPES:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="invalid_analysis_type",
                        message=f"Unknown analysis type '{analysis_type}'",
                    )
                )
                continue

            params = analysis.get("parameters", {})
            if not isinstance(params, dict):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="invalid_parameters",
                        message=f"Analysis '{analysis_type}' parameters must be a dictionary",
                    )
                )
            else:
                required = cls.REQUIRED_PARAMS.get(analysis_type, [])
                for req_param in required:
                    if req_param not in params:
                        issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                category="missing_parameter",
                                message=f"Analysis '{analysis_type}' missing required parameter '{req_param}'",
                            )
                        )

        return issues


class BlueprintValidator:
    def __init__(self):
        self.component_validator = ComponentValidator()
        self.node_validator = NodeValidator()
        self.analysis_validator = AnalysisValidator()

    def validate(self, blueprint: dict) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        blueprint = dict(blueprint) if blueprint else {}

        if not blueprint:
            result.add_error("missing_blueprint", "Blueprint is empty or None")
            return result

        circuit_id = blueprint.get("circuit_id", "")
        if not circuit_id:
            result.add_warning("missing_field", "Blueprint missing 'circuit_id'")

        description = blueprint.get("description", "")
        if not description:
            result.add_warning("missing_field", "Blueprint missing 'description'")

        components = blueprint.get("components", [])
        if not components:
            result.add_error(
                "missing_components", "Blueprint has no components defined"
            )
            return result

        for comp in components:
            comp_issues = self.component_validator.validate_component(comp)
            for issue in comp_issues:
                if issue.severity == ValidationSeverity.ERROR:
                    result.add_error(
                        issue.category, issue.message, issue.component_name, issue.node
                    )
                else:
                    result.add_warning(
                        issue.category, issue.message, issue.component_name, issue.node
                    )

        ground_node = blueprint.get("ground_node", "0")
        node_issues = self.node_validator.validate_nodes(components, ground_node)
        for issue in node_issues:
            if issue.severity == ValidationSeverity.ERROR:
                result.add_error(
                    issue.category, issue.message, issue.component_name, issue.node
                )
            else:
                result.add_warning(
                    issue.category, issue.message, issue.component_name, issue.node
                )

        analyses = blueprint.get("analyses", [])
        analysis_issues = self.analysis_validator.validate_analyses(analyses)
        for issue in analysis_issues:
            if issue.severity == ValidationSeverity.ERROR:
                result.add_error(
                    issue.category, issue.message, issue.component_name, issue.node
                )
            else:
                result.add_warning(
                    issue.category, issue.message, issue.component_name, issue.node
                )

        if result.is_valid:
            result.validated_blueprint = blueprint

        return result


def validate_circuit_blueprint(blueprint: dict) -> ValidationResult:
    validator = BlueprintValidator()
    return validator.validate(blueprint)
