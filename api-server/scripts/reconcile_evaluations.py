"""Explicit, offline reconciliation of duplicate legacy evaluations.

Before applying #17's unique-homework migration:
  cd api-server
  python scripts/reconcile_evaluations.py --audit --output duplicate-plan.json
  # Edit each keep_id after reviewing original records and making a DB backup.
  # Stop the application, workers and any other writers first.
  python scripts/reconcile_evaluations.py --plan duplicate-plan.json \\
      --apply --backup-confirmed --writers-stopped
  alembic upgrade head

Default audit is read-only. Apply archives all non-keeper rows in the same DB
transaction as their deletion; it never chooses keepers automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import engine  # noqa: E402
from app.services.evaluation_reconciliation import (  # noqa: E402
    audit_duplicates, reconcile_duplicates,
)


def _write_json_atomically(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="read-only inspection (default)")
    parser.add_argument("--output", type=Path, help="write editable audit JSON")
    parser.add_argument("--plan", type=Path, help="an audited plan with every keep_id filled")
    parser.add_argument("--apply", action="store_true", help="archive and remove approved duplicates")
    parser.add_argument("--backup-confirmed", action="store_true",
                        help="operator confirms a restorable DB backup exists")
    parser.add_argument("--writers-stopped", action="store_true",
                        help="operator confirms application and all writers are stopped")
    args = parser.parse_args(argv)

    if args.apply:
        if not (args.plan and args.backup_confirmed and args.writers_stopped):
            parser.error("--apply requires --plan, --backup-confirmed, --writers-stopped")
        if args.output or args.audit:
            parser.error("--apply cannot be combined with --audit/--output")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        summary = reconcile_duplicates(engine, plan)
        print(json.dumps(summary, ensure_ascii=False))
        return 0

    if args.plan:
        parser.error("--plan requires --apply")
    report = audit_duplicates(engine)
    if args.output:
        _write_json_atomically(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["groups"] else 0


if __name__ == "__main__":
    sys.exit(main())
