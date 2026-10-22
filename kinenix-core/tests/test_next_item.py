"""#102: on_error: next_item records the failure and goes on with the next item of the loop."""
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import validate_flow

INVOICES = [{"no": "INV-1", "amount": "1,200"}, {"no": "INV-2", "amount": ""}, {"no": "INV-3", "amount": "300"}]


def run(tmp_path, markdown, **initial):
    bundle = tmp_path / "bundle"
    bundle.mkdir(exist_ok=True)
    ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
        markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(bundle), "config": {"invoices": INVOICES},
                                                  **initial})
    return ctx, bundle


def loop_flow(check, after="", tail=""):
    return f"""# Invoice Check

## Steps

### 1. Each Invoice (`logic.loop`)
- **items:** ${{config.invoices}}
- **item_var:** inv
- **item_label:** ${{inv.no}}
- **Sub-steps:**
{check}
  - Keep (`logic.append`):
    - **target:** checked
    - **item:** ${{inv.no}}
{after}
### 2. Summary (`logic.set_variable`)
- **name:** summary
- **value:** ${{join(checked, ",")}}
{tail}"""


FAIL_WITHOUT_AMOUNT = """  - No Amount (`flow.fail`):
    - **condition:** `${inv.amount} is empty`
    - **message:** Invoice ${inv.no} has no amount
    - **on_error:** next_item"""


def test_next_item_skips_the_rest_of_the_item_and_the_run_succeeds(tmp_path):
    md = loop_flow(FAIL_WITHOUT_AMOUNT)
    # older Kinenix would stop at next_item, so validate asks for a Requires line (the run itself is fine)
    issues = validate_flow(markdown_to_flow(md))
    assert len(issues) == 1 and "on_error: next_item" in issues[0] and "kinenix>=0.4.0b1" in issues[0]
    ctx, _ = run(tmp_path, md)
    assert not ctx.has_error and ctx.failure_details is None
    assert ctx.get_variable("summary") == "INV-1,INV-3"
    assert ctx.items == {"total": 3, "done": 2, "failed": 1}
    failed = [r for r in ctx.step_results if r.status == "failed"]
    assert len(failed) == 1 and failed[0].error_type == "Business"
    assert failed[0].failure["handled"] == "next_item"
    assert ctx.get_variable("error")["message"] == "Invoice INV-2 has no amount"


def test_next_item_inside_logic_if_and_in_a_nested_loop_ends_only_the_innermost_item(tmp_path):
    check = """  - Lines (`logic.loop`):
    - **items:** ["a", "b"]
    - **item_var:** line
    - **Sub-steps:**
      - Check (`logic.if`):
        - **condition:** `${inv.amount} is empty`
        - **Sub-steps:**
          - Stop This Line (`flow.fail`):
            - **message:** no amount on ${line}
            - **on_error:** next_item
      - Line Done (`logic.append`):
        - **target:** lines
        - **item:** ${inv.no}/${line}"""
    ctx, _ = run(tmp_path, loop_flow(check))
    assert not ctx.has_error
    assert ctx.get_variable("lines") == ["INV-1/a", "INV-1/b", "INV-3/a", "INV-3/b"]
    # the outer item goes on after its inner loop
    assert ctx.get_variable("summary") == "INV-1,INV-2,INV-3"


def test_next_item_on_a_flow_call_skips_the_item_when_the_subflow_fails(tmp_path):
    subflows = tmp_path / "bundle" / "subflows"
    subflows.mkdir(parents=True)
    (subflows / "check_one.md").write_text("""# check_one

## Steps

### 1. Amount (`flow.fail`)
- **condition:** `${inv.amount} is empty`
- **message:** Invoice ${inv.no} has no amount
""", encoding="utf-8")
    check = """  - Check One (`flow.call`):
    - **flow:** ./subflows/check_one.md
    - **inputs:** {"inv": "${inv}"}
    - **on_error:** next_item"""
    ctx, _ = run(tmp_path, loop_flow(check))
    assert not ctx.has_error
    assert ctx.get_variable("summary") == "INV-1,INV-3"
    assert ctx.items == {"total": 3, "done": 2, "failed": 1}


def test_retries_come_before_next_item(tmp_path):
    check = """  - Read (`file.read_text`):
    - **path:** ./missing/${inv.no}.txt
    - **max_retries:** 1
    - **retry_interval:** 0
    - **on_error:** next_item"""
    ctx, _ = run(tmp_path, loop_flow(check))
    assert not ctx.has_error and ctx.get_variable("checked") is None
    assert [r.retries for r in ctx.step_results if r.status == "failed"] == [1, 1, 1]


def test_next_item_outside_a_loop_stops_the_run_and_validate_says_so(tmp_path):
    md = """# Not In A Loop

## Steps

### 1. Read (`file.read_text`)
- **path:** ./missing.txt
- **on_error:** next_item

### 2. After (`logic.set_variable`)
- **name:** after
- **value:** reached
"""
    issues = validate_flow(markdown_to_flow(md))
    assert any("on_error next_item is for steps inside a logic.loop" in i for i in issues)
    assert any("Requires: kinenix>=0.4.0b1" in i for i in issues)
    ctx, _ = run(tmp_path, md)
    assert ctx.has_error and ctx.get_variable("after") is None
    assert ctx.step_results[0].failure["handled"] == "stopped"


def test_a_subflow_called_in_a_loop_is_not_inside_that_loop(tmp_path):
    # next_item in the subflow's own steps would end the parent's item from inside another flow; it stops the
    # subflow like fail, and the parent's flow.call decides
    subflows = tmp_path / "bundle" / "subflows"
    subflows.mkdir(parents=True)
    (subflows / "check_one.md").write_text("""# check_one

## Steps

### 1. Amount (`flow.fail`)
- **condition:** `${inv.amount} is empty`
- **message:** no amount
- **on_error:** next_item

### 2. Reached (`logic.set_variable`)
- **name:** reached
- **value:** yes
""", encoding="utf-8")
    check = """  - Check One (`flow.call`):
    - **flow:** ./subflows/check_one.md
    - **inputs:** {"inv": "${inv}"}
    - **on_error:** continue"""
    ctx, _ = run(tmp_path, loop_flow(check))
    assert not ctx.has_error
    assert ctx.get_variable("summary") == "INV-1,INV-2,INV-3"  # continue on the flow.call
    assert ctx.items == {"total": 3, "done": 2, "failed": 1}
