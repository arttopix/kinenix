"""1.0.0: exit codes with a meaning (docs/design/agent-interface.md, section 4) and `Run <run_id>` first."""
import os
import re
import subprocess
import sys

import pytest

from kinenix import exit_codes
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow

STEP = "### 1. Wait (`logic.delay`)\n- **seconds:** 0\n"


def _flow(steps, requires=""):
    return f"# Codes\n{requires}\n## Steps\n\n{steps}"


def _cli(tmp_path, *args):
    env = {**os.environ, "KINENIX_FLOWS_DIR": str(tmp_path)}
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)


def _bundle(tmp_path, name, text):
    bundle = tmp_path / name
    bundle.mkdir()
    (bundle / "flow.md").write_text(text, encoding="utf-8")
    return name


def _run_context(text):
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(markdown_to_flow(text))


@pytest.mark.parametrize("steps, requires, code", [
    (STEP, "", exit_codes.OK),
    ("### 1. Read (`file.read_text`)\n- **path:** ./missing.txt\n", "", exit_codes.TECHNICAL),
    ("### 1. Stop (`flow.fail`)\n- **message:** total does not match\n", "", exit_codes.BUSINESS),
    ("### 1. Stop (`flow.fail`)\n- **message:** site down\n- **category:** technical\n", "", exit_codes.TECHNICAL),
    ("### 1. Count (`logic.set_variable`)\n- **name:** n\n- **value:** ${len(1, 2)}\n", "", exit_codes.INVALID_FLOW),
    ("### 1. Nope (`web.nothing`)\n", "", exit_codes.INVALID_FLOW),
    (STEP, "> Requires: kinenix>=99.0\n", exit_codes.NEWER_KINENIX),
    # A failure in Finally after successful steps is technical, whatever stopped it
    (STEP + "\n## Finally\n\n### 2. Stop (`flow.fail`)\n- **message:** x\n", "", exit_codes.TECHNICAL),
    # Failures the flow handles itself end the run with 0: the run did not stop
    ("### 1. Read (`file.read_text`)\n- **path:** ./missing.txt\n- **on_error:** continue\n", "", exit_codes.OK),
])
def test_a_run_ends_with_the_code_of_its_failure(steps, requires, code):
    assert exit_codes.for_run(_run_context(_flow(steps, requires))) == code


def test_kinenix_run_prints_the_run_id_first_and_exits_with_its_code(tmp_path):
    _bundle(tmp_path, "ok", _flow(STEP))
    result = _cli(tmp_path, "run", "ok", "--log-dir", str(tmp_path / "logs"))
    assert result.returncode == 0, result.stderr
    first = result.stdout.splitlines()[0]
    assert re.fullmatch(r"Run \d{8}T\d{6}-[a-z]{4}", first), first
    run_id = first.split()[1]
    assert any(run_id in p.name for p in (tmp_path / "logs").rglob("*.json*"))  # the same id names the log

    _bundle(tmp_path, "business", _flow("### 1. Stop (`flow.fail`)\n- **message:** no data\n"))
    assert _cli(tmp_path, "run", "business", "--log-dir", str(tmp_path / "logs")).returncode == exit_codes.BUSINESS


@pytest.mark.parametrize("args, code", [
    (("run", "no-such-flow"), exit_codes.NOT_FOUND),
    (("validate", "no-such-flow"), exit_codes.NOT_FOUND),
    (("run", "ok", "--vars", "{not json"), exit_codes.USAGE),
    (("run", "ok", "--config", "config/missing.json"), exit_codes.NOT_FOUND),
    (("run", "--no-such-option"), exit_codes.USAGE),
    (("validate", "invalid"), exit_codes.INVALID_FLOW),
    (("init",), exit_codes.USAGE),
    (("init", "x", "--example", "no-such-example"), exit_codes.NOT_FOUND),
    (("actions", "nothing"), exit_codes.NOT_FOUND),
])
def test_command_problems_have_their_own_codes(tmp_path, args, code):
    _bundle(tmp_path, "ok", _flow(STEP))
    _bundle(tmp_path, "invalid", _flow("### 1. Nope (`web.nothing`)\n"))
    result = _cli(tmp_path, *args)
    assert result.returncode == code, result.stdout + result.stderr


def test_connect_to_a_hub_that_does_not_answer_is_unreachable(tmp_path):
    env = {**os.environ, "KINENIX_SETTINGS_FILE": str(tmp_path / "kinenix.env")}

    def connect(url):
        # connect asks for the key at a terminal; an empty answer means no key
        return subprocess.run([sys.executable, "-m", "kinenix.cli", "connect", url], cwd=tmp_path, env=env,
                              input="\n", capture_output=True, text=True, timeout=60)

    result = connect("http://127.0.0.1:9")
    assert result.returncode == exit_codes.UNREACHABLE, result.stdout
    bad = connect("ftp://hub")  # not an http(s) address
    assert bad.returncode == exit_codes.USAGE, bad.stdout
