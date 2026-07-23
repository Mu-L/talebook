from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"


def test_pull_request_description_and_design_preview_rules_are_documented():
    instructions = AGENTS.read_text(encoding="utf-8")

    assert "### Pull Request 提交规范" in instructions
    assert all(
        requirement in instructions
        for requirement in (
            "背景或目标",
            "关键改动",
            "实际验证结果",
            "风险或兼容性",
            "方案路径或豁免原因",
            "截图",
            "完整 commit SHA",
        )
    )
    assert "https://github.com/<owner>/<repo>/blob/<commit-sha>/<path>" in instructions
    assert "https://raw.githack.com/<owner>/<repo>/<commit-sha>/<path>" in instructions
    assert (
        "https://raw.githack.com/talebook/talebook/18113f147aefa0ad79e8c7efd93f1c882610b3ed/"
        "design/webserver/20260721-booksource-large-json-import.active.html"
    ) in instructions
