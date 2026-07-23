from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    with (ROOT / ".github" / "workflows" / name).open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def workflow_step(job, name):
    for step in job["steps"]:
        if step.get("name") == name:
            return step
    raise AssertionError(f"workflow step not found: {name}")


def test_claude_action_uses_the_dev_container_and_prepares_current_checkout():
    claude_job = workflow("claude.yml")["jobs"]["claude"]
    steps = claude_job["steps"]
    verify = workflow_step(claude_job, "Verify development environment")
    synchronize = workflow_step(claude_job, "Synchronize project dependencies")
    run_claude = workflow_step(claude_job, "Run Claude Code")

    assert claude_job["container"] == {"image": "talebook/talebook:dev", "options": "--user root"}
    assert claude_job["defaults"] == {"run": {"shell": "bash"}}
    assert all(
        probe in verify["run"]
        for probe in (
            "ebook-convert --version",
            "python3 --version",
            "node --version",
            "npm --version",
            "make --version",
            "python3 -m pytest --version",
            "ruff --version",
        )
    )
    assert synchronize["run"] == "make init\nnpm --prefix app ci\n"
    assert steps.index(verify) < steps.index(synchronize) < steps.index(run_claude)

    action_inputs = run_claude["with"]
    assert "path_to_claude_code_executable" not in action_inputs
    assert "path_to_bun_executable" not in action_inputs
    assert "--allowedTools" in action_inputs["claude_args"]
    assert all(
        command in action_inputs["claude_args"]
        for command in (
            "Bash(make:*)",
            "Bash(npm:*)",
            "Bash(npx:*)",
            "Bash(node:*)",
            "Bash(python3:*)",
            "Bash(pytest:*)",
            "Bash(ruff:*)",
        )
    )
