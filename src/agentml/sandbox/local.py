"""Local sandbox — executes code via subprocess in a temp directory."""

import asyncio
import tempfile
import time
from pathlib import Path

from agentml.interfaces.sandbox import ExecutionResult, Sandbox


class LocalSandbox(Sandbox):
    """Sandbox that executes code in a local subprocess."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._workdir: Path | None = None

    async def execute(self, code: str, *, language: str = "python") -> ExecutionResult:
        """Execute code in a subprocess."""
        if language != "python":
            return ExecutionResult(stderr=f"Unsupported language: {language}", exit_code=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "script.py"
            script_path.write_text(code)

            start = time.monotonic()
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python",
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                duration_ms = (time.monotonic() - start) * 1000

                return ExecutionResult(
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    exit_code=proc.returncode or 0,
                    duration_ms=duration_ms,
                )
            except TimeoutError:
                duration_ms = (time.monotonic() - start) * 1000
                return ExecutionResult(
                    stderr="Execution timed out",
                    exit_code=-1,
                    duration_ms=duration_ms,
                )

    async def install_packages(self, packages: list[str]) -> ExecutionResult:
        """Install packages using pip."""
        proc = await asyncio.create_subprocess_exec(
            "pip",
            "install",
            *packages,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return ExecutionResult(
            stdout=stdout.decode(),
            stderr=stderr.decode(),
            exit_code=proc.returncode or 0,
        )

    async def cleanup(self) -> None:
        """No persistent resources to clean up in local sandbox."""
