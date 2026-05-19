"""Reset the local demo SQLite database and reseed demo data."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.database import get_db_path  # noqa: E402
from scripts.seed_demo_data import seed_demo_data  # noqa: E402


def reset_demo_database(force: bool = False) -> None:
    db_path = get_db_path()
    sidecars = [db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")]
    if not force:
        answer = input(f"This will delete the demo database at {db_path}. Continue? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Reset cancelled.")
            return
    for path in sidecars:
        if path.exists():
            path.unlink()
            print(f"Removed {path}")
    seed_demo_data()
    print("Demo database reset complete.")


if __name__ == "__main__":
    reset_demo_database(force="--force" in sys.argv)
