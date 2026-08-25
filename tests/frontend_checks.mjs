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

console.log(`${checks - failures}/${checks} frontend checks passed`);
if (failures) process.exit(1);
