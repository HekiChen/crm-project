"""
Entrypoint to start backend FastAPI services for CRM project.
Run: python run.py
"""
import sys
from pathlib import Path
import uvicorn

# Ensure the `backend` directory is on sys.path so imports like `import app.*` work
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Provide minimal defaults for required env vars when running from project root.
# This makes `python run.py` work for local development without extra setup.
# If you have a configured `.env` or real DATABASE_URL, that will take precedence.
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

# Decide whether to use reload mode. When reload is enabled, uvicorn requires an
# import string (e.g. 'app.main:app') so it can re-import the application in the
# child process — passing the app object with reload=True triggers a warning.
RELOAD = True


def _start_with_reload():
    # Ensure the backend directory is available to the subprocess via PYTHONPATH
    pythonpath = os.environ.get("PYTHONPATH", "")
    backend_str = str(BACKEND)
    if backend_str not in pythonpath.split(os.pathsep):
        os.environ["PYTHONPATH"] = backend_str + (os.pathsep + pythonpath if pythonpath else "")

    # Provide the import string uvicorn will use to locate the app in reload workers
    import_string = "app.main:app"
    # Change working directory to backend so pydantic Settings reads backend/.env
    os.chdir(backend_str)
    uvicorn.run(
        import_string,
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


def _start_without_reload():
    # Import the FastAPI app object and pass it directly to uvicorn
    # Ensure backend/.env is read by changing cwd before importing
    os.chdir(str(BACKEND))
    from app.main import app as fastapi_app
    uvicorn.run(
        fastapi_app,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    if RELOAD:
        _start_with_reload()
    else:
        _start_without_reload()
