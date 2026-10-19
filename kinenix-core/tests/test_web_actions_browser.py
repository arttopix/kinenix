"""0.4.0b1 web actions in a real browser, against local pages (no internet): web.goto and subflow page handoff."""
from pathlib import Path

import pytest

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow

PAGES = {
    "a.html": "<html><head><title>Page A</title></head><body><h1>A</h1></body></html>",
    "b.html": "<html><head><title>Page B</title></head><body><h1>B</h1></body></html>",
}


@pytest.fixture
def site(tmp_path, chromium):
    """Local pages, and their file:// URLs as config values."""
    for name, html in PAGES.items():
        (tmp_path / name).write_text(html, encoding="utf-8")
    return {"a": (tmp_path / "a.html").as_uri(), "b": (tmp_path / "b.html").as_uri(), "dir": tmp_path}


def _run(markdown, site, subflows=None):
    for name, text in (subflows or {}).items():
        (site["dir"] / "subflows").mkdir(exist_ok=True)
        (site["dir"] / "subflows" / name).write_text(text, encoding="utf-8")
    interpreter = FlowInterpreter(logger=ExecutionLogger(log_dir=None))
    return interpreter.run_flow(markdown_to_flow(markdown), initial_vars={
        "__flow_dir__": str(site["dir"]), "config": {"a": site["a"], "b": site["b"]}})


@pytest.fixture
def closed_browsers(monkeypatch):
    """Every browser the run closes, to check that no browser process is left behind."""
    closed = []
    original = FlowInterpreter._close_browser

    def spy(self, context, **kwargs):
        browser = context.get_variable("__playwright_browser__")
        original(self, context, **kwargs)
        if browser is not None:
            closed.append(browser)
    monkeypatch.setattr(FlowInterpreter, "_close_browser", spy)
    return closed


GOTO_FLOW = """# Goto

## Steps

### 1. First Page (`web.goto`)
- **url:** ${config.a}
- **headless:** true

### 2. Read A (`web.get_text`)
- **selector:** h1
- **output_var:** `first`

### 3. Second Page In The Same Tab (`web.goto`)
- **url:** ${config.b}
- **wait_until:** domcontentloaded
- **output_var:** `went`

### 4. Read B (`web.get_text`)
- **selector:** h1
- **output_var:** `second`
"""


def test_goto_opens_a_browser_when_needed_and_stays_in_one_tab(site, closed_browsers):
    context = _run(GOTO_FLOW, site)
    assert not context.has_error, context.failure_details
    assert context.get_variable("first") == "A" and context.get_variable("second") == "B"
    went = context.get_variable("went")
    assert went["title"] == "Page B" and went["url"] == site["b"] and went["status"] == "navigated"
    assert len(closed_browsers) == 1 and not closed_browsers[0].is_connected()


def test_goto_reuses_the_tab_of_web_open(site, closed_browsers):
    flow = """# Goto After Open

## Steps

### 1. Open (`web.open`)
- **url:** ${config.a}
- **headless:** true

### 2. Go (`web.goto`)
- **url:** ${config.b}

### 3. Read (`web.get_text`)
- **selector:** h1
- **output_var:** `seen`
"""
    pages = []
    original = FlowInterpreter._close_browser

    def count_pages(self, context, **kwargs):
        browser = context.get_variable("__playwright_browser__")
        if browser is not None:
            pages.append(sum(len(c.pages) for c in browser.contexts))
        original(self, context, **kwargs)
    import kinenix.engine.interpreter as interpreter_module
    interpreter_module.FlowInterpreter._close_browser = count_pages
    try:
        context = _run(flow, site)
    finally:
        interpreter_module.FlowInterpreter._close_browser = original
    assert not context.has_error and context.get_variable("seen") == "B"
    assert pages == [1]  # web.goto did not open a second tab


@pytest.mark.parametrize("bad, message", [
    ("", "'url' is empty"),
    ("${config.missing}", "'url' is empty"),
])
def test_goto_needs_a_url(site, bad, message):
    flow = f"# Bad\n\n## Steps\n\n### 1. Go (`web.goto`)\n- **url:** {bad}\n- **headless:** true\n"
    context = _run(flow, site)
    assert context.has_error and message in context.failure_details.error_message


def test_goto_refuses_an_unknown_wait(site):
    flow = "# Bad\n\n## Steps\n\n### 1. Go (`web.goto`)\n- **url:** ${config.a}\n- **wait_until:** soon\n"
    context = _run(flow, site)
    assert context.has_error and "wait_until 'soon' is not one of" in context.failure_details.error_message


PARENT = """# Parent

## Steps

### 1. Open A (`web.open`)
- **url:** ${config.a}
- **headless:** true

### 2. Move On (`flow.call`)
- **flow:** ./subflows/move.md

### 3. Read (`web.get_text`)
- **selector:** h1
- **output_var:** `seen`
"""

MOVE = """# Move

## Steps

### 1. Go To B (`web.goto`)
- **url:** ${config.b}
"""


def test_the_parent_sees_the_page_the_subflow_left(site, closed_browsers):
    context = _run(PARENT, site, {"move.md": MOVE})
    assert not context.has_error, context.failure_details
    assert context.get_variable("seen") == "B"
    assert len(closed_browsers) == 1 and not closed_browsers[0].is_connected()


def test_a_browser_opened_by_a_subflow_is_closed_at_the_end(site, closed_browsers):
    """Before 0.4.0b1, nothing closed it: the subflow skips cleanup, and the parent did not know about it."""
    parent = PARENT.replace("### 1. Open A (`web.open`)\n- **url:** ${config.a}\n- **headless:** true\n\n", "")
    context = _run(parent.replace("### 2. Move", "### 1. Move").replace("### 3. Read", "### 2. Read"),
                   site, {"move.md": MOVE.replace("- **url:** ${config.b}", "- **url:** ${config.b}\n- **headless:** true")})
    assert not context.has_error, context.failure_details
    assert context.get_variable("seen") == "B"
    assert len(closed_browsers) == 1 and not closed_browsers[0].is_connected()


def test_a_subflow_that_does_not_share_the_browser_closes_its_own(site, closed_browsers):
    parent = PARENT.replace("- **flow:** ./subflows/move.md", "- **flow:** ./subflows/move.md\n- **propagate_sessions:** false")
    context = _run(parent, site, {"move.md": MOVE.replace("- **url:** ${config.b}", "- **url:** ${config.b}\n- **headless:** true")})
    assert not context.has_error, context.failure_details
    assert context.get_variable("seen") == "A"  # the parent kept its own page
    assert len(closed_browsers) == 2 and not any(b.is_connected() for b in closed_browsers)
