#!/usr/bin/env python3
"""Run database migrations."""
import sys

from alembic import command
from alembic.config import Config


def migrate():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully")


def create_migration(message: str):
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=True)
    print(f"Migration '{message}' created successfully")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        if len(sys.argv) < 3:
            print("Usage: python migrate.py create <message>")
            sys.exit(1)
        create_migration(sys.argv[2])
    else:
        migrate()
