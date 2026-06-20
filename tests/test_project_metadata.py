from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def test_pyproject_declares_installable_python_package():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    project = pyproject["project"]
    assert project["name"] == "agile-ai-htb"
    assert project["requires-python"] == ">=3.11"

    dependencies = set(project["dependencies"])
    assert {
        "fastapi",
        "uvicorn",
        "pydantic",
        "pyyaml",
        "jinja2",
        "python-multipart",
    }.issubset(dependencies)
    assert "litellm" not in dependencies

    test_dependencies = set(pyproject["project"]["optional-dependencies"]["test"])
    assert {"pytest", "pytest-asyncio", "httpx"}.issubset(test_dependencies)

    pytest_options = pyproject["tool"]["pytest"]["ini_options"]
    assert pytest_options["testpaths"] == ["tests"]
    assert pytest_options["pythonpath"] == ["src"]


def test_package_imports_from_src_layout():
    sys.path.insert(0, str(SRC))
    try:
        import agile_ai_htb
    finally:
        sys.path.remove(str(SRC))

    assert agile_ai_htb.__version__ == "0.1.0"
