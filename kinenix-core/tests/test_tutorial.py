"""#117: the first-flow tutorial. Its solution must keep working on the saved pages, as docs/tutorial.md says."""
import csv
import shutil
from pathlib import Path

import pytest

from kinenix import scaffold
from kinenix.engine import requires
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import load_flow
from kinenix.engine.validation import validate_flow

# The solution stays in the repository: shipped into the reader's project, an AI assistant copied it instead of
# building the flow (field test of 0.5.0b1)
SOLUTION = Path(__file__).resolve().parents[2] / "flows" / "examples" / "first_flow" / "solution" / "flow.md"


@pytest.fixture
def project(tmp_path, monkeypatch):
    # The solution says Requires: kinenix>=0.5.0b1, which may be newer than the version being developed
    monkeypatch.setattr(requires, "__version__", "999.0")
    return scaffold.create_project(tmp_path / "my-first-flow", example="first_flow")


@pytest.fixture
def solved(project):
    shutil.copyfile(SOLUTION, project / "flow.md")
    return project


def _run(project, **config):
    flow = load_flow(project / "flow.md")
    return FlowInterpreter(logger=ExecutionLogger(log_dir=project / "logs")).run_flow(
        flow, initial_vars={"__flow_dir__": str(project), "config": {"headless": True, **config}})


def _rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_the_project_starts_with_requirements_and_no_answer(project):
    for name in ("requirements.md", "AGENTS.md", "CLAUDE.md", "config/config.json", "config/empty.json",
                 "tests/pages/catalog.html", "tests/pages/catalog-2.html", "tests/pages/catalog-empty.html"):
        assert (project / name).is_file(), name
    # Nothing in the project gives the answer away: no solution, and no file points to one
    assert not (project / "solution").exists()
    assert not [p for p in project.rglob("*.md") if "solution/" in p.read_text(encoding="utf-8")
                and p.name not in ("README.md",)]
    starter = load_flow(project / "flow.md")
    assert [s.action for s in starter.steps] == ["logic.set_variable"]
    assert validate_flow(starter) == []
    assert ("first_flow", True) in [(name, browser) for name, _, browser in scaffold.available_examples()]


def test_the_solution_reads_both_pages_and_finds_the_products_over_budget(solved, chromium):
    stale = solved / "output" / "over_budget.csv"
    stale.parent.mkdir()
    stale.write_text("from last month", encoding="utf-8")
    assert validate_flow(load_flow(solved / "flow.md")) == []
    context = _run(solved)
    assert not context.has_error, context.failure_details and context.failure_details.error_message
    products = _rows(solved / "output" / "products.csv")
    assert len(products) == 10 and products[0] == {"name": "Ballpoint Pens, Box of 50", "category": "Writing",
                                                   "price": "189.0"}
    assert [p["name"] for p in _rows(stale)] == [
        "A4 Copy Paper, 5 Reams", "Stapler, Heavy Duty", "Ergonomic Office Chair", "Paper Shredder", "Laminator, A4"]
    assert (solved / "output" / "summary.txt").read_text(encoding="utf-8") == \
        "10 products read, 5 over the budget of 500 THB."


def test_last_months_over_budget_file_is_not_left_behind(solved, chromium):
    stale = solved / "output" / "over_budget.csv"
    stale.parent.mkdir()
    stale.write_text("from last month", encoding="utf-8")
    context = _run(solved, budget=100000)
    assert not context.has_error
    assert not stale.exists()
    assert (solved / "output" / "summary.txt").read_text(encoding="utf-8").endswith("0 over the budget of 100000 THB.")


def test_breaking_it_on_purpose_gives_the_messages_the_tutorial_describes(solved, chromium):
    empty = _run(solved, catalog_url="tests/pages/catalog-empty.html")  # what config/empty.json sets
    assert empty.has_error
    assert empty.failure_details.error_message.startswith("No products were found at tests/pages/catalog-empty.html")

    flow = (solved / "flow.md").read_text(encoding="utf-8")
    (solved / "flow.md").write_text(flow.replace('"price": ".price"', '"price": ".cost"'), encoding="utf-8")
    wrong_selector = _run(solved)
    assert wrong_selector.has_error
    assert "item 1 has no 'price' (selector '.cost')" in wrong_selector.failure_details.error_message


def test_a_solution_folder_is_not_listed_as_a_flow_of_its_own(solved, monkeypatch):
    from kinenix.cli import discover_flows
    (solved / "solution").mkdir()
    shutil.copyfile(SOLUTION, solved / "solution" / "flow.md")  # a reader who saved it next to their flow
    monkeypatch.setenv("KINENIX_FLOWS_DIR", str(solved.parent))
    monkeypatch.chdir(solved.parent)
    flows = discover_flows()
    assert "my-first-flow" in flows and "solution" not in flows
