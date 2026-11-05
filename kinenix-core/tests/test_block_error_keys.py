"""on_error and retries have no effect on logic.if, logic.loop, and flow.return, and validate says so (#168)."""
import pytest

from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import validate_flow

SUB = "- **Sub-steps:**\n  - Wait (`logic.delay`):\n    - **seconds:** 0\n"
IF = "### 1. Block (`logic.if`)\n- **condition:** `1 == 1`\n{key}\n" + SUB
LOOP = "### 1. Each (`logic.loop`)\n- **items:** [1]\n- **item_var:** `i`\n{key}\n" + SUB
RETURN = "### 1. Done (`flow.return`)\n- **value:** 1\n{key}\n"


def _issues(steps):
    return validate_flow(markdown_to_flow(f"# F\n\n## Steps\n\n{steps}"))


@pytest.mark.parametrize("block, action, hint", [
    (IF, "logic.if", "Sub-steps and Else-steps"),
    (LOOP, "logic.loop", "next_item"),
    (RETURN, "flow.return", "Delete them"),
])
@pytest.mark.parametrize("key, name", [
    ("- **on_error:** continue", "on_error"),
    ("- **max_retries:** 2", "max_retries"),
    ("- **retry_interval:** 3", "retry_interval"),
])
def test_error_keys_on_a_block_are_reported_with_what_to_do(block, action, hint, key, name):
    issues = _issues(block.format(key=key))
    assert len(issues) == 1, issues
    assert f"{name} has no effect on {action}" in issues[0] and hint in issues[0]


def test_every_key_is_named_in_one_problem():
    issues = _issues(IF.format(key="- **on_error:** continue\n- **max_retries:** 2"))
    assert len(issues) == 1 and "on_error, max_retries has no effect" in issues[0]


def test_a_block_nested_in_a_block_is_reported():
    steps = ("### 1. Each (`logic.loop`)\n- **items:** [1]\n- **item_var:** `i`\n- **Sub-steps:**\n"
             "  - Check (`logic.if`):\n    - **condition:** `1 == 1`\n    - **on_error:** continue\n"
             "    - **Sub-steps:**\n      - Wait (`logic.delay`):\n        - **seconds:** 0\n")
    assert any("on_error has no effect on logic.if" in issue for issue in _issues(steps))


def test_error_keys_on_steps_inside_a_block_are_fine():
    steps = ("### 1. Each (`logic.loop`)\n- **items:** [1]\n- **item_var:** `i`\n- **Sub-steps:**\n"
             "  - Wait (`logic.delay`):\n    - **seconds:** 0\n    - **max_retries:** 2\n"
             "    - **on_error:** continue\n")
    assert _issues(steps) == []


def test_error_keys_on_flow_call_are_fine(tmp_path):
    assert _issues("### 1. Call (`flow.call`)\n- **flow:** ./sub.md\n- **on_error:** continue\n") == []
