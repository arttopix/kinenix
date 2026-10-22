"""#111: common web action errors explained in one line, from Playwright's fixed message patterns."""
import pytest

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.web_errors import explain

# From the insurance quote field test on the Raspberry Pi (shortened)
BLOCKED_BY_BANNER_AND_MENU = """Locator.click: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[data-testid=motorTypeRadio] a:has(div:text-is('ประกันชั้น 2+'))").first
    - locator resolved to <a href="/motor/motor_step_1/2_plus" class="py-4 px-1 border-2 plan ">…</a>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div id="onetrust-group-container" class="ot-sdk-eight ot-sdk-columns">…</div> from <div id="onetrust-consent-sdk">…</div> subtree intercepts pointer events
    - retrying click action
    - waiting 20ms
      - <div itemid="ซื้อประกัน-0" class="submenu min-w-[220px] rounded-[15px]">…</div> from <nav data-cy="header" class="absolute !z-[21] w-full">…</nav> subtree intercepts pointer events
  2 × retrying click action
"""


def test_a_click_blocked_by_a_cookie_banner_and_a_menu_names_both():
    cause, fix = explain(BLOCKED_BY_BANNER_AND_MENU)
    assert cause.startswith(
        "The click on locator(\"[data-testid=motorTypeRadio] a:has(div:text-is('ประกันชั้น 2+'))\") was blocked: "
        "div#onetrust-consent-sdk (cookie banner), then nav[data-cy=header] (menu) covered it")
    assert "Accept or close the cookie banner" in fix and "A menu is open over the element" in fix


@pytest.mark.parametrize("message, cause, fix", [
    ('Locator.click: Timeout 5000ms exceeded.\nCall log:\n  - waiting for locator("#submit")\n',
     'No element matching locator("#submit") appeared within 5 s.', "Compare the selector with the page"),
    ('Locator.click: Error: strict mode violation: locator(".row") resolved to 3 elements:\n',
     'The selector locator(".row") matches 3 elements', "more specific"),
    ("Page.goto: net::ERR_NAME_NOT_RESOLVED at https://example.invalid/\nCall log:\n  - navigating to ...",
     "The website could not be opened: the website's name could not be found (DNS)", "Check the URL"),
    ("Page.goto: net::ERR_SOMETHING_NEW at https://x/", "the browser reported ERR_SOMETHING_NEW", "Check the URL"),
    ('Page.goto: Timeout 30000ms exceeded.\nCall log:\n  - navigating to "https://slow.example/", waiting until "load"\n',
     "The page did not finish loading within 30 s.", "domcontentloaded"),
    ('Locator.click: Timeout 3000ms exceeded.\nCall log:\n  - waiting for locator("#go")\n'
     '    - locator resolved to <button id="go" disabled>Go</button>\n  - element is not enabled\n',
     'locator("#go") was found but stayed disabled for 3 s.', "earlier fields"),
    ('Locator.click: Timeout 3000ms exceeded.\nCall log:\n  - waiting for locator("#x")\n'
     '    - locator resolved to <div id="x" class="modal-backdrop show"></div>\n  - element is not visible\n',
     'locator("#x") was found but stayed hidden for 3 s.', ":visible"),
    ("Locator.click: Target page, context or browser has been closed", "The browser or tab was closed", "web.close"),
])
def test_known_patterns(message, cause, fix):
    explained = explain(message)
    assert explained is not None and cause in explained.root_cause and fix in explained.suggested_fix


@pytest.mark.parametrize("message", ["", "Excel file not found: ./a.xlsx", "division by zero",
                                     "Timeout while waiting for the mail server"])
def test_unknown_messages_are_not_guessed(message):
    assert explain(message) is None


def test_an_unknown_blocker_suggests_waiting_for_it_to_go():
    message = ('Locator.click: Timeout 1000ms exceeded.\n  - waiting for locator("#b")\n'
               '      - <span class="toast">…</span> intercepts pointer events\n')
    cause, fix = explain(message)
    assert "span.toast covered it" in cause and "web.wait_for with state: hidden" in fix


BANNER_PAGE = """<!doctype html><html><body>
<button id="buy" style="margin-top:40px">Buy</button>
<div id="onetrust-consent-sdk" style="position:fixed;inset:0;background:rgba(0,0,0,.4)">
  <div id="onetrust-group-container">This website uses cookies <button id="accept">Accept</button></div>
</div>
<script>document.getElementById('accept').onclick = () => document.getElementById('onetrust-consent-sdk').remove();</script>
</body></html>"""


def _run(tmp_path, steps):
    page = tmp_path / "banner.html"
    page.write_text(BANNER_PAGE, encoding="utf-8")
    subflows = tmp_path / "subflows"
    subflows.mkdir()
    (subflows / "buy.md").write_text(f"# buy\n\n## Steps\n\n{steps}", encoding="utf-8")
    md = f"""# Banner

## Steps

### 1. Open (`web.open`)
- **url:** {page.as_uri()}
- **headless:** true

### 2. Buy (`flow.call`)
- **flow:** ./subflows/buy.md
"""
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(
        markdown_to_flow(md), initial_vars={"__flow_dir__": str(tmp_path)})


def test_a_real_click_under_a_cookie_banner_says_so_also_from_a_subflow(tmp_path, chromium):
    ctx = _run(tmp_path, "### 1. Click Buy (`web.click`)\n- **selector:** `#buy`\n- **timeout:** 1500\n")
    assert ctx.has_error
    cause = ctx.failure_details.root_cause
    assert cause.startswith("In subflow 'buy', step 'Click Buy': The click on locator(\"#buy\") was blocked: "
                            "div#onetrust-consent-sdk (cookie banner) covered it"), cause
    assert "Accept or close the cookie banner" in ctx.failure_details.suggested_fix
    # the step that failed in the subflow carries the same explanation
    inner = [r for r in ctx.step_results if r.step_name == "Click Buy"][0]
    assert inner.failure["root_cause"].startswith("The click on locator(\"#buy\") was blocked")


def test_accepting_the_banner_first_lets_the_click_through(tmp_path, chromium):
    ctx = _run(tmp_path, """### 1. Accept Cookies (`web.click`)
- **selector:** `#accept`
- **optional:** true

### 2. Click Buy (`web.click`)
- **selector:** `#buy`
- **timeout:** 1500
""")
    assert not ctx.has_error, ctx.failure_details and ctx.failure_details.root_cause
