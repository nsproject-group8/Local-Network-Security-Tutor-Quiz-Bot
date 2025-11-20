import shutil
from pathlib import Path
import datetime
import sys

ROOT = Path(__file__).resolve().parents[2]
CHROMA_DB = ROOT / 'data' / 'chroma_db' / 'chroma.sqlite3'


def backup_and_reset():
    if not CHROMA_DB.exists():
        print(f"No chroma DB found at {CHROMA_DB}")
        return

    backup_dir = ROOT / 'data' / f'chroma_db_backup_{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}'
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(CHROMA_DB.parent, backup_dir)
    print(f"Backed up chroma DB to: {backup_dir}")

    # Remove sqlite file so chromadb can recreate it with the correct schema
    for p in (CHROMA_DB,):
        if p.exists():
            p.unlink()
            print(f"Removed {p}")

    print("Chroma DB reset complete. Re-start the backend to recreate the DB.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: manage_chroma.py backup-reset")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'backup-reset':
        backup_and_reset()
    else:
        print("Unknown command")
