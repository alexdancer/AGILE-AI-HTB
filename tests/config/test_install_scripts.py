import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "install.sh"
SMOKE_SCRIPT = ROOT / "scripts" / "pipx-install-smoke.sh"


def _write_fake_tool(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\nset -eu\n" + body)
    path.chmod(0o755)


def _run_installer(tmp_path: Path, *, fake_uv: str | None = None, fake_pipx: str | None = None):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "calls.log"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}/bin{os.pathsep}/usr/bin",
        "FAKE_BIN": str(bin_dir),
        "FAKE_LOG": str(log_path),
        "AGILE_AI_HTB_INSTALL_SOURCE": "demo-source",
    }
    if fake_uv is not None:
        _write_fake_tool(bin_dir / "uv", fake_uv)
    if fake_pipx is not None:
        _write_fake_tool(bin_dir / "pipx", fake_pipx)
    result = subprocess.run(
        ["/bin/sh", str(INSTALLER)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result, log_path


def test_install_script_prefers_uv_tool_and_prints_next_steps(tmp_path):
    result, log_path = _run_installer(
        tmp_path,
        fake_uv="""
printf 'uv %s\n' "$*" >> "$FAKE_LOG"
printf '#!/bin/sh\n' > "$FAKE_BIN/htb"
chmod +x "$FAKE_BIN/htb"
""",
        fake_pipx="""
printf 'pipx %s\n' "$*" >> "$FAKE_LOG"
exit 9
""",
    )

    assert result.returncode == 0, result.stderr
    assert "Using uv tool install from: demo-source" in result.stdout
    assert "Next: htb init" in result.stdout
    assert "Then: htb serve" in result.stdout
    assert "uv tool install --force demo-source" in log_path.read_text()
    assert "pipx" not in log_path.read_text()


def test_install_script_falls_back_to_pipx(tmp_path):
    result, log_path = _run_installer(
        tmp_path,
        fake_pipx="""
printf 'pipx %s\n' "$*" >> "$FAKE_LOG"
printf '#!/bin/sh\n' > "$FAKE_BIN/htb"
chmod +x "$FAKE_BIN/htb"
""",
    )

    assert result.returncode == 0, result.stderr
    assert "Using pipx install from: demo-source" in result.stdout
    assert "Next: htb init" in result.stdout
    assert "pipx install --force demo-source" in log_path.read_text()


def test_install_script_reports_path_remediation_when_htb_missing(tmp_path):
    result, _ = _run_installer(
        tmp_path,
        fake_uv="""
printf 'uv %s\n' "$*" >> "$FAKE_LOG"
""",
    )

    assert result.returncode == 1
    assert "'htb' is not visible on PATH" in result.stderr
    assert "uv tool update-shell" in result.stderr
    assert "htb init" in result.stderr


def test_install_script_reports_missing_installers_without_secrets(tmp_path):
    result, _ = _run_installer(tmp_path)

    assert result.returncode == 1
    assert "Install uv or pipx first" in result.stderr
    assert "API" not in result.stderr
    assert "token" not in result.stderr.lower()


def test_disposable_pipx_smoke_script_uses_temp_pipx_environment():
    content = SMOKE_SCRIPT.read_text()

    assert "PIPX_HOME=\"$TMP_DIR/pipx-home\"" in content
    assert "PIPX_BIN_DIR=\"$TMP_DIR/bin\"" in content
    assert "pipx install --force \"$ROOT_DIR\"" in content
    assert "htb --help" in content
    assert "htb init" in content
    assert "test -s .htb/guardrails.yaml" in content
    assert "rm -rf \"$TMP_DIR\"" in content
