import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_design_docs.py"


def write_design(repo_root, relative_path, body=None):
    path = repo_root / "design" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        body
        or """<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8"><title>有效方案</title></head>
  <body><main><h1>有效方案</h1></main></body>
</html>
""",
        encoding="utf-8",
    )
    return path


def run_check(repo_root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def html_with(content):
    return f"""<!doctype html>
<html lang="zh-CN">
  <head><meta charset="utf-8"><title>方案</title></head>
  <body>{content}</body>
</html>
"""


def test_valid_active_design_passes(tmp_path):
    (tmp_path / "app").mkdir()
    write_design(tmp_path, "app/20260713-reading-theme.active.html")

    result = run_check(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 design document(s) passed" in result.stdout


@pytest.mark.parametrize(
    "relative_path",
    [
        "unknown/20260713-feature.active.html",
        "app/nested/20260713-feature.active.html",
        "app/20260230-feature.active.html",
        "app/20260713-ReadingTheme.active.html",
        "app/20260713-reading-theme.html",
        "app/20260713-reading-theme.active.md",
    ],
)
def test_invalid_design_path_fails(tmp_path, relative_path):
    if relative_path.startswith("app/"):
        (tmp_path / "app").mkdir()
    write_design(tmp_path, relative_path)

    result = run_check(tmp_path)

    assert result.returncode == 1
    assert "invalid design document path" in result.stdout


def test_wip_design_blocks_merge_check(tmp_path):
    (tmp_path / "app").mkdir()
    write_design(tmp_path, "app/20260713-reading-theme.wip.html")

    result = run_check(tmp_path)

    assert result.returncode == 1
    assert "WIP design document cannot be merged" in result.stdout


@pytest.mark.parametrize(
    "body",
    [
        '<html lang="zh-CN"><head><meta charset="utf-8"><title>方案</title></head><body></body></html>',
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>方案</title></head><body></body></html>',
        '<!doctype html><html lang="zh-CN"><head><title>方案</title></head><body></body></html>',
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"></head><body></body></html>',
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>方案</title></head></html>',
    ],
)
def test_invalid_html_structure_fails(tmp_path, body):
    (tmp_path / "app").mkdir()
    write_design(tmp_path, "app/20260713-reading-theme.active.html", body)

    result = run_check(tmp_path)

    assert result.returncode == 1
    assert "invalid HTML structure" in result.stdout


@pytest.mark.parametrize(
    "resource",
    [
        '<script src="https://cdn.example.com/app.js"></script>',
        '<link rel="stylesheet" href="/assets/design.css">',
        '<img src="../images/diagram.png" alt="架构图">',
        '<iframe src="//example.com/embed"></iframe>',
        '<svg><image href="https://example.com/diagram.png"></image></svg>',
        '<svg><use href="https://example.com/icons.svg#check"></use></svg>',
        '<style>@import url("https://example.com/theme.css");</style>',
        '<style>.hero { background: url("./background.png"); }</style>',
    ],
)
def test_external_resource_fails(tmp_path, resource):
    (tmp_path / "app").mkdir()
    write_design(tmp_path, "app/20260713-reading-theme.active.html", html_with(resource))

    result = run_check(tmp_path)

    assert result.returncode == 1
    assert "external resource is not allowed" in result.stdout


def test_external_requirement_link_is_allowed(tmp_path):
    (tmp_path / "app").mkdir()
    write_design(
        tmp_path,
        "app/20260713-reading-theme.active.html",
        html_with('<a href="https://github.com/talebook/talebook/issues/1">需求来源</a>'),
    )

    result = run_check(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
