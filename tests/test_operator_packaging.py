from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_docker_packaging_files_define_demo_container_contract():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "docker-compose.yml").read_text()
    dockerignore = (ROOT / ".dockerignore").read_text()

    assert "agile-ai-htb" in compose
    assert "agile-ai-htb:local" in compose
    assert "8000:8000" in compose
    assert "TOKEN_TRACKER_DATABASE_PATH=/data/harness.db" in compose
    assert "TOKEN_TRACKER_PORTAL_TOKEN=${TOKEN_TRACKER_PORTAL_TOKEN:-DEMO_PORTAL_TOKEN_2099}" in compose
    assert "python" in compose and "/health" in compose

    assert "COPY guardrails.yaml" in dockerfile
    assert "htb" in dockerfile and "serve" in dockerfile
    assert "8000" in dockerfile

    assert ".venv" in dockerignore
    assert "harness.db" in dockerignore


def test_pyproject_exposes_htb_console_script():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["htb"] == "agile_ai_htb.cli:main"


def test_pyproject_packages_server_rendered_templates():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["tool"]["setuptools"]["package-data"]["agile_ai_htb"] == [
        "templates/*.html"
    ]


def test_readme_documents_portal_first_operator_flow():
    readme = (ROOT / "README.md").read_text()

    assert "AGILE-AI-HTB" in readme
    assert "http://localhost:8000/login" in readme
    assert "htb seed-demo" in readme
    assert "docker compose up" in readme
    assert ".venv/bin/python -m pytest" in readme
    assert "provider" in readme.lower()
    assert "env var" in readme.lower()
    assert "PROVIDER_API_KEY" in readme
