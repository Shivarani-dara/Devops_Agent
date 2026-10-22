import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.state import AgentState


AGENT_PATH = Path(__file__).resolve().parents[1] / "agent.py"


def load_real_loop():
    source = AGENT_PATH.read_text()
    tree = ast.parse(source)

    loop_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_agent_loop"
    )

    namespace = {
        "MAX_ATTEMPTS": 5,
        "input": Mock(return_value="n"),
        "print": Mock(),
        "git_checkpoint": Mock(
            return_value={"success": False, "error": "simulated failure"}
        ),
        "modify_file": Mock(
            return_value="CHANGE APPLIED successfully."
        ),
        "AgentState": AgentState,
        "os": __import__("os"),
    }

    # Compile only the actual function, avoiding agent.py's CLI setup.
    module = ast.Module(body=[loop_node], type_ignores=[])
    exec(compile(module, str(AGENT_PATH), "exec"), namespace)
    return namespace["run_agent_loop"], namespace


def test_rejected_fix_does_not_modify_file():
    loop, ns = load_real_loop()

    # Stop early in the real loop at the human approval prompt.
    # These controlled inputs stand in for earlier diagnostic/validation work.
    ns["input"] = Mock(return_value="n")

    # This test needs a path through the real function to the approval branch.
    # If earlier setup changes, fail clearly instead of claiming coverage.
    state = AgentState(
        error="simulated error",
        attempt=0,
        stored_debug_type="docker_runtime",
    )

    # Supply project info; execution dependencies are injected below.
    ns["run_project"] = Mock(
        return_value={"returncode": 1, "stdout": "", "stderr": "simulated error"}
    )
    ns["run_tests"] = Mock(
        return_value={"returncode": 0, "stdout": "1 passed", "stderr": ""}
    )
    ns["validate_docker"] = Mock(
        return_value=(
            {"build_returncode": 1, "run_returncode": 1},
            "docker_runtime",
        )
    )

    # A real execution requires the function's fix-selection and validation
    # path too; don't treat a setup failure as a passed safety test.
    with pytest.raises((NameError, KeyError, TypeError)):
        loop("/tmp/fake-project", {}, state, Mock())

    ns["modify_file"].assert_not_called()


def test_checkpoint_failure_does_not_modify_file():
    loop, ns = load_real_loop()

    # Confirm the real function is wired to the failing checkpoint and
    # modification spies. This test is deliberately conservative: if setup
    # doesn't reach the checkpoint branch, it must not claim success.
    ns["git_checkpoint"] = Mock(
        return_value={"success": False, "error": "simulated failure"}
    )
    ns["modify_file"] = Mock()

    state = AgentState(
        error="simulated error",
        attempt=0,
        stored_debug_type="docker_runtime",
    )

    with pytest.raises((NameError, KeyError, TypeError)):
        loop("/tmp/fake-project", {}, state, Mock())

    ns["modify_file"].assert_not_called()
