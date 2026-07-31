"""GARUDA Launcher - Development mode command."""

import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

from launcher.config import PathConfig, ServerConfig, AppInfo
from launcher.style import Style, ok, fail, info, header, banner, step
from launcher.logging import log_startup, log_shutdown, launcher_logger
from launcher.process import register_process, unregister_process, is_process_running, kill_existing_processes
from launcher.utils import ensure_directories, run_command


class ManagedProcess:
    """Wrapper around a subprocess with output forwarding."""

    def __init__(self, name: str, cmd: list[str], cwd: Path):
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.process: subprocess.Popen | None = None
        self._output_thread = None
        self._stop_output = False

    def start(self) -> None:
        """Start the subprocess."""
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        self.process = subprocess.Popen(
            self.cmd,
            cwd=str(self.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=flags,
        )
        register_process(self.name, self.process.pid)

        import threading
        self._stop_output = False
        self._output_thread = threading.Thread(target=self._forward_output, daemon=True)
        self._output_thread.start()

    def _forward_output(self) -> None:
        """Forward subprocess output to console."""
        if self.process is None or self.process.stdout is None:
            return
        prefix = f"  [{self.name:>9}] "
        try:
            for line in self.process.stdout:
                if self._stop_output:
                    break
                line = line.rstrip()
                if line:
                    print(f"{prefix}{line}")
        except Exception:
            pass

    def is_running(self) -> bool:
        """Check if process is alive."""
        return self.process is not None and self.process.poll() is None

    def shutdown(self, timeout: float = 10.0) -> None:
        """Gracefully terminate."""
        self._stop_output = True
        if self.process is None:
            return
        if self.process.poll() is not None:
            unregister_process(self.name)
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        except Exception:
            pass
        unregister_process(self.name)


def wait_for_backend(timeout: float = ServerConfig.HEALTH_TIMEOUT) -> bool:
    """Poll health endpoint until ready."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(ServerConfig.HEALTH_ENDPOINT, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError, ConnectionError):
            pass
        time.sleep(ServerConfig.HEALTH_INTERVAL)
    return False


def start_backend() -> ManagedProcess:
    """Start the FastAPI backend."""
    cmd = [
        str(PathConfig.BACKEND_PYTHON),
        "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", ServerConfig.BACKEND_HOST,
        "--port", str(ServerConfig.BACKEND_PORT),
    ]
    proc = ManagedProcess("backend", cmd, PathConfig.BACKEND_DIR)
    proc.start()
    return proc


def start_frontend() -> ManagedProcess:
    """Start the Vite dev server."""
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm, "run", "dev"]
    proc = ManagedProcess("frontend", cmd, PathConfig.FRONTEND_DIR)
    proc.start()
    return proc


def monitor(backend: ManagedProcess, frontend: ManagedProcess) -> None:
    """Block and monitor both processes."""
    try:
        while True:
            if not backend.is_running():
                print(f"\n{fail('Backend process exited unexpectedly')}")
                break
            if not frontend.is_running():
                print(f"\n{fail('Frontend process exited unexpectedly')}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def cmd_dev() -> int:
    """Run GARUDA in development mode."""
    print(banner(f"GARUDA Development Server v{AppInfo.VERSION}"))
    log_startup("Development server starting")

    print(header("Phase 1: Environment"))
    print(info("Killing any existing GARUDA processes..."))
    kill_existing_processes()

    print(header("Phase 2: Setup"))
    print(info("Creating storage directories..."))
    ensure_directories()

    print(header("Phase 3: Database"))
    print(info("Running Alembic migrations..."))
    alembic_ini = PathConfig.ALEMBIC_INI
    if alembic_ini.exists() and PathConfig.BACKEND_PYTHON.exists():
        code, out = run_command(
            [str(PathConfig.BACKEND_PYTHON), "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=str(PathConfig.BACKEND_DIR),
            timeout=60,
        )
        if code == 0:
            print(ok("Migrations applied"))
        else:
            print(fail(f"Migration failed: {out[:200]}"))
            return 1
    else:
        print(fail("Cannot run migrations (alembic.ini or Python not found)"))
        return 1

    print(header("Phase 4: Backend"))
    print(info(f"Starting FastAPI on port {ServerConfig.BACKEND_PORT}..."))
    backend = start_backend()

    print(info("Waiting for backend health check..."))
    if not wait_for_backend():
        print(fail("Backend failed to respond"))
        backend.shutdown()
        return 1
    print(ok(f"Backend ready at http://{ServerConfig.BACKEND_HOST}:{ServerConfig.BACKEND_PORT}"))

    print(header("Phase 5: Frontend"))
    print(info("Starting Vite dev server..."))
    frontend = start_frontend()

    print(info("Waiting for frontend..."))
    time.sleep(3)
    print(ok(f"Frontend ready at {ServerConfig.FRONTEND_URL}"))

    print(header("GARUDA Ready"))
    print(f"\n  {Style.BOLD}Services:{Style.RESET}")
    print(f"    Backend  : {Style.GREEN}http://localhost:{ServerConfig.BACKEND_PORT}{Style.RESET}")
    print(f"    Frontend : {Style.GREEN}{ServerConfig.FRONTEND_URL}{Style.RESET}")
    print(f"    API Docs : {Style.GREEN}http://localhost:{ServerConfig.BACKEND_PORT}/docs{Style.RESET}")
    print(f"\n  {Style.DIM}Press Ctrl+C to stop all services{Style.RESET}\n")

    log_startup("Development server started successfully")
    monitor(backend, frontend)

    print(info("Shutting down..."))
    log_shutdown("Development server shutting down")
    backend.shutdown()
    frontend.shutdown()
    print(ok("All services stopped"))
    log_shutdown("Development server stopped")
    return 0
