from importlib.metadata import distribution
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[2]


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


def test_installed_distribution_exposes_htb_console_script():
    dist = distribution("agile-ai-htb")

    entrypoint = next(entry for entry in dist.entry_points if entry.name == "htb")
    assert entrypoint.group == "console_scripts"
    assert entrypoint.value == "agile_ai_htb.cli:main"


def test_pyproject_has_public_cli_package_metadata():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    project = pyproject["project"]

    assert project["readme"] == "README.md"
    assert project["license"] == "MIT"
    assert "token-tracking" in project["keywords"]
    assert project["urls"]["Repository"] == "https://github.com/alexdancer/AI-Harness-Token-Tracker"


def test_pyproject_packages_server_rendered_templates_and_defaults():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["tool"]["setuptools"]["package-data"]["agile_ai_htb"] == [
        "templates/*.html",
        "defaults/*.yaml",
    ]


def test_readme_documents_portal_first_operator_flow():
    readme = (ROOT / "README.md").read_text()

    assert "AGILE-AI-HTB" in readme
    assert "pipx install" in readme
    assert "htb init" in readme
    assert "uv run htb init" not in readme.split("## Docker", 1)[0]
    assert "http://localhost:8000/login" in readme
    assert "htb check" in readme
    removed_command = "seed" + "-demo"
    assert f"htb {removed_command}" not in readme
    assert "docker-compose up" in readme
    assert "uv run pytest" in readme
    assert "provider" in readme.lower()
    assert "env var" in readme.lower()
    assert "PROVIDER_API_KEY" in readme


def test_install_docs_separate_operator_installs_from_contributor_uv_run():
    install_doc = (ROOT / "docs" / "INSTALL.md").read_text()
    getting_started = (ROOT / "docs" / "GETTING_STARTED.md").read_text()

    assert 'pipx install "git+https://github.com/alexdancer/AI-Harness-Token-Tracker.git"' in install_doc
    assert "pipx install agile-ai-htb" in install_doc
    assert "curl -fsSL https://raw.githubusercontent.com/alexdancer/AI-Harness-Token-Tracker/main/install.sh | sh" in install_doc
    assert "Homebrew is planned" in install_doc
    assert "not published yet" in install_doc
    assert "uv run htb ...` is a contributor convenience" in install_doc
    assert "htb init" in getting_started
    assert "uv run htb ...` is a contributor convenience" in getting_started


def test_support_checklist_requests_bare_htb_check_and_install_method():
    checklist = (ROOT / "docs" / "SETUP_SUPPORT_CHECKLIST.md").read_text()
    setup_issue = (ROOT / ".github" / "ISSUE_TEMPLATE" / "setup_support.md").read_text()

    assert "htb check" in checklist
    assert "uv run htb check" in checklist
    assert "Install method" in checklist
    assert "Does `command -v htb` succeed?" in setup_issue
    assert "pipx / curl installer / Homebrew / source checkout / Docker / other" in setup_issue
