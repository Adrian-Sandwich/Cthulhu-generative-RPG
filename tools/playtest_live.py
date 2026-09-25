"""Bounded live-model route audit through Flask HTTP handlers, with real dice.

Run with LLM_MODEL configured. Writes isolated saves and an incremental transcript.
This is a scripted route audit, not a blind usability or browser test.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--pace', type=float, default=3.2,
                        help='Minimum seconds between requests, respecting the action rate limit')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ['DATA_DIR'] = str(args.output.resolve() / 'data')
    os.environ['CTHULHU_DATABASE_URL'] = ''
    os.environ['ENABLE_ENTITY_GRAPH'] = '0'
    os.environ['ENABLE_IMAGES'] = '0'
    from app import create_app
    from core.llm_client import LLMClient, resolve_llm_config
    cfg = resolve_llm_config()
    report = {'model': cfg['model'], 'provider': cfg['provider'], 'runs': []}

    def flush():
        (args.output / 'transcript.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    for ending in ('escape', 'victory', 'destruction'):
        app = create_app({'DATA_DIR': str(args.output.resolve() / ending), 'DATABASE_URL': ''})
        client = app.test_client()
        run = {'target': ending, 'events': [], 'outcome': 'incomplete'}
        report['runs'].append(run)
        previous_request = 0.0

        def request(path, payload=None):
            nonlocal previous_request
            time.sleep(max(0, args.pace - (time.monotonic() - previous_request)))
            previous_request = time.monotonic()
            start = time.monotonic()
            before = LLMClient.degraded_turns
            response = client.post(path, json=payload)
            body = response.get_json()
            run['events'].append({'path': path, 'input': payload,
                                  'status': response.status_code, 'response': body,
                                  'seconds': round(time.monotonic()-start, 2),
                                  'fallbacks': LLMClient.degraded_turns-before})
            flush()
            print(ending, path, (payload or {}).get('action', ''), response.status_code,
                  run['events'][-1]['seconds'], flush=True)
            return response.status_code, body

        _, started = request('/api/game/start', {'name': 'Live route audit', 'archetype': 'scholar'})
        gs = next(iter(app.extensions['cthulhu'].sessions.values()))

        def action(text):
            status, body = request('/api/game/action', {'action': text, 'action_id': uuid4().hex,
                                                       'game_id': started['game_id']})
            if status != 200:
                raise RuntimeError(f'{text}: HTTP {status}: {body.get("error")}')
            if run['events'][-1]['fallbacks']:
                raise RuntimeError('Model degraded to fallback; live narration was not validated')
            if body.get('pending_roll'):
                status, body = request('/api/game/roll')
                if status != 200:
                    raise RuntimeError(f'Roll failed: HTTP {status}')
                if run['events'][-1]['fallbacks']:
                    raise RuntimeError('Roll narration degraded to fallback')
            if gs.engine.state.active_combat:
                raise RuntimeError('Combat interrupted scripted route; manual play required')

        def objective(key, text):
            text = gs.engine.adventure_config.investigations.get(key, {}).get('actions', [text])[0]
            for _ in range(args.attempts):
                action(text)
                if key in gs.engine.state.ending_objectives:
                    return
                if gs.engine.state.ending_reached:
                    break
            raise RuntimeError(f'Objective not earned within attempt budget: {key}')

        try:
            action('I listen to the wind outside the lighthouse')
            if ending == 'escape':
                objective('safe_route', 'I navigate the coast to find a safe route off the island')
                action('leave the island')
            else:
                if ending == 'victory':
                    objective('shore_search', 'I search the exterior for the keeper key')
                    action('take keeper key')
                    action("go to Keeper's Quarters")
                    objective('keeper_evidence', 'I search the quarters for evidence')
                    action('go to exterior')
                for move in ('interior', 'ground floor', 'basement'):
                    action('go to ' + move)
                objective('foundation_survey', 'I investigate the foundations')
                if ending == 'destruction':
                    action('take dynamite')
                for move in ('ground floor', 'interior', 'stairs', 'upper level', 'lantern room'):
                    action('go to ' + move)
                objective('beacon_symbols', 'I interpret the occult symbols around the beacon')
                for move in ('upper level', 'stairs', 'interior', 'ground floor', 'basement', 'hidden chamber'):
                    action('go to ' + move)
                objective('fissure_studied', 'I interpret the occult symbols around the fissure')
                if ending == 'destruction':
                    action('go to basement')
                    action('detonate the dynamite')
                else:
                    action('embrace the transformation')
            run['outcome'] = 'reached' if gs.engine.state.ending_reached == ending else 'wrong_ending'
        except RuntimeError as exc:
            run['outcome'] = 'blocked'
            run['reason'] = str(exc)
        finally:
            state = gs.engine.state
            run['final'] = {'turn': state.turn, 'location': state.location,
                            'ending': state.ending_reached, 'objectives': state.ending_objectives,
                            'inventory': state.investigator.inventory}
            gs.engine.close()
            flush()
    print(json.dumps([{'target': r['target'], 'outcome': r['outcome'], 'reason': r.get('reason')}
                      for r in report['runs']], indent=2))


if __name__ == '__main__':
    main()
