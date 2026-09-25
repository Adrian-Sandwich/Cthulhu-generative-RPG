"""Explicit schema setup and non-destructive import of existing JSON saves.

Set CTHULHU_DATABASE_URL, then run from the repository root:
  python tools/migrate_postgres.py init
  python tools/migrate_postgres.py import-json --data-dir /data
  python tools/migrate_postgres.py import-json --data-dir /data --apply
Stop all file-backed writers before the final import and backend switch.
"""

import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.generative_save import GenerativeSave, saves_dir
from core.postgres_store import PostgresStore
from core.state import GameState, InvestigatorState
from dataclasses import fields, MISSING


def validate_payload(payload):
    if not isinstance(payload['metadata']['model'], str):
        raise ValueError('Invalid model')
    state = payload['game_state']
    investigator = state['investigator']
    for cls, values in [(GameState, state), (InvestigatorState, investigator)]:
        if not isinstance(values, dict):
            raise ValueError('Invalid game state')
        required = {f.name for f in fields(cls) if f.default is MISSING and f.default_factory is MISSING}
        if not required <= values.keys():
            raise ValueError('Incomplete game state')
    if not isinstance(state['turn'], int) or not isinstance(state['narrative'], list):
        raise ValueError('Invalid turn history')


def import_saves(store, data_dir, apply=False):
    counts = {'imported': 0, 'would_import': 0, 'unchanged': 0, 'conflicts': 0, 'invalid': 0}
    for path in sorted(saves_dir(data_dir).glob('*.json')):
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            sid = payload['metadata']['session_id']
            if not isinstance(sid, str) or GenerativeSave._safe_id(sid) != sid or path.stem != sid:
                raise ValueError('Invalid session identity')
            validate_payload(payload)
        except (ValueError, KeyError, TypeError):
            counts['invalid'] += 1
            continue
        with store.locked(sid) as owner:
            try:
                existing = owner.read(sid)
            except FileNotFoundError:
                existing = None
            if existing is not None:
                counts['unchanged' if existing == payload else 'conflicts'] += 1
            elif apply:
                owner.write(sid, payload)
                counts['imported'] += 1
            else:
                counts['would_import'] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'import-json'])
    parser.add_argument('--data-dir', default=os.environ.get('DATA_DIR', '.'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    dsn = os.environ.get('CTHULHU_DATABASE_URL')
    if not dsn:
        parser.error('Set CTHULHU_DATABASE_URL before running this command')
    store = PostgresStore(dsn)
    if args.command == 'init':
        store.initialize()
        print('PostgreSQL schema ready.')
        return 0
    counts = import_saves(store, args.data_dir, args.apply)
    print(json.dumps(counts))
    return 1 if counts['invalid'] or counts['conflicts'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
