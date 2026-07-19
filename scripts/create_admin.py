"""Create a glossary administrator interactively without storing a plaintext password."""

from getpass import getpass
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.admin.database import get_admin_database


def main() -> None:
    username = input("Administrator username: ").strip()
    password = getpass("Password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    try:
        admin = get_admin_database().create_admin(username, password)
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise SystemExit(f"Could not create administrator: {exc}") from exc
    print(f"Administrator created: {admin['username']}")


if __name__ == "__main__":
    main()
