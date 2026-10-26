"""#117: the first-flow tutorial. Its solution must keep working on the saved pages, as docs/tutorial.md says."""
import csv
import shutil

import pytest

from kinenix import scaffold
from kinenix.engine import requires
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import load_flow
from kinenix.engine.validation import validate_flow


@pytest.fixture
def project(tmp_path, monkeypatch):
    # The solution says Requires: kinenix>=0.5.0b1; the version is raised when 0.5.0b1 is released
    monkeypatch.setattr(requires, "__version__", "999.0")
    return scaffold.create_project(tmp_path / "my-first-flow", example="first_flow")


def _run(project, **config):
    flow = load_flow(project / "flow.md")
    return FlowInterpreter(logger=ExecutionLogger(log_dir=project / "logs")).run_flow(
        flow, initial_vars={"__flow_dir__": str(project), "config": {"headless": True, **config}})


def _rows(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_the_project_starts_with_requirements_and_no_answer(project):
    for name in ("requirements.md", "AGENTS.md", "CLAUDE.md", "config/config.json", "config/empty.json",
                 "tests/pages/catalog.html", "tests/pages/catalog-2.html", "tests/pages/catalog-empty.html",
                 "solution/flow.md"):
        assert (project / name).is_file(), name
    starter = load_flow(project / "flow.md")
    assert [s.action for s in starter.steps] == ["logic.set_variable"]
    assert validate_flow(starter) == []
    assert ("first_flow", True) in [(name, browser) for name, _, browser in scaffold.available_examples()]


def test_the_solution_reads_both_pages_and_finds_the_products_over_budget(project, chromium):
    shutil.copyfile(project / "solution" / "flow.md", project / "flow.md")
    assert validate_flow(load_flow(project / "flow.md")) == []
    context = _run(project)
    assert not context.has_error, context.failure_details and context.failure_details.error_message
    products = _rows(project / "output" / "products.csv")
    assert len(products) == 10 and products[0] == {"name": "Ballpoint Pens, Box of 50", "category": "Writing",
                                                   "price": "189.0"}
    assert [p["name"] for p in _rows(project / "output" / "over_budget.csv")] == [
        "A4 Copy Paper, 5 Reams", "Stapler, Heavy Duty", "Ergonomic Office Chair", "Paper Shredder", "Laminator, A4"]
    assert (project / "output" / "summary.txt").read_text(encoding="utf-8") == \
        "10 products read, 5 over the budget of 500 THB."


def test_breaking_it_on_purpose_gives_the_messages_the_tutorial_describes(project, chromium):
    shutil.copyfile(project / "solution" / "flow.md", project / "flow.md")

    empty = _run(project, catalog_url="tests/pages/catalog-empty.html")  # what config/empty.json sets
    assert empty.has_error
    assert empty.failure_details.error_message.startswith("No products were found at tests/pages/catalog-empty.html")

    flow = (project / "flow.md").read_text(encoding="utf-8")
    (project / "flow.md").write_text(flow.replace('"price": ".price"', '"price": ".cost"'), encoding="utf-8")
    wrong_selector = _run(project)
    assert wrong_selector.has_error
    assert "item 1 has no 'price' (selector '.cost')" in wrong_selector.failure_details.error_message


def test_the_solution_is_not_listed_as_a_flow_of_its_own(project, monkeypatch):
    from kinenix.cli import discover_flows
    monkeypatch.setenv("KINENIX_FLOWS_DIR", str(project.parent))
    monkeypatch.chdir(project.parent)
    flows = discover_flows()
    assert "my-first-flow" in flows and "solution" not in flows
