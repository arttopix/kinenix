"""Conditions compare numbers as numbers and say so when they cannot (#160), and report groups (#161)."""
import pytest

from kinenix import exit_codes
from kinenix.engine.conditions import ConditionError, grouping_problem, number_value
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import validate_flow


def _holds(condition, **variables):
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None))._condition_holds(condition, variables)


@pytest.mark.parametrize("text, number", [
    ("1,200", 1200), ("฿1200", 1200), ("1,200.50", 1200.5), (" 15 ", 15), ("-3", -3), ("$-3", -3), ("-฿3", -3),
    (".5", 0.5), (100, 100), (1.5, 1.5), ("1200฿", 1200),
])
def test_values_that_are_numbers(text, number):
    assert number_value(text) == number


@pytest.mark.parametrize("text", ["N/A", "", None, "3 of 5", "12 items", "1,2,3", "1200,50", True, "2026-11-04"])
def test_values_that_are_not_numbers(text):
    assert number_value(text) is None


@pytest.mark.parametrize("condition, value, expected", [
    ("${p} > 500", "1,200", True),
    ("${p} > 500", "฿1200", True),
    ("not ${p} > 500", "1,200", False),
    ("${p} <= 1200", "1,200", True),
    ("${p} == 100", 100.0, True),
    ("${p} == 100", "100.00", True),
    ("${p} != 100", "100.00", False),
    ("${p} == 1,200", 1200, True),
    ("${p} == 0012", "12", True),
    ("${p} == Active", "active", True),
    ("${p} == true", True, True),
])
def test_comparisons(condition, value, expected):
    assert _holds(condition, p=value) is expected


@pytest.mark.parametrize("condition, value, expected", [
    ("${p} == '0012'", "12", False),
    ("${p} == '0012'", "0012", True),
    ("${p} != '0012'", "12", True),
    ("${p} == '100'", "100.00", False),
    ("${p} == 'Active'", "ACTIVE", True),
])
def test_a_quoted_side_compares_as_text(condition, value, expected):
    assert _holds(condition, p=value) is expected


@pytest.mark.parametrize("condition, variables, reason", [
    ("${p} > 500", {"p": "N/A"}, "'N/A' is not a number"),
    ("${p} > 500", {"p": ""}, "a side is empty"),
    ("${p} > 500", {"p": "12 items"}, "'12 items' is not a number"),
    ("${missing} > 5", {}, "a side is empty"),
    ("not ${missing} > 5", {}, "a side is empty"),
])
def test_a_side_that_is_not_a_number_fails_and_says_why(condition, variables, reason):
    with pytest.raises(ConditionError) as failure:
        _holds(condition, **variables)
    assert reason in str(failure.value) and condition.replace("not ", "") in str(failure.value)


def test_checking_for_empty_first_guards_a_comparison():
    assert _holds("${p} is not empty and ${p} > 0", p="") is False


def _run(steps):
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(markdown_to_flow(f"# C\n\n## Steps\n\n{steps}"))


def test_a_run_stops_with_the_reason_and_exit_code_4():
    context = _run("### 1. Rule (`flow.fail`)\n- **condition:** `${amount} > 100`\n- **message:** too much\n")
    assert context.has_error and exit_codes.for_run(context) == exit_codes.INVALID_FLOW
    assert "a side is empty" in context.failure_details.error_message


def test_a_rule_fires_for_a_value_read_from_a_page():
    flow = "## Variables\n- `amount`: 1,200\n\n"
    context = FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(markdown_to_flow(
        f"# C\n\n{flow}## Steps\n\n### 1. Rule (`flow.fail`)\n- **condition:** `${{amount}} > 500`\n- **message:** too much\n"))
    assert exit_codes.for_run(context) == exit_codes.BUSINESS


@pytest.mark.parametrize("condition", [
    "(${a} == 1 or ${b} == 2) and ${c} == 3",
    "${c} == 3 and (${a} == 1 or ${b} == 2)",
    "${c} == 3 or (${a} == 1)",
    "not (${a} == 1)",
])
def test_groups_are_reported(condition):
    assert grouping_problem(condition)
    with pytest.raises(ConditionError, match="parentheses cannot group"):
        _holds(condition, a=1, b=2, c=3)


@pytest.mark.parametrize("condition, value", [
    ("${name} == Acme (Thailand)", "Acme (Thailand)"),
    ("${name} == Acme (Thailand) and ${name} is not empty", "Acme (Thailand)"),
    ("${name} == '(none)'", "(none)"),
])
def test_parentheses_in_values_stay_allowed(condition, value):
    assert grouping_problem(condition) is None
    assert _holds(condition, name=value) is True


def test_kinenix_validate_reports_a_group():
    flow = markdown_to_flow("""# C

## Steps

### 1. Step (`logic.delay`)
- **seconds:** 0
- **condition:** `(${a} == 1 or ${b} == 2) and ${c} == 3`

### 2. Block (`logic.if`)
- **condition:** `(${a} == 1)`
- **Sub-steps:**
  - Wait (`logic.delay`):
    - **seconds:** 0
""")
    issues = [i for i in validate_flow(flow) if "parentheses cannot group" in i]
    assert len(issues) == 2 and "Step 'step_1'" in issues[0]


def test_an_apostrophe_is_not_a_quote():
    assert _holds("${a} == don't and ${b} == can't", a="don't", b="can't") is True
    assert _holds("${a} == don't and ${b} == can't", a="don't", b="no") is False
