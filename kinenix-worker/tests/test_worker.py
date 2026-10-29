from pathlib import Path
import pytest

from kinenix import exit_codes
from kinenix.engine.markdown import flow_to_markdown
from kinenix_worker.runner import WorkerRunner
from kinenix.models.flow import FlowDefinition, Step


def test_worker_system_info():
    info = WorkerRunner.get_system_info()
    assert "os" in info
    assert "machine" in info
    assert "cpu_count" in info
    assert "memory_total_mb" in info
    assert info["cpu_count"] > 0


def test_worker_execute_simple_flow(tmp_path: Path):
    flow_file = tmp_path / "flow.md"
    flow_content = {
        "name": "Worker Simple Test Flow",
        "variables": {
            "test_key": "initial_value"
        },
        "steps": [
            {
                "id": "step_1",
                "name": "Set Test Variable",
                "action": "logic.set_variable",
                "parameters": {
                    "name": "test_key",
                    "value": "worker_executed_successfully"
                }
            }
        ]
    }
    flow_file.write_text(flow_to_markdown(FlowDefinition(**flow_content)), encoding="utf-8")

    runner = WorkerRunner()
    result = runner.execute_flow(str(flow_file), log_dir=str(tmp_path / "logs"))

    assert result["status"] == "success"
    assert result["has_error"] is False
    assert result["steps_executed"] == 1
    assert result["flow_name"] == "Worker Simple Test Flow"
    assert "worker_system" in result


def test_worker_result_carries_the_exit_code_and_run_id(tmp_path: Path):
    flow_file = tmp_path / "flow.md"
    flow_file.write_text("# Stop\n\n## Steps\n\n### 1. Stop (`flow.fail`)\n- **message:** no data\n", encoding="utf-8")
    result = WorkerRunner().execute_flow(str(flow_file), log_dir=str(tmp_path / "logs"))
    assert result["has_error"] is True
    assert result["exit_code"] == exit_codes.BUSINESS
    assert result["run_id"] and any(result["run_id"] in p.name for p in (tmp_path / "logs").rglob("*.json*"))


def test_worker_run_finishes_when_the_hub_is_down(tmp_path: Path):
    """Failure injection (1.0.0): heartbeats and telemetry fail, the run still completes and keeps its log."""
    import os
    import socket
    import subprocess
    import sys
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    bundle = tmp_path / "slow"
    bundle.mkdir()
    # Long enough for several heartbeats, which must not each print a warning
    (bundle / "flow.md").write_text("# Slow\n\n## Steps\n\n### 1. Wait (`logic.delay`)\n- **seconds:** 3\n", encoding="utf-8")
    env = {**os.environ, "KINENIX_HUB_URL": f"http://127.0.0.1:{port}", "KINENIX_HEARTBEAT_INTERVAL": "0.5"}
    result = subprocess.run([sys.executable, "-m", "kinenix_worker.cli", "run", str(bundle), "--log-dir", str(tmp_path / "logs")],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    assert result.returncode == exit_codes.OK, output
    assert list((tmp_path / "logs").rglob("*_success.json"))
    assert output.count("Heartbeat to Hub") == 1, output
    assert output.count("The run was not sent to the Hub") == 1, output
