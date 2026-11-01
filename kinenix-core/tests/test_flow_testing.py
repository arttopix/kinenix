"""#105 leftover JSON flows and refreshing AGENTS.md; #106 testing a flow against saved pages with --config."""
import csv
import json
import os
import subprocess
import sys

import pytest

from kinenix import scaffold
from kinenix.engine.validation import leftover_json_flows

STEP = "# {title}\n\n## Steps\n\n### 1. Wait (`logic.delay`)\n- **seconds:** 0\n"


def _cli(tmp_path, *args):
    env = {**os.environ, "KINENIX_FLOWS_DIR": str(tmp_path)}
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=180)


def _bundle(tmp_path, name="old_bot", title="Old Bot"):
    bundle = tmp_path / name
    (bundle / "subflows").mkdir(parents=True)
    (bundle / "flow.md").write_text(STEP.format(title=title), encoding="utf-8")
    return bundle


def test_leftover_json_flows_are_named(tmp_path):
    bundle = _bundle(tmp_path)
    (bundle / "subflows" / "process.md").write_text(STEP.format(title="process"), encoding="utf-8")
    assert leftover_json_flows(bundle / "flow.md") == []

    (bundle / "flow.json").write_text("{}", encoding="utf-8")
    (bundle / "subflows" / "process.json").write_text("{}", encoding="utf-8")
    (bundle / "subflows" / "lookup.json").write_text("{}", encoding="utf-8")  # no .md: not a leftover of a flow
    problems = leftover_json_flows(bundle / "flow.md")
    assert [p.split(" is not read")[0] for p in problems] == ["flow.json", "subflows/process.json"]
    assert "kinenix init --update-agents" in problems[0]

    result = _cli(tmp_path, "validate", "old_bot")
    assert result.returncode == 4 and "flow.json is not read" in result.stderr


def test_update_agents_keeps_the_title_and_the_old_file(tmp_path):
    bundle = _bundle(tmp_path)
    (bundle / "AGENTS.md").write_text("# Instructions for AI assistants: Old Bot\n\nCompile flow.md into flow.json.\n",
                                      encoding="utf-8")
    result = _cli(tmp_path, "init", "old_bot", "--update-agents")
    assert result.returncode == 0, result.stderr
    agents = (bundle / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.startswith("# Instructions for AI assistants: Old Bot\n") and "on_error: next_item" in agents
    assert "Compile flow.md into flow.json" in (bundle / "AGENTS.md.bak").read_text(encoding="utf-8")
    assert (bundle / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert "already current" in _cli(tmp_path, "init", "old_bot", "--update-agents").stdout


def test_update_agents_takes_the_title_from_flow_md_and_refuses_other_folders(tmp_path):
    bundle = _bundle(tmp_path, title="Supplier Invoice Check")
    assert scaffold.update_agent_instructions(bundle) == [bundle / "AGENTS.md", bundle / "CLAUDE.md"]
    assert (bundle / "AGENTS.md").read_text(encoding="utf-8").startswith(
        "# Instructions for AI assistants: Supplier Invoice Check\n")
    assert not (bundle / "AGENTS.md.bak").exists()
    with pytest.raises(ValueError, match="has no flow.md"):
        scaffold.update_agent_instructions(tmp_path)


SAVED_PAGE = """<!doctype html><html><body>
<table id="rates"><thead><tr><th>Currency</th><th>Rate</th></tr></thead>
<tbody><tr><td>USD</td><td>33.10</td></tr><tr><td>EUR</td><td>36.45</td></tr></tbody></table>
</body></html>"""

FLOW = """# Rates

## Steps

### 1. Open Rates (`web.goto`)
- **url:** ${config.rates_url}
- **headless:** true

### 2. Read Rates (`web.get_table`)
- **selector:** `#rates`
- **numeric_columns:** ["Rate"]
- **output_var:** `rates`

### 3. Save (`csv.write`)
- **file_path:** ./output/${config.output_name}
- **data:** ${rates}
"""


def test_a_web_flow_runs_against_saved_pages_with_a_test_config(tmp_path, chromium):
    bundle = tmp_path / "rates"
    (bundle / "config").mkdir(parents=True)
    (bundle / "tests" / "pages").mkdir(parents=True)
    (bundle / "flow.md").write_text(FLOW, encoding="utf-8")
    (bundle / "tests" / "pages" / "rates.html").write_text(SAVED_PAGE, encoding="utf-8")
    (bundle / "config" / "config.json").write_text(json.dumps(
        {"rates_url": "https://www.bot.or.th/rates", "output_name": "rates.csv"}), encoding="utf-8")
    (bundle / "config" / "test.json").write_text(json.dumps({"rates_url": "tests/pages/rates.html"}), encoding="utf-8")

    result = _cli(tmp_path, "run", "rates", "--config", "config/test.json", "--log-dir", str(tmp_path / "logs"))
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    with open(bundle / "output" / "rates.csv", encoding="utf-8-sig") as f:
        assert [(r["Currency"], r["Rate"]) for r in csv.DictReader(f)] == [("USD", "33.1"), ("EUR", "36.45")]


@pytest.mark.parametrize("content, message, code", [
    (None, "'config/missing.json' was not found", 7),
    ("{not json", "is not valid JSON", 2),
    ("[1, 2]", "must hold a JSON object", 2),
])
def test_config_file_problems_stop_before_the_run(tmp_path, content, message, code):
    bundle = _bundle(tmp_path)
    name = "config/missing.json"
    if content is not None:
        (bundle / "config").mkdir()
        name = "config/test.json"
        (bundle / name).write_text(content, encoding="utf-8")
    result = _cli(tmp_path, "run", "old_bot", "--config", name)
    assert result.returncode == code and message in result.stderr
