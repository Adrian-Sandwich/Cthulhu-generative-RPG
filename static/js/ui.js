// THE LIGHTHOUSE — ui
//
// Character sheet, panels, HUD rendering, suggestion chips and feedback.

function renderSheet(container, sheet) {
    const chars = sheet.characteristics;
    const charOrder = ['STR', 'CON', 'SIZ', 'DEX', 'APP', 'INT', 'POW', 'EDU'];

    const skills = Object.entries(sheet.skills)
        .sort((a, b) => b[1] - a[1])
        .map(([name, value]) => {
            const label = name.replace(/_/g, ' ');
            return `<span class="skill">${label} <b>${value}</b></span>`;
        })
        .join('');

    container.innerHTML = `
        ${sheet.description ? `<p class="sheet-desc">${sheet.description}</p>` : ''}
        <div class="sheet-chars">
            ${charOrder.map(c => `<span>${c} <b>${chars[c]}</b></span>`).join('')}
        </div>
        <div class="sheet-derived">
            HP <b>${sheet.derived.HP}</b> &nbsp; SAN <b>${sheet.derived.SAN}</b> &nbsp; LUCK <b>${sheet.derived.Luck}</b>
        </div>
        <div class="sheet-skills">${skills}</div>
    `;
}

// Preview the selected archetype's sheet on the startup screen
function previewArchetype() {
    const key = document.getElementById('investigator-archetype').value;
    const sheet = archetypes[key];
    if (sheet) {
        renderSheet(document.getElementById('archetype-preview'), sheet);
    }
}

// Show the investigator sheet during play
async function showSheet() {
    try {
        const response = await fetch('/api/game/state');
        if (!response.ok) return;
        const inv = (await response.json()).investigator;

        renderSheet(document.getElementById('sheet-content'), {
            description: null,
            characteristics: inv.characteristics,
            derived: { HP: inv.HP, SAN: inv.SAN, Luck: inv.Luck },
            skills: inv.skills
        });

        hidePanels();
        document.getElementById('sheet-display').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading sheet:', error);
    }
}

// Show the how-to-play panel
function showHelp() {
    hidePanels();
    document.getElementById('help-display').classList.remove('hidden');
}

// Hide every overlay panel (narrative stays as the base layer)
function hidePanels() {
    ['narrative-display', 'history-display', 'sheet-display', 'help-display']
        .forEach(id => document.getElementById(id).classList.add('hidden'));
}

// Start Game
async function startGame(event) {
    event.preventDefault();

    const name = document.getElementById('investigator-name').value;
    const archetype = document.getElementById('investigator-archetype').value;
    // Selector hidden while Spanish play is paused; element may not exist.
    const langEl = document.getElementById('game-language');
    const language = langEl ? langEl.value : 'en';

    // Guard against double-submit: repeated BEGIN clicks each restarted the
    // game server-side (and re-translated the intro) while the first loaded.
    const startBtn = document.querySelector('.start-btn');
    if (startBtn.disabled) return;
    startBtn.disabled = true;
    startBtn.textContent = '...';

    try {
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, archetype, language })
        });

        const data = await response.json();

        if (data.success) {
            gameStarted = true;
            gameHistory = [];
            maxHP = data.investigator.maxHP || data.investigator.HP;

            document.getElementById('startup-screen').classList.add('hidden');
            document.getElementById('game-screen').classList.remove('hidden');

            updateStats(data.investigator);
            if (data.location) {
                document.getElementById('location-display').textContent = data.location;
            }

            // Opening narrative so the player knows the setup. Render it
            // as the DM's first beat with a hint to act in free text.
            const intro = document.getElementById('narrative-content');
            intro.innerHTML = '';
            if (data.intro) {
                const introEl = document.createElement('div');
                introEl.className = 'narrative-turn dm-response intro';
                introEl.textContent = data.intro;
                intro.appendChild(introEl);
            }
            const hintEl = document.createElement('div');
            hintEl.className = 'narrative-turn hint';
            hintEl.innerHTML =
                'CÓMO JUGAR / HOW TO PLAY<br>' +
                '• Escribe lo que TU personaje intenta (o usa los botones de abajo).<br>' +
                '• Cuando aparezca el dado, haz click para tirarlo — decide si lo logras.<br>' +
                '• El horror baja tu cordura (SAN). Sobrevive y descubre la verdad.';
            intro.appendChild(hintEl);

            refreshGameState();
            setStatus('');
            document.getElementById('action-input').focus();
            startMusic();  // BEGIN click is the user gesture AudioContext needs
            renderSuggestions('explore');
            armExitFeedback();
        } else {
            setStatus('Error: ' + (data.error || 'unknown'), true);
        }
    } catch (error) {
        setStatus('Connection error: ' + error.message, true);
    } finally {
        startBtn.disabled = false;
        startBtn.textContent = 'BEGIN';
    }
}

// Status line under the input
function setStatus(message, isError = false) {
    const el = document.getElementById('action-status');
    el.textContent = message || '';
    el.classList.toggle('error', isError);
}

// Update Stats
function updateStats(stats) {
    if (stats.maxHP !== undefined) {
        maxHP = stats.maxHP;
    }
    if (maxHP === null || maxHP === undefined) {
        maxHP = stats.HP; // Fallback until start / state refresh arrives
    }
    document.getElementById('hp-value').textContent = stats.HP + '/' + maxHP;
    document.getElementById('san-value').textContent = stats.SAN + '/99';
    document.getElementById('luck-value').textContent = stats.Luck;
    musicState.san = stats.SAN;
    musicState.turn = parseInt(document.getElementById('turn-counter').textContent, 10) || musicState.turn;
    updateMusic();
}

// Show the current enemy and its HP while fighting.
function renderCombat(combat) {
    const bar = document.getElementById('combat-bar');
    musicState.inCombat = !!combat;
    updateMusic();
    if (!combat) { bar.classList.add('hidden'); return; }
    document.getElementById('combat-name').textContent = combat.name;
    document.getElementById('combat-hp').textContent = `HP ${combat.hp}`;
    bar.classList.remove('hidden');
}

let gameOver = false;

// The story has ended — show the game-over screen and lock further input.
function showEnding(ending) {
    if (!ending || gameOver) return;
    gameOver = true;
    document.getElementById('ending-name').textContent = (ending.name || 'THE END').toUpperCase();
    document.getElementById('ending-text').textContent = ending.narrative || '';
    document.getElementById('ending-screen').classList.remove('hidden');
    document.getElementById('ending-screen').scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Lock the game: no more actions, hide the dice/suggestions.
    document.getElementById('action-input').disabled = true;
    hideDiceArea();
    hideSuggestions();
    document.getElementById('combat-bar').classList.add('hidden');
    stopHeartbeat();
    // let the dread music resolve into silence
    setTimeout(stopMusic, 4000);
    // one last feedback ask on the way out
    if (typeof fbGiven !== 'undefined' && !fbGiven) setTimeout(() => showFeedback(false), 1500);
}

// Show finite stakes (ammo, doom clock) in the HUD.
function renderResources(res) {
    if (!res) return;
    const ammoStat = document.getElementById('ammo-stat');
    const ammoVal = document.getElementById('ammo-value');
    const timeStat = document.getElementById('time-stat');
    const timeVal = document.getElementById('time-value');

    // Ammo: only shown once the player actually has a firearm (no phantom
    // rounds without a gun).
    if (res.has_firearm) {
        ammoVal.textContent = res.ammo;
        ammoVal.classList.toggle('depleted', res.ammo === 0);
        ammoStat.classList.remove('hidden');
    } else {
        ammoStat.classList.add('hidden');
    }
    // Doom clock: time_remaining = -1 means no clock.
    if (res.time_remaining !== undefined && res.time_remaining >= 0) {
        timeVal.textContent = res.time_remaining;
        timeVal.classList.toggle('depleted', res.time_remaining <= 3);
        timeStat.classList.remove('hidden');
    }
    musicState.timeRemaining = (res.time_remaining !== undefined) ? res.time_remaining : -1;
    updateMusic();
}

// Render the dossier of NPCs the player has met, with how they regard you.
function renderNpcs(npcs) {
    const dossier = document.getElementById('npc-dossier');
    const list = document.getElementById('npc-list');
    if (!npcs || npcs.length === 0) {
        dossier.classList.add('hidden');
        return;
    }
    list.innerHTML = npcs.map(n => {
        const rep = (n.reputation >= 0 ? '+' : '') + n.reputation;
        const mem = n.times_talked > 1 ? ` · remembers ${n.times_talked}` : '';
        const ally = n.companion ? `<span class="npc-att att-trusted">⚑ ally</span>` : '';
        return `<span class="npc-chip">
            <span class="npc-name">${escapeHtml(n.name)}</span>
            ${ally}
            <span class="npc-att att-${n.attitude}">${n.attitude}</span>
            <span class="npc-rep">${rep}</span>
            <span class="npc-mem">${mem}</span>
        </span>`;
    }).join('');
    dossier.classList.remove('hidden');
}

// Distort the screen as sanity fails (0=lucid .. 3=shattered).
function applySanityFx(level) {
    const screen = document.getElementById('game-screen');
    screen.classList.remove('san-fx-1', 'san-fx-2', 'san-fx-3');
    if (level >= 1) screen.classList.add('san-fx-' + Math.min(level, 3));
    startHeartbeat(level);  // pulse loop kicks in at level 2+
    musicState.corruption = level;
    updateMusic();
}

function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : s;
    return d.innerHTML;
}

// ---- Suggested actions: guidance chips so players always know a next move.
// Playtest feedback: total freedom paralyzes ("no le hayo"), and after a roll
// players didn't know how to continue. Rule-based (no LLM latency); clicking
// a chip submits it as the action — typing anything remains king.
// Players who don't realise the die is clickable type the request as an action
// instead. Champi did exactly that in the LAN playtest ("Lanza el dado") and
// spent a turn on it, since the Keeper receives it as narrative. Rolls are
// engine-driven — the die appears on its own when an action is risky — so
// answer the question locally rather than burning the turn.
const ROLL_REQUEST_RE = new RegExp(
    '^\\s*(?:' +
    // Spanish: lanza/tira/echa/avienta (el|los|un) dado(s)
    '(?:lanz|tir|ech|avient)\\w*\\s+(?:el|los|un|unos)?\\s*dad[oi]s?' +
    '|' +
    // English: roll/throw/cast (the|a) dice/die/d100
    '(?:roll|throw|cast)\\s+(?:the|a|my)?\\s*(?:dice|die|d100|d\\d+)' +
    ')\\s*[.!]*\\s*$',
    'i'
);

const SUGGESTION_POOLS = {
    explore: [
        'Look around carefully', 'Examine that more closely', 'Search for anything useful',
        'Listen for sounds', 'Move deeper inside', 'Check the logs and papers',
        'Look for a weapon', 'Head toward the stairs',
    ],
    shaken: ['Take a breath and steady yourself', 'Pray quietly for a moment'],
    afterRoll: ['Press on', 'Search the area', 'Back away slowly'],
};

function renderSuggestions(kind) {
    const box = document.getElementById('suggestions');
    if (pendingRoll) { box.classList.add('hidden'); return; }  // dice first
    const picks = [];
    const pool = [...SUGGESTION_POOLS[kind === 'afterRoll' ? 'afterRoll' : 'explore']];
    while (picks.length < 3 && pool.length) {
        picks.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
    }
    if (musicState.san < 50) picks[picks.length - 1] =
        SUGGESTION_POOLS.shaken[Math.floor(Math.random() * SUGGESTION_POOLS.shaken.length)];
    box.innerHTML = picks.map(p =>
        `<span class="suggestion-chip" onclick="useSuggestion(this)">${escapeHtml(p)}</span>`).join('');
    box.classList.remove('hidden');
}

function useSuggestion(el) {
    const input = document.getElementById('action-input');
    if (input.disabled) return;
    input.value = el.textContent;
    document.getElementById('action-form').requestSubmit();
}

function hideSuggestions() {
    document.getElementById('suggestions').classList.add('hidden');
}

// ---- Feedback: leave your findings any time, or on the way out.
let fbRating = 0;
let fbThenReset = false;
let fbGiven = false;      //已 left feedback this session → stop nagging
let fbPrompted = false;   // one-time mid-session nudge already shown

function showFeedback(thenReset) {
    fbThenReset = !!thenReset;
    setRating(0);
    const panel = document.getElementById('feedback-panel');
    panel.classList.remove('hidden');
    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.getElementById('feedback-text').focus();
}

// Fire once when the player tries to LEAVE (close tab / navigate away). We
// can't hold them, so if they've written anything we ship it with
// sendBeacon, which survives page unload. If they've engaged but written
// nothing, pop the panel so a returning/again-closing player sees the ask.
function armExitFeedback() {
    window.addEventListener('beforeunload', () => {
        if (fbGiven) return;
        const text = (document.getElementById('feedback-text').value || '').trim();
        if (text || fbRating) {
            const blob = new Blob(
                [JSON.stringify({ text: text || '(solo rating)', rating: fbRating || undefined })],
                { type: 'application/json' });
            navigator.sendBeacon('/api/feedback', blob);
            fbGiven = true;
        } else if (gameStarted && !document.getElementById('feedback-panel').classList.contains('hidden') === false) {
            // reveal the panel for next time (can't block unload reliably)
            document.getElementById('feedback-panel').classList.remove('hidden');
        }
    });
    // Also catch tab-hide on mobile (beforeunload is unreliable there).
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && !fbGiven && gameStarted) {
            const text = (document.getElementById('feedback-text').value || '').trim();
            if (text || fbRating) {
                const blob = new Blob(
                    [JSON.stringify({ text: text || '(solo rating)', rating: fbRating || undefined })],
                    { type: 'application/json' });
                navigator.sendBeacon('/api/feedback', blob);
                fbGiven = true;
            }
        }
    });
}

// One-time nudge after the player is clearly invested.
function maybePromptFeedback(turn) {
    if (fbPrompted || fbGiven || turn < 8) return;
    fbPrompted = true;
    showFeedback(false);
    setStatus('Llevas un rato — ¿nos dejas una reseña rápida? (o [skip])');
}

function setRating(n) {
    fbRating = n;
    document.querySelectorAll('#feedback-stars a').forEach((a, i) => {
        a.textContent = i < n ? '★' : '☆';
        a.classList.toggle('lit', i < n);
    });
}

function closeFeedback() {
    document.getElementById('feedback-panel').classList.add('hidden');
    if (fbThenReset) { fbThenReset = false; doReset(); }
}

async function submitFeedback() {
    const text = document.getElementById('feedback-text').value.trim();
    if (!text && !fbRating) { closeFeedback(); return; }
    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text || '(solo rating)', rating: fbRating || undefined })
        });
        setStatus('Feedback guardado — gracias, investigador.');
    } catch (e) {
        setStatus('No se pudo guardar el feedback', true);
    }
    fbGiven = true;  // stop exit/visibility nags once they've sent something
    document.getElementById('feedback-text').value = '';
    closeFeedback();
}

// Refresh game state from server (location, scene image).
// Image generation runs server-side in the background; poll until ready.
