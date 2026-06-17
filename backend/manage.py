#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: list[str]):
    """Run shell command safely"""
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


def ensure_postgres():
    """Start PostgreSQL if not already running."""
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("PostgreSQL is already running.")
            return

        print("Starting PostgreSQL...")
        subprocess.run(
            ["pg_ctlcluster", "18", "main", "start"],
            check=True,
        )
        print("PostgreSQL started.")
    except subprocess.CalledProcessError:
        print("WARNING: Could not start PostgreSQL automatically.")
        print("  Run manually: sudo pg_ctlcluster 18 main start")
        print("  Sessions will not persist until PostgreSQL is running.")
    except FileNotFoundError:
        print("WARNING: pg_isready not found. Skipping PostgreSQL check.")


def _latest_revision_file() -> Path | None:
    versions_dir = Path(__file__).resolve().parent / "alembic" / "versions"
    if not versions_dir.exists():
        return None

    candidates = [p for p in versions_dir.iterdir() if p.suffix == ".py"]
    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def _is_empty_revision(file_path: Path) -> bool:
    content = file_path.read_text(encoding="utf-8")
    return "op." not in content and "pass" in content


def makemigrations():
    print("Generating migrations...")
    run_command(["alembic", "revision", "--autogenerate", "-m", "auto migration"])
    latest = _latest_revision_file()
    if latest and _is_empty_revision(latest):
        latest.unlink()
        print("No schema changes detected. No migration created.")
        return


def migrate():
    print("Applying migrations...")
    run_command(["alembic", "upgrade", "head"])


def runserver():
    ensure_postgres()
    print("Starting FastAPI server...")
    run_command([
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


def main():
    if len(sys.argv) < 2:
        print("""
Usage:
  python manage.py makemigrations
  python manage.py migrate
  python manage.py runserver
""")
        sys.exit(1)

    command = sys.argv[1]

    if command == "makemigrations":
        makemigrations()
    elif command == "migrate":
        migrate()
    elif command == "runserver":
        runserver()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()