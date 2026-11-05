"""Values placed inside text read as written in a flow, not in Python's format (#174)."""
import json

import pytest

from kinenix.engine.evaluator import VariableEvaluator


def _value(template, **variables):
    return VariableEvaluator.evaluate_value(template, variables)


@pytest.mark.parametrize("value, text", [
    (1200.0, "1200"),
    (1200.5, "1200.5"),
    (1200, "1200"),
    (0.0, "0"),
    (True, "true"),
    (False, "false"),
    (None, ""),
    ("plain", "plain"),
    ([{"a": 1}], '[{"a": 1}]'),
    ({"a": True, "b": None}, '{"a": true, "b": null}'),
    (["ไทย"], '["ไทย"]'),
    ([], "[]"),
])
def test_values_inside_text(value, text):
    assert _value("Total: ${x}!", x=value) == f"Total: {text}!"


@pytest.mark.parametrize("value", [1200.0, True, [{"a": 1}], {"a": 1}, None])
def test_a_value_alone_keeps_its_type(value):
    assert _value("${x}", x=value) == value and type(_value("${x}", x=value)) is type(value)


def test_a_very_large_number_stays_readable_as_a_number():
    assert float(_value("n: ${x}", x=1e20).split()[1]) == 1e20


def test_functions_write_values_the_same_way():
    assert _value("${join(rows, ', ')}", rows=[1.0, True, "a"]) == "1, true, a"


def test_a_value_inside_a_json_parameter_keeps_its_type():
    assert _value({"total": "${x}", "note": "n ${x}"}, x=5.0) == {"total": 5.0, "note": "n 5"}


def test_json_text_can_be_read_back():
    assert json.loads(_value("Rows: ${x}", x=[{"a": 1}]).removeprefix("Rows: ")) == [{"a": 1}]
