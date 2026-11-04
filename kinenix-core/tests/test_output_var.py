"""output_var holds the result of this step, never a value left over from an earlier loop item (#159)."""
from kinenix.actions.base import BaseAction
from kinenix.actions.registry import register_action
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow


@register_action("test.price_of")
class PriceOf(BaseAction):
    def execute(self, parameters, context):
        item = parameters["item"]
        if item == "boom":
            raise ValueError("no such page")
        return None if item == "none" else f"price of {item}"


def _prices(items, on_error="continue", extra=""):
    flow = markdown_to_flow(f"""# Prices

## Variables
- `out`: []

## Steps

### 1. Each (`logic.loop`)
- **items:** {items}
- **item_var:** `i`
- **Sub-steps:**
  - Read (`test.price_of`):
    - **item:** ${{i}}
    - **output_var:** `price`
    - **on_error:** {on_error}
{extra}  - Add (`logic.append`):
    - **target:** `out`
    - **item:** {{"id": "${{i}}", "price": "${{price}}"}}
""")
    context = FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(flow)
    assert not context.has_error, context.failure_details
    return context.variables["out"]


def test_an_action_that_returns_nothing_clears_the_previous_item():
    assert _prices('["a", "none"]') == [{"id": "a", "price": "price of a"}, {"id": "none", "price": None}]


def test_a_failed_step_clears_the_previous_item():
    assert _prices('["a", "boom"]') == [{"id": "a", "price": "price of a"}, {"id": "boom", "price": None}]


def test_a_later_item_gets_its_own_value_again():
    assert [row["price"] for row in _prices('["none", "b"]')] == [None, "price of b"]


def test_a_skipped_step_keeps_the_value_set_before_it():
    flow = markdown_to_flow("""# Default

## Variables
- `price`: 100
- `use_page`: no

## Steps

### 1. Read (`test.price_of`)
- **condition:** `${use_page} == yes`
- **item:** a
- **output_var:** `price`
""")
    context = FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(flow)
    assert context.variables["price"] == 100
