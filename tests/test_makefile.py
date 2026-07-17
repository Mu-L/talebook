from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"


def test_coverage_targets_report_current_webserver_package():
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert 'coverage report --include "webserver/*"' in makefile
    assert 'coverage html -d ".htmlcov" --include "webserver/*"' in makefile
    assert '"*talebook*"' not in makefile
