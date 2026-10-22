"""Plain-language causes for the error messages of web actions (#111).

Playwright's messages follow a small set of fixed patterns that do not depend on the website: an element
covering the one to click, a locator that never appeared, a selector matching several elements, a site
that cannot be reached. explain() turns a known pattern into one sentence and a concrete fix for the step
failure's root_cause and suggested_fix; for anything else it returns None and the caller keeps its own
wording. Nothing is guessed, and the full message stays in error_message.
"""
import re
from typing import List, NamedTuple, Optional


class Explanation(NamedTuple):
    root_cause: str
    suggested_fix: str


_TIMEOUT = re.compile(r"Timeout (\d+)ms exceeded")
_LOCATOR = re.compile(r'waiting for (?:locator|get_by_\w+)\((.{1,200}?)\)(?:\.first|\.nth\(\d+\)|\.last)?(?: to be \w+)?\n')
_RESOLVED = re.compile(r"locator resolved to (?:visible |hidden )?(<[^\n]{1,300}?>)")
# "<div id="a" class="b">…</div> from <div id="c">…</div> subtree intercepts pointer events"
_INTERCEPT = re.compile(r"(<[^\n]*?>)(?:…</\w+>)?(?: from (<[^\n]*?>)(?:…</\w+>)? subtree)? intercepts pointer events")
_STRICT = re.compile(r"strict mode violation: (.{1,200}?) resolved to (\d+) elements")
_NET = re.compile(r"net::(ERR_[A-Z_]+)")
# The pointer action Playwright was doing: "Locator.hover: Timeout ..." is a hover, not a click
_ACTION = re.compile(r"\b(?:Locator|Page|Frame|ElementHandle)\.(\w+):")
_ACTION_WORDS = {"dblclick": "double-click", "hover": "hover", "check": "check", "uncheck": "uncheck",
                 "tap": "tap", "set_checked": "check", "setChecked": "check", "drag_to": "drag", "dragTo": "drag"}

_NET_CAUSES = {
    "ERR_NAME_NOT_RESOLVED": "the website's name could not be found (DNS): the address is wrong, or this machine has no working DNS",
    "ERR_CONNECTION_REFUSED": "the server refused the connection: nothing is running at that address and port",
    "ERR_INTERNET_DISCONNECTED": "this machine is not connected to the internet",
    "ERR_CONNECTION_TIMED_OUT": "the website did not answer in time",
    "ERR_TIMED_OUT": "the website did not answer in time",
    "ERR_CONNECTION_RESET": "the connection was cut off by the server or the network",
    "ERR_ADDRESS_UNREACHABLE": "the address cannot be reached from this network",
    "ERR_PROXY_CONNECTION_FAILED": "the proxy server could not be reached",
}

# What a blocking element probably is, from its tag, id, classes, and attributes
_KINDS = (
    ("cookie banner", re.compile(r"cookie|consent|onetrust|cookiebot|gdpr|cmp-", re.I)),
    ("popup or dialog", re.compile(r"modal|dialog|popup|overlay|backdrop|lightbox", re.I)),
    ("menu", re.compile(r"<nav\b|menu|dropdown|navbar|header", re.I)),
)
_FIXES = {
    "cookie banner": "Accept or close the cookie banner before this step, for example with a web.click on its accept "
                     "button and optional: true. Banners can appear a few seconds late: give that click a longer "
                     "timeout, or repeat it right before this step.",
    "popup or dialog": "Close the popup before this step (a web.click on its close button, with optional: true when "
                       "it does not always appear).",
    "menu": "A menu is open over the element, often left open by a web.hover. Move the mouse to another element "
            "(web.hover) or close the menu before this step.",
}


def _describe(tag: str) -> str:
    """A short name for an HTML start tag: tag#id, tag[data-testid=..], or tag.first-class."""
    name = re.match(r"<(\w+)", tag)
    name = name.group(1) if name else "element"
    for attribute, form in (("id", "{n}#{v}"), ("data-testid", "{n}[data-testid={v}]"), ("data-cy", "{n}[data-cy={v}]"),
                            ("itemid", "{n}[itemid={v}]")):
        found = re.search(rf'\b{attribute}="([^"]{{1,80}})"', tag)
        if found:
            return form.format(n=name, v=found.group(1))
    classes = re.search(r'\bclass="([^"]{1,200})"', tag)
    if classes and classes.group(1).split():
        return f"{name}.{classes.group(1).split()[0]}"
    return name


def _kind(*tags: str) -> Optional[str]:
    text = " ".join(t for t in tags if t)
    for kind, pattern in _KINDS:
        if pattern.search(text):
            return kind
    return None


def _target(message: str) -> str:
    locator = _LOCATOR.search(message)
    return f"locator({locator.group(1)})" if locator else "the element"


def _pointer_action(message: str) -> str:
    action = _ACTION.search(message)
    return _ACTION_WORDS.get(action.group(1), "click") if action else "click"


def _seconds(message: str) -> str:
    timeout = _TIMEOUT.search(message)
    return f"{int(timeout.group(1)) / 1000:g} s" if timeout else "the timeout"


def explain(message: str) -> Optional[Explanation]:
    """root_cause and suggested_fix for a known web error message, or None."""
    if not message:
        return None

    blockers: List[tuple] = []
    for inner, outer in _INTERCEPT.findall(message):
        blocker = (_describe(outer) if outer else _describe(inner), _kind(inner, outer))
        if blocker not in blockers:
            blockers.append(blocker)
    if blockers:
        # A cookie banner, popup, or menu tells more than an anonymous element; name those first
        blockers.sort(key=lambda b: b[1] is None)
        names = ", then ".join(f"{name} ({kind})" if kind else name for name, kind in blockers[:3])
        fixes = [_FIXES[kind] for kind in dict.fromkeys(kind for _, kind in blockers if kind)]
        fix = " ".join(fixes) or ("Wait until the covering element is gone (web.wait_for with state: hidden) or "
                                  "close it before this step.")
        action = _pointer_action(message)
        return Explanation(
            f"The {action} on {_target(message)} was blocked: {names} covered it, so the {action} would have hit "
            f"the wrong element. The element itself was found and ready.", fix)

    strict = _STRICT.search(message)
    if strict:
        return Explanation(
            f"The selector {strict.group(1)} matches {strict.group(2)} elements, so it is not clear which one to use.",
            "Make the selector more specific (an id, data-testid, or text), or add :visible, or >> nth=0 for the "
            "first match.")

    net = _NET.search(message)
    if net:
        cause = _NET_CAUSES.get(net.group(1), f"the browser reported {net.group(1)}")
        return Explanation(f"The website could not be opened: {cause}.",
                           "Check the URL and open it in a browser on this machine; check the network, VPN, or proxy.")

    if "Target page, context or browser has been closed" in message or "Target closed" in message:
        return Explanation("The browser or tab was closed before this step could use it.",
                           "Check for an earlier web.close or a subflow that closed the browser, or a browser crash.")

    if not _TIMEOUT.search(message):
        return None
    if re.search(r"\b(?:Page|Frame)\.goto\b", message) or "navigating to" in message:
        return Explanation(f"The page did not finish loading within {_seconds(message)}.",
                           "Check that the site is up and fast from this machine; use wait_until: domcontentloaded, "
                           "or raise timeout.")
    resolved = _RESOLVED.search(message)
    target = _target(message)
    if not resolved and _LOCATOR.search(message):
        return Explanation(
            f"No element matching {target} appeared within {_seconds(message)}.",
            "Compare the selector with the page in the screenshot: the page may have changed, or a different "
            "page is shown (an error, a login, a popup). Raise timeout if the page is only slow.")
    if resolved and "element is not visible" in message:
        return Explanation(f"{target} was found but stayed hidden for {_seconds(message)}.",
                           "Something must happen first to show it (a click, a tab, scrolling), or the selector "
                           "matches a hidden copy: add :visible.")
    if resolved and "element is not enabled" in message:
        return Explanation(f"{target} was found but stayed disabled for {_seconds(message)}.",
                           "Fill in what the page requires first (the button is usually enabled by earlier fields).")
    if resolved and "element is not stable" in message:
        return Explanation(f"{target} kept moving (an animation) for {_seconds(message)}.",
                           "Wait for the animation to end (web.wait_for or a short logic.delay) before this step.")
    return None
