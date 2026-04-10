#!/usr/bin/env python3

import sys
import subprocess


def run_command(command: list[str]):
    """Run shell command safely"""
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


def makemigrations():
    print("Generating migrations...")
    run_command(["alembic", "revision", "--autogenerate", "-m", "auto migration"])


def migrate():
    print("Applying migrations...")
    run_command(["alembic", "upgrade", "head"])


def runserver():
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