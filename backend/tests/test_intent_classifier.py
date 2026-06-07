from app.services.intent_classifier import IntentClassifier, classify_intent
from app.models.pipeline_models import IntentType


def test_classifier_create_explicit():
    result = classify_intent("Create a low pass filter with 1k resistor and 1uF capacitor")
    assert result.intent == IntentType.CREATE_CIRCUIT


def test_classifier_create_synonyms():
    for verb in ["Design", "Make", "Build", "Generate", "Construct", "Produce"]:
        result = classify_intent(f"{verb} a voltage divider")
        assert result.intent == IntentType.CREATE_CIRCUIT, f"Failed for '{verb}'"


def test_classifier_explain_question():
    result = classify_intent("What is an RC filter?")
    assert result.intent == IntentType.EXPLAIN_CIRCUIT
    assert result.is_question is True


def test_classifier_explain_explicit():
    result = classify_intent("Explain how a common emitter amplifier works")
    assert result.intent == IntentType.EXPLAIN_CIRCUIT


def test_classifier_modify_explicit():
    result = classify_intent("Change the resistor value to 10k")
    assert result.intent == IntentType.MODIFY_CIRCUIT


def test_classifier_modify_synonyms():
    for verb in ["Modify", "Update", "Adjust", "Change", "Replace"]:
        result = classify_intent(f"{verb} R1 to 470 ohms")
        assert result.intent == IntentType.MODIFY_CIRCUIT, f"Failed for '{verb}'"


def test_classifier_modify_add():
    result = classify_intent("Add a capacitor to the output")
    assert result.intent == IntentType.MODIFY_CIRCUIT


def test_classifier_modify_remove():
    result = classify_intent("Remove the second stage")
    assert result.intent == IntentType.MODIFY_CIRCUIT


def test_classifier_how_question():
    result = classify_intent("How does a differential pair work?")
    assert result.intent == IntentType.EXPLAIN_CIRCUIT


def test_classifier_describe():
    result = classify_intent("Describe the circuit in this netlist")
    assert result.intent == IntentType.EXPLAIN_CIRCUIT


def test_classifier_confidence_create():
    result = classify_intent("Create an amplifier")
    assert result.confidence >= 0.8


def test_classifier_confidence_modify():
    result = classify_intent("Modify the gain")
    assert result.confidence >= 0.8


def test_classifier_empty_rules_only():
    classifier = IntentClassifier(llm_client=None)
    result = classifier.classify("Make a circuit")
    assert result.intent == IntentType.CREATE_CIRCUIT
