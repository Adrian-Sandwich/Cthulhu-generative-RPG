// Frontend checks for the client scripts — run by tests/test_frontend.py, or
// directly with `node tests/frontend_checks.mjs`.
//
// They are classic <script> tags, not modules, so there is nothing to import.
// These checks read the sources and evaluate the specific pure values they
// assert on. That is deliberate: if a constant is renamed or removed the
// extraction fails loudly here instead of the suite passing on nothing.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { runInNewContext } from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

// The client is five classic scripts sharing one top-level scope (see
// templates/index.html). They are checked as one program, in load order,
// because that is how the browser sees them.
export const CLIENT_FILES = ['state', 'audio', 'ui', 'turn', 'dice']
    .map(n => `static/js/${n}.js`);
const src = CLIENT_FILES
    .map(f => readFileSync(join(root, f), 'utf8'))
    .join('\n');

let failures = 0;
let checks = 0;

function check(label, ok) {
    checks++;
    if (!ok) {
        failures++;
        console.error(`FAIL  ${label}`);
    }
}

function tryExtract(re) {
    const m = src.match(re);
    return m ? m[1] : null;
}

function missing(label) {
    failures++;
    console.error(`FAIL  could not find ${label} in the client scripts — renamed or removed?`);
}

// --- ROLL_REQUEST_RE ---------------------------------------------------------
// Players who don't realise the die is clickable type the request as an action
// ("Lanza el dado"). The client answers those locally instead of spending a
// turn. The risk is over-matching: real actions that open with the same verbs
// must still reach the Keeper, so the adversarial cases below matter more than
// the positive ones.

// Accept either form the constant may legitimately take: a `new RegExp(...)`
// call or a literal. Anything else fails the extraction rather than skipping.
const reSrc =
    tryExtract(/const ROLL_REQUEST_RE =\s*(new RegExp\([\s\S]*?\));/) ??
    tryExtract(/const ROLL_REQUEST_RE =\s*(\/.*\/[gimsuy]*);/);
if (!reSrc) missing('ROLL_REQUEST_RE');
else {
    const ROLL_REQUEST_RE = eval(reSrc);

    const intercepted = [
        'Lanza el dado',
        'lanza el dado!',
        'Lanzar el dado',
        'tira los dados',
        'tirar el dado',
        'echa el dado',
        'avienta el dado',
        '  tira el dado  ',
        'roll the dice',
        'Roll dice',
        'throw the die',
        'cast the dice',
        'roll a d100',
        'ROLL THE DICE.',
    ];

    // Real actions. Over-matching here would silently eat a player's turn,
    // which is worse than the bug this pattern fixes.
    const passedThrough = [
        'lanzo el cuchillo al agua',
        'lanzo una piedra al agua para ver qué pasa',
        'tiro la puerta abajo',
        'tira de la cuerda con fuerza',
        'echa un vistazo por la ventana',
        'examino el dado tallado en la mesa',
        'roll under the table to hide',
        'I throw the lantern at the creature',
        'throw the rope to the lieutenant',
        'search the room',
        'subo las escaleras',
        'talk to Warner about the logs',
    ];

    for (const s of intercepted) {
        check(`should intercept: ${JSON.stringify(s)}`, ROLL_REQUEST_RE.test(s));
    }
    for (const s of passedThrough) {
        check(`should reach the Keeper: ${JSON.stringify(s)}`, !ROLL_REQUEST_RE.test(s));
    }
}

// --- guard wiring ------------------------------------------------------------
// The pattern is useless if submitAction stops consulting it, and the guard has
// to sit before the turn is sent.

const submitBody = src.slice(src.indexOf('async function submitAction'));
const guardAt = submitBody.indexOf('ROLL_REQUEST_RE.test(action)');
const fetchAt = submitBody.indexOf("fetch('/api/game/action/stream'");

check('submitAction consults ROLL_REQUEST_RE', guardAt !== -1);
check('the guard runs before the turn is sent', guardAt !== -1 && fetchAt !== -1 && guardAt < fetchAt);

// --- onboarding affordances --------------------------------------------------
// Both halves of the LAN playtest complaint. Champi didn't know the die was
// clickable; Lysis didn't know how to continue after a roll resolved.

check('first-roll die tip is still wired', /getElementById\('die-tip'\)/.test(src));
check('post-roll suggestions still render', /renderSuggestions\('afterRoll'\)/.test(src));

// Exercise the real recovery functions with a simulated browser and server.
const turnSource = readFileSync(join(root, 'static/js/turn.js'), 'utf8');
const recoverySource = turnSource.slice(turnSource.indexOf('const TURN_STORAGE_KEY'));
for (const mode of ['network-error', 'early-eof', 'not-received', 'reload', 'failed', 'offline']) {
    const calls = [], rendered = [];
    const storage = new Map();
    const command = { action: 'look around', action_id: 'persisted-action-001', game_id: 'game-test-001' };
    if (mode === 'reload') storage.set('lighthouse.pendingTurn', JSON.stringify(command));
    let status = '', boot;
    const input = { value: 'look around', disabled: false, focus() {} };
    let polls = 0;
    const payload = { success: true, turn: 2, action_id: command.action_id };
    const context = {
        document: { getElementById: id => id === 'action-input' ? input : {
            classList: { add() {}, remove() {} },
        } },
        window: { addEventListener: (event, fn) => { boot = fn; } },
        sessionStorage: {
            getItem: key => storage.get(key) || null,
            setItem: (key, value) => storage.set(key, value),
            removeItem: key => storage.delete(key),
        },
        crypto: { getRandomValues: array => array.fill(7) },
        gameId: command.game_id, gameStarted: true,
        ROLL_REQUEST_RE: /never-match/, pendingRoll: null,
        setStatus: text => { status = text; }, hideSuggestions() {}, scrollNarrative() {},
        beginTurn: () => ({ turnEl: { remove() {} }, dmEl: {} }),
        finishTurnUI: result => rendered.push(result),
        refreshGameState: async () => {},
        AbortController, TextDecoder, Uint8Array,
        setTimeout: (fn, ms) => ms === 2000 ? (queueMicrotask(fn), 0) : setTimeout(fn, ms),
        clearTimeout,
        fetch: async (url, options = {}) => {
            calls.push({ url, body: options.body });
            if (mode === 'offline') throw new Error('offline');
            if (url.endsWith('/stream')) {
                if (mode === 'network-error' || mode === 'not-received') throw new Error('disconnected');
                return { ok: true, body: { getReader: () => ({ read: async () => ({ done: true }) }) } };
            }
            if (url.includes('/actions/')) {
                polls++;
                if (mode === 'not-received') return { ok: false, status: 404, json: async () => ({}) };
                const state = polls === 1 ? 'running' : mode === 'failed' ? 'failed' : 'completed';
                return { ok: true, status: 200, json: async () => ({ status: state,
                    result: mode === 'failed' ? { error: 'Turn interrupted' } : payload }) };
            }
            return { ok: true, status: 200, json: async () => payload };
        },
    };
    runInNewContext(recoverySource, context);
    if (mode === 'reload') await boot();
    else await runInNewContext('Promise.all([submitAction({preventDefault() {}}), submitAction({preventDefault() {}})])', context);
    const posts = calls.filter(call => call.body);
    check(`${mode}: double click sends at most one initial command`, calls.filter(c => c.url.endsWith('/stream')).length <= 1);
    if (mode === 'not-received') {
        check('unknown action is retried with identical ID and text', posts.length === 2 && posts[0].body === posts[1].body);
    } else if (mode !== 'reload') {
        check(`${mode}: known/ambiguous action is not blindly reposted`, posts.length === 1);
    }
    if (mode === 'offline') {
        check('offline recovery retains durable command', storage.has('lighthouse.pendingTurn'));
        check('offline recovery does not fabricate success', rendered.length === 0);
    } else {
        check(`${mode}: terminal command removed from storage`, !storage.has('lighthouse.pendingTurn'));
        check(`${mode}: terminal result rendered once`, rendered.length === (mode === 'failed' ? 0 : 1));
    }
    if (mode === 'reload') check('reload queries the stored identifier', calls[0].url.includes(command.action_id));
    if (mode === 'failed') check('failed turn is explained', status.includes('interrupted'));
    check(`${mode}: input usable again`, !input.disabled);
}

console.log(`${checks - failures}/${checks} frontend checks passed`);
if (failures) process.exit(1);
