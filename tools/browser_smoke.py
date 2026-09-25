"""Real Chromium smoke check for inventory, clues, SSE and saved-game reload.

Requires playwright and its Chromium browser. Uses isolated local JSON saves.
"""
import json
import os
from pathlib import Path
import sys
import threading
from uuid import uuid4
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    output = Path('.runtime') / ('browser-' + uuid4().hex)
    output.mkdir(parents=True)
    os.environ['DATA_DIR'] = str(output.resolve() / 'data')
    os.environ['CTHULHU_DATABASE_URL'] = ''
    from app import create_app
    from werkzeug.serving import make_server
    from playwright.sync_api import sync_playwright, expect
    app = create_app({'DATA_DIR': os.environ['DATA_DIR'], 'DATABASE_URL': ''})
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    errors = []
    checks = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#investigator-name').fill('Browser audit')
            page.locator('.start-btn').click()
            expect(page.locator('#game-screen')).to_be_visible()
            expect(page.locator('#turn-counter')).to_have_text('1')
            page.get_by_text('[inventory & clues]', exact=True).click()
            expect(page.locator('#inventory-content')).to_contain_text('empty')
            expect(page.locator('#discoveries-content')).to_contain_text('No confirmed')
            page.get_by_role('button', name='take flashlight', exact=True).click()
            expect(page.locator('#turn-counter')).to_have_text('2')
            checks.append('SSE pickup through actual UI')
            page.locator('#action-input').fill('inventario')
            page.locator('#action-input').press('Enter')
            expect(page.locator('#sheet-display')).to_be_visible()
            expect(page.locator('#inventory-content')).to_contain_text('Flashlight')
            expect(page.locator('#turn-counter')).to_have_text('2')
            checks.append('Spanish inventory query costs no turn')
            page.get_by_role('button', name='search for the keeper key', exact=True).click()
            expect(page.locator('#dice-area')).to_be_visible()
            expect(page.locator('#dice-label')).to_contain_text('Normal')
            page.get_by_text('[inventory & clues]', exact=True).click()
            expect(page.locator('#inventory-content')).to_contain_text('Flashlight')
            for button in page.locator('#available-actions button').all():
                expect(button).to_be_disabled()
            checks.append('Inventory accessible while dice pending; actions disabled')
            page.reload()
            expect(page.locator('#game-screen')).to_be_visible()
            expect(page.locator('#dice-area')).to_be_visible()
            expect(page.locator('#turn-counter')).to_have_text('3')
            checks.append('Reload restores existing game and pending die')
            page.get_by_text('[inventory & clues]', exact=True).click()
            expect(page.locator('#inventory-content')).to_contain_text('Flashlight')
            # Fixed die only in this UI check; live route audits use real dice.
            with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
                page.locator('#pixel-die').click()
                expect(page.locator('#dice-area')).to_be_hidden(timeout=10000)
            page.get_by_text('[inventory & clues]', exact=True).click()
            expect(page.locator('#discoveries-content')).to_contain_text('take keeper key')
            expect(page.get_by_role('button', name='take keeper key', exact=True)).to_be_enabled()
            checks.append('Successful die shows confirmed clue and unlocks pickup')
            page.reload()
            expect(page.locator('#game-screen')).to_be_visible()
            page.get_by_text('[inventory & clues]', exact=True).click()
            expect(page.locator('#discoveries-content')).to_contain_text('take keeper key')
            checks.append('Reload preserves confirmed clue')
            page.screenshot(path=str(output / 'inventory-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(output / 'inventory-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            checks.append('Mobile panel fits viewport')
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        thread.join(5)
        for gs in app.extensions['cthulhu'].sessions.values():
            if gs.engine:
                gs.engine.close()
    (output / 'report.json').write_text(json.dumps({'checks': checks, 'errors': errors}, indent=2))
    print(output)
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
