"""1.0.0: what Kinenix 2.0 removes still works in 1.x, with a warning (CHANGELOG, Deprecated)."""
import os
import subprocess
import sys

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import deprecated_uses, validate_flow

OLD_FLOW = """# Old Ways

## Steps

### 1. Wait (`logic.delay`)
- **seconds:** 0
- **on_error:** retry

### 2. Read (`file.read_text`)
- **path:** ./missing.txt
- **fallback_step_id:** step_3

### 3. Recover (`logic.delay`)
- **seconds:** 0
"""


def _cli(tmp_path, *args):
    env = {**os.environ, "KINENIX_FLOWS_DIR": str(tmp_path)}
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)


def test_retry_and_fallback_are_deprecated_but_not_problems():
    flow = markdown_to_flow(OLD_FLOW)
    notices = deprecated_uses(flow)
    assert len(notices) == 2
    assert "on_error retry" in notices[0] and "Kinenix 2.0" in notices[0]
    assert "fallback_step_id" in notices[1] and "Kinenix 2.0" in notices[1]
    assert validate_flow(flow) == []
    assert deprecated_uses(markdown_to_flow(OLD_FLOW.replace("- **on_error:** retry\n", "")
                                            .replace("- **fallback_step_id:** step_3\n", ""))) == []


def test_a_run_logs_the_deprecated_parts_and_still_works(caplog):
    with caplog.at_level("WARNING"):
        context = FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(markdown_to_flow(OLD_FLOW))
    assert not context.has_error  # the fallback still recovers
    assert "on_error retry is deprecated" in caplog.text and "fallback_step_id is deprecated" in caplog.text


def test_validate_prints_deprecations_and_passes(tmp_path):
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "flow.md").write_text(OLD_FLOW, encoding="utf-8")
    result = _cli(tmp_path, "validate", "old")
    assert result.returncode == 0, result.stderr
    assert result.stderr.count("Deprecated:") == 2


def test_old_command_names_warn(tmp_path):
    (tmp_path / "ok").mkdir()
    (tmp_path / "ok" / "flow.md").write_text("# Ok\n\n## Steps\n\n### 1. Wait (`logic.delay`)\n- **seconds:** 0\n",
                                            encoding="utf-8")
    run = _cli(tmp_path, "run", "ok", "--orchestrator", "http://127.0.0.1:9", "--log-dir", str(tmp_path / "logs"))
    assert "Deprecated: --orchestrator is now --hub" in run.stderr
    export = _cli(tmp_path, "export-md", "missing.json")
    assert "Deprecated: kinenix export-md will be removed in Kinenix 2.0" in export.stderr
