from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def load_ci_workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def test_server_uses_base_checkout_and_make_without_explicit_git_config():
    test_server = load_ci_workflow()["jobs"]["test-server"]

    assert test_server["container"]["image"] == "talebook/talebook-base:latest"

    steps = test_server["steps"]
    checkout = next(step for step in steps if step.get("name") == "Checkout code")
    assert checkout["uses"] == "actions/checkout@v4"

    commands = [step.get("run", "") for step in steps]
    assert all("safe.directory" not in command for command in commands)
    assert "make init" in commands
    assert "make lint-py" in commands
    assert "make pytest" in commands
    assert "make test" not in commands
