from __future__ import annotations

import os
import subprocess
import threading
from typing import Any, Callable

from foreman_ai_hq.worker_adapters import CommandPlan, SUBPROCESS_RUNNER_TIMEOUT_SECONDS


def streaming_runner(
    plan: CommandPlan,
    on_event: Callable[[str], None],
) -> subprocess.CompletedProcess[str]:
    """Run a Worker command, forwarding stdout lines without changing final output."""
    timeout_seconds = _timeout_seconds(plan)
    try:
        process = subprocess.Popen(
            plan.command,
            cwd=str(plan.cwd) if plan.cwd else None,
            env={**os.environ, **plan.env},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        command_name = plan.command[0] if plan.command else "<empty>"
        error_text = getattr(exc, "strerror", None) or str(exc)
        return subprocess.CompletedProcess(
            plan.command,
            127,
            stdout="",
            stderr=f"Failed to launch command {command_name!r}: {type(exc).__name__}: {error_text}",
        )

    stdout: list[str] = []
    stderr: list[str] = []
    timed_out = threading.Event()

    def read_stderr() -> None:
        assert process.stderr is not None
        stderr.extend(process.stderr)

    def kill_on_timeout() -> None:
        timed_out.set()
        process.kill()

    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()
    timer = threading.Timer(timeout_seconds, kill_on_timeout)
    timer.start()
    try:
        assert process.stdout is not None
        for line in process.stdout:
            stdout.append(line)
            try:
                on_event(line)
            except Exception:
                # Stream display is additive evidence; it cannot fail a Worker Run.
                pass
        process.wait()
    finally:
        timer.cancel()
        stderr_thread.join()

    stdout_text = "".join(stdout)
    stderr_text = "".join(stderr)
    if timed_out.is_set():
        timeout_message = f"Command timed out after {timeout_seconds} seconds."
        stderr_text = f"{stderr_text}\n{timeout_message}" if stderr_text else timeout_message
        return subprocess.CompletedProcess(plan.command, 124, stdout=stdout_text, stderr=stderr_text)
    return subprocess.CompletedProcess(plan.command, process.returncode, stdout=stdout_text, stderr=stderr_text)


def _timeout_seconds(plan: CommandPlan) -> int:
    candidate: Any = plan.metadata.get("timeout_seconds")
    try:
        seconds = int(candidate)
    except (TypeError, ValueError):
        return SUBPROCESS_RUNNER_TIMEOUT_SECONDS
    return seconds if seconds > 0 else SUBPROCESS_RUNNER_TIMEOUT_SECONDS
