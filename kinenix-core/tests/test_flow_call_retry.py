"""Only the last attempt of a retried flow.call counts in the run's record, as for any other step (#167)."""
from kinenix import exit_codes
from kinenix.actions.base import BaseAction
from kinenix.actions.registry import register_action
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow

_calls = {"count": 0, "fail_every": 2}


@register_action("test.flaky")
class Flaky(BaseAction):
    """Fails on the first of every `fail_every` calls; with fail_every 0 it always fails."""

    def execute(self, parameters, context):
        _calls["count"] += 1
        every = _calls["fail_every"]
        if every == 0 or _calls["count"] % every == 1:
            raise ConnectionError("site did not answer")
        return "ok"


def _run(tmp_path, fail_every, on_error="next_item", max_retries=1):
    _calls.update(count=0, fail_every=fail_every)
    (tmp_path / "subflows").mkdir()
    (tmp_path / "subflows" / "work.md").write_text(
        "# Work\n\n## Steps\n\n### 1. Try (`test.flaky`)\n", encoding="utf-8")
    flow = markdown_to_flow(f"""# Batch

## Steps

### 1. Each (`logic.loop`)
- **items:** ["a", "b"]
- **item_var:** `i`
- **item_label:** ${{i}}
- **Sub-steps:**
  - Call (`flow.call`):
    - **flow:** ./subflows/work.md
    - **max_retries:** {max_retries}
    - **retry_interval:** 0
    - **on_error:** {on_error}
""")
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(
        flow, initial_vars={"__flow_dir__": str(tmp_path)})


def _failed(context):
    return [r for r in context.step_results if r.status == "failed"]


def test_a_subflow_that_succeeds_on_retry_is_a_done_item(tmp_path):
    context = _run(tmp_path, fail_every=2)
    assert _calls["count"] == 4  # both attempts of both items ran
    assert context.items == {"total": 2, "done": 2, "failed": 0}
    assert context.metrics.failed_steps == 0 and not _failed(context)
    assert exit_codes.for_run(context) == exit_codes.OK


def test_the_call_records_how_many_retries_it_took(tmp_path):
    context = _run(tmp_path, fail_every=2)
    calls = [r for r in context.step_results if r.action == "flow.call"]
    assert [r.retries for r in calls] == [1, 1]


def test_a_subflow_that_fails_every_attempt_is_recorded_once_per_item(tmp_path):
    context = _run(tmp_path, fail_every=0, max_retries=2)
    assert _calls["count"] == 6
    assert context.items == {"total": 2, "done": 0, "failed": 2}
    assert exit_codes.for_run(context) == exit_codes.PARTIAL
    # The failing step of the last attempt and the flow.call that reports it, for each item
    assert [r.action for r in _failed(context)] == ["test.flaky", "flow.call"] * 2


def test_a_subflow_that_fails_every_attempt_still_stops_the_run(tmp_path):
    context = _run(tmp_path, fail_every=0, on_error="fail")
    assert context.has_error
    assert exit_codes.for_run(context) == exit_codes.TECHNICAL
