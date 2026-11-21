"""Offline inventory/quarantine of orphaned attempt-specific result images.

From api-server/:
  python scripts/maintain_evaluation_overlays.py
  python scripts/maintain_evaluation_overlays.py --min-age-days 45
  # After a manual review, stop the API and every model worker.
  python scripts/maintain_evaluation_overlays.py --apply --writers-stopped \\
    --quarantine-dir ../private-overlay-quarantine

The program NEVER permanently deletes files. The quarantine directory must be
outside /uploads, on the same filesystem, and accessible only to operators.
Its manifest.jsonl records the original relative paths for manual restoration.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.services.evaluation_overlay_maintenance import (  # noqa: E402
    DEFAULT_MIN_AGE_SECONDS, find_orphan_overlays, quarantine_orphan_overlays,
)
from app.services.file_storage_service import FileStorageService  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="move candidates into quarantine")
    parser.add_argument("--writers-stopped", action="store_true",
                        help="confirm no API, worker or storage writer remains active")
    parser.add_argument("--quarantine-dir", type=Path,
                        help="required for --apply; outside the public storage root")
    parser.add_argument("--min-age-days", type=int, default=30,
                        help="minimum untouched age, default 30 days")
    args = parser.parse_args(argv)
    if args.min_age_days < 1:
        parser.error("--min-age-days must be >= 1")
    if args.apply and (not args.writers_stopped or args.quarantine_dir is None):
        parser.error("--apply requires --writers-stopped and --quarantine-dir")
    if not args.apply and (args.writers_stopped or args.quarantine_dir):
        parser.error("--writers-stopped and --quarantine-dir require --apply")

    root = FileStorageService.get_storage_root()
    minimum = args.min_age_days * 24 * 3600
    if args.apply:
        moved = quarantine_orphan_overlays(
            SessionLocal, root, args.quarantine_dir,
            writers_stopped=args.writers_stopped, min_age_seconds=minimum,
        )
        print(json.dumps({"quarantined": len(moved), "files": moved},
                         ensure_ascii=False, indent=2))
    else:
        with SessionLocal() as db:
            candidates = find_orphan_overlays(db, root, min_age_seconds=minimum)
        print(json.dumps({
            "mode": "dry-run", "threshold_days": args.min_age_days,
            "eligible": len(candidates), "files": candidates,
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
