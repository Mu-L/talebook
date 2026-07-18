import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_TOOLS = {"flake8", "pytest", "pytest-cov", "ruff"}


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def dependency_name(requirement: str) -> str:
    return re.split(r"[<>=!~\[]", requirement, maxsplit=1)[0].strip().lower()


def requirement_names(name: str) -> set[str]:
    names = set()
    for raw_line in read(name).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(dependency_name(line))
    return names


def docker_stage(name: str) -> str:
    dockerfile = read("Dockerfile")
    stages = list(re.finditer(r"^FROM\s+\S+\s+AS\s+(\S+)\s*$", dockerfile, re.MULTILINE | re.IGNORECASE))
    for index, match in enumerate(stages):
        if match.group(1).lower() != name.lower():
            continue
        end = stages[index + 1].start() if index + 1 < len(stages) else len(dockerfile)
        return dockerfile[match.start() : end]
    raise AssertionError(f"Docker stage not found: {name}")


def dependency_names(dependencies: list[str]) -> set[str]:
    return {dependency_name(dependency) for dependency in dependencies}


def test_server_uses_slim_base_without_vim_installation():
    server = docker_stage("server")

    assert server.startswith("FROM talebook/talebook-base:slim-v8.5.0 AS server")
    assert not re.search(r"\bvim\b", server)


def test_base_image_source_and_publisher_are_externalized():
    assert not (ROOT / "Dockerfile.base").exists()
    assert not (ROOT / ".github" / "workflows" / "build-base.yml").exists()
    assert "github.com/talebook/talebook-base" in read("Dockerfile")


def test_test_tools_are_isolated_from_production_requirements():
    production = requirement_names("requirements.txt")
    testing = requirement_names("requirements-test.txt")

    assert production.isdisjoint(TEST_TOOLS)
    assert TEST_TOOLS <= testing


def test_test_stage_installs_the_test_requirements_only_after_server():
    server = docker_stage("server")
    test = docker_stage("test")

    assert "requirements-test.txt" not in server
    assert "COPY requirements-test.txt /tmp/" in test
    assert "pip install -r /tmp/requirements-test.txt" in test


def test_pyproject_declares_test_tools_as_optional_dependencies():
    with (ROOT / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)["project"]

    production = dependency_names(project["dependencies"])
    testing = dependency_names(project["optional-dependencies"]["test"])

    assert production.isdisjoint(TEST_TOOLS)
    assert TEST_TOOLS <= testing


def test_make_init_installs_production_and_test_requirements():
    makefile = read("Makefile")
    init = re.search(r"^init:\n(?P<body>(?:\t.*\n)+)", makefile, re.MULTILINE)

    assert init is not None
    assert "-r requirements.txt" in init.group("body")
    assert "-r requirements-test.txt" in init.group("body")
