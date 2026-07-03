// THE LIGHTHOUSE - Client Logic

let gameStarted = false;
let gameHistory = [];
let maxHP = 14; // Replaced with the investigator's starting HP on game start
let imagePollTimer = null;
let archetypes = {};
let pendingRoll = null;
let rolling = false;

// ---- Retro audio (synthesized, no asset files) ----
let audioCtx = null;
let soundOn = true;
let heartbeatTimer = null;

function getAudio() {
    if (!soundOn) return null;
    if (!audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return null;
        audioCtx = new AC();
    }
    if (audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
}

// Short square-wave blip — the building block for all retro SFX.
function blip(freq, dur, type = 'square', gain = 0.05) {
    const ctx = getAudio();
    if (!ctx) return;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.value = freq;
    o.connect(g);
    g.connect(ctx.destination);
    const t = ctx.currentTime;
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t);
    o.stop(t + dur);
}

function sfxTumble() { blip(140 + Math.random() * 260, 0.03, 'square', 0.035); }

function sfxLand(success, fumble) {
    if (fumble) { blip(70, 0.5, 'sawtooth', 0.09); blip(48, 0.6, 'sawtooth', 0.07); return; }
    if (success) { blip(440, 0.08); setTimeout(() => blip(660, 0.14), 70); }
    else { blip(180, 0.12, 'sawtooth', 0.07); setTimeout(() => blip(110, 0.22, 'sawtooth', 0.07), 90); }
}

// Low "lub-dub" pulse loop while sanity is failing; faster at higher levels.
function startHeartbeat(level) {
    stopHeartbeat();
    if (level < 2 || !soundOn) return;
    const period = level >= 3 ? 900 : 1500;
    const beat = () => {
        blip(60, 0.12, 'sine', 0.10);
        setTimeout(() => blip(50, 0.16, 'sine', 0.09), 150);
    };
    beat();
    heartbeatTimer = setInterval(beat, period);
}
function stopHeartbeat() {
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
}

function toggleSound() {
    soundOn = !soundOn;
    const el = document.getElementById('sound-toggle');
    if (el) el.textContent = soundOn ? '[sound on]' : '[sound off]';
    if (!soundOn) stopHeartbeat();
}

// Load archetype stat blocks and show the initial preview
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/archetypes');
        archetypes = (await response.json()).archetypes;
        previewArchetype();
    } catch (error) {
        console.error('Error loading archetypes:', error);
    }
});

// Character sheet markup shared by the preview and the in-game sheet
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
    const language = document.getElementById('game-language').value;

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
            maxHP = data.investigator.HP; // Starting HP is the max

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
            hintEl.textContent = 'Type what you do below — look around, examine the logs, head inside…';
            intro.appendChild(hintEl);

            refreshGameState();
            setStatus('');
            document.getElementById('action-input').focus();
        } else {
            setStatus('Error: ' + (data.error || 'unknown'), true);
        }
    } catch (error) {
        setStatus('Connection error: ' + error.message, true);
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
    document.getElementById('hp-value').textContent = stats.HP + '/' + maxHP;
    document.getElementById('san-value').textContent = stats.SAN + '/99';
    document.getElementById('luck-value').textContent = stats.Luck;
}

// Show the current enemy and its HP while fighting.
function renderCombat(combat) {
    const bar = document.getElementById('combat-bar');
    if (!combat) { bar.classList.add('hidden'); return; }
    document.getElementById('combat-name').textContent = combat.name;
    document.getElementById('combat-hp').textContent = `HP ${combat.hp}`;
    bar.classList.remove('hidden');
}

// Show finite stakes (ammo, doom clock) in the HUD.
function renderResources(res) {
    if (!res) return;
    const ammoStat = document.getElementById('ammo-stat');
    const ammoVal = document.getElementById('ammo-value');
    const timeStat = document.getElementById('time-stat');
    const timeVal = document.getElementById('time-value');

    // Ammo: show whenever the adventure tracks it.
    if (res.ammo !== undefined) {
        ammoVal.textContent = res.ammo;
        ammoVal.classList.toggle('depleted', res.ammo === 0);
        ammoStat.classList.remove('hidden');
    }
    // Doom clock: time_remaining = -1 means no clock.
    if (res.time_remaining !== undefined && res.time_remaining >= 0) {
        timeVal.textContent = res.time_remaining;
        timeVal.classList.toggle('depleted', res.time_remaining <= 3);
        timeStat.classList.remove('hidden');
    }
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
}

function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : s;
    return d.innerHTML;
}

// Refresh game state from server (location, scene image).
// Image generation runs server-side in the background; poll until ready.
async function refreshGameState() {
    if (!gameStarted) return;

    clearTimeout(imagePollTimer);

    try {
        const response = await fetch('/api/game/state');
        if (!response.ok) return;
        const data = await response.json();

        document.getElementById('location-display').textContent = data.location;
        document.getElementById('turn-counter').textContent = data.turn;
        renderNpcs(data.npcs);
        renderResources(data.resources);
        renderCombat(data.combat);
        applySanityFx(data.sanity_corruption || 0);

        // Scene frame only appears when an image is present or being made;
        // text-only mode (images disabled) hides it entirely
        const frame = document.getElementById('scene-frame');
        const img = document.getElementById('scene-image');
        const placeholder = document.getElementById('scene-placeholder');
        if (data.image_url) {
            img.src = data.image_url;
            img.classList.remove('hidden');
            placeholder.classList.add('hidden');
            frame.classList.remove('hidden');
        } else if (data.image_generating) {
            img.classList.add('hidden');
            placeholder.classList.remove('hidden');
            frame.classList.remove('hidden');
            imagePollTimer = setTimeout(refreshGameState, 5000);
        } else {
            frame.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error refreshing game state:', error);
    }
}

// Begin a live narrative turn we can stream the DM's words into.
function beginTurn(action) {
    const turnEl = document.createElement('div');
    turnEl.className = 'narrative-turn';
    const playerEl = document.createElement('div');
    playerEl.className = 'player-action';
    playerEl.textContent = `> ${action}`;
    const dmEl = document.createElement('div');
    dmEl.className = 'dm-response';
    turnEl.appendChild(playerEl);
    turnEl.appendChild(dmEl);
    document.getElementById('narrative-content').appendChild(turnEl);
    scrollNarrative();
    return { turnEl, dmEl };
}

function scrollNarrative() {
    const d = document.getElementById('narrative-display');
    d.scrollTop = d.scrollHeight;
}

// Parse one SSE frame into {event, data}.
function parseSSE(frame) {
    let ev = 'message', data = '';
    frame.split('\n').forEach(line => {
        if (line.startsWith('event:')) ev = line.slice(6).trim();
        else if (line.startsWith('data:')) data += line.slice(5).trim();
    });
    return { event: ev, data };
}

function finishTurnUI(done, action, dmEl) {
    dmEl.textContent = (done.narrative || dmEl.textContent || '...').trim();
    gameHistory.push({ turn: done.turn, playerAction: action, dmResponse: done.narrative });
    updateStats(done.state);
    if (done.sanity_recovered > 0) {
        setStatus(`Your mind steadies. +${done.sanity_recovered} SAN`);
    }
    renderNpcs(done.npcs);
    renderResources(done.resources);
    renderCombat(done.combat);
    applySanityFx(done.sanity_corruption || 0);
    document.getElementById('turn-counter').textContent = done.turn;
    document.getElementById('location-display').textContent = done.location;
    if (done.pending_roll) showDiceArea(done.pending_roll);
    refreshGameState();
}

// Submit Player Action — streams the DM narration over SSE, falls back to the
// plain JSON endpoint if streaming isn't available.
async function submitAction(event) {
    event.preventDefault();

    const actionInput = document.getElementById('action-input');
    const action = actionInput.value.trim();
    if (!action) return;

    setStatus('...');
    actionInput.disabled = true;
    const { turnEl, dmEl } = beginTurn(action);

    try {
        const resp = await fetch('/api/game/action/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        if (!resp.ok || !resp.body) throw new Error('stream unavailable');

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = '', streamed = '', done = null, errMsg = null;

        while (true) {
            const { value, done: rdone } = await reader.read();
            if (rdone) break;
            buf += decoder.decode(value, { stream: true });
            let i;
            while ((i = buf.indexOf('\n\n')) >= 0) {
                const ev = parseSSE(buf.slice(0, i));
                buf = buf.slice(i + 2);
                if (ev.event === 'done') {
                    done = JSON.parse(ev.data);
                } else if (ev.event === 'error') {
                    errMsg = JSON.parse(ev.data).error;
                } else if (ev.data) {
                    streamed += (JSON.parse(ev.data).chunk || '');
                    dmEl.textContent = streamed;
                    scrollNarrative();
                }
            }
        }

        if (errMsg) { turnEl.remove(); setStatus(errMsg, true); return; }
        if (done) { setStatus(''); finishTurnUI(done, action, dmEl); actionInput.value = ''; }
        else { turnEl.remove(); throw new Error('stream ended early'); }
    } catch (error) {
        turnEl.remove();
        await submitActionFallback(action);
    } finally {
        if (!pendingRoll) {
            actionInput.disabled = false;
            actionInput.focus();
        }
    }
}

// Non-streaming fallback (original JSON endpoint).
async function submitActionFallback(action) {
    try {
        const response = await fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const data = await response.json();
        if (data.success) {
            addNarrativeTurn(data.turn, action, data.narrative);
            updateStats(data.state);
            renderNpcs(data.npcs);
            renderResources(data.resources);
            renderCombat(data.combat);
            applySanityFx(data.sanity_corruption || 0);
            document.getElementById('turn-counter').textContent = data.turn;
            document.getElementById('location-display').textContent = data.location;
            document.getElementById('action-input').value = '';
            setStatus(data.sanity_recovered > 0
                ? `Your mind steadies. +${data.sanity_recovered} SAN` : '');
            if (data.pending_roll) showDiceArea(data.pending_roll);
            refreshGameState();
        } else {
            setStatus(data.error || 'Action failed', true);
        }
    } catch (error) {
        setStatus(error.message, true);
    }
}

// ---- Dice rolling ----

// Set every face of the 3D die to the same (or a random) value.
function setDieFaces(die, value) {
    const faces = die.querySelectorAll('.face');
    faces.forEach(f => {
        f.textContent = value === undefined
            ? (1 + Math.floor(Math.random() * 100))
            : value;
    });
}

function showDiceArea(roll) {
    pendingRoll = roll;
    document.getElementById('action-input').disabled = true;

    const die = document.getElementById('pixel-die');
    die.className = '';
    setDieFaces(die, '?');

    document.getElementById('dice-label').textContent = roll.combat
        ? `ATTACK: ${roll.skill} — target ${roll.target}`
        : `ROLL: ${roll.skill} (${roll.difficulty}) — target ${roll.target}`;
    // Flee is only an option mid-combat.
    document.getElementById('flee-btn').classList.toggle('hidden', !roll.combat);
    const result = document.getElementById('dice-result');
    result.textContent = '';
    result.className = '';

    document.getElementById('dice-area').classList.remove('hidden');
}

function hideDiceArea() {
    pendingRoll = null;
    document.getElementById('dice-area').classList.add('hidden');
    document.getElementById('flee-btn').classList.add('hidden');
    const actionInput = document.getElementById('action-input');
    actionInput.disabled = false;
    actionInput.focus();
}

// Break off combat instead of throwing the attack die.
async function flee() {
    if (rolling) return;
    rolling = true;
    try {
        const data = await (await fetch('/api/game/flee', { method: 'POST' })).json();
        if (data.success) {
            addNarrativeTurn(data.turn, 'flee', data.narrative);
            updateStats(data.state);
            renderCombat(data.combat);
            hideDiceArea();
            refreshGameState();
        } else {
            setStatus(data.error || 'Cannot flee', true);
        }
    } catch (e) {
        setStatus(e.message, true);
    } finally {
        rolling = false;
    }
}

async function rollDice() {
    if (!pendingRoll || rolling) return;
    rolling = true;
    const roll = pendingRoll;  // capture (combat rounds re-show a new one)

    const die = document.getElementById('pixel-die');
    const resultEl = document.getElementById('dice-result');
    die.className = '';
    die.classList.add('rolling');

    // Cube tumbles in 3D; faces flicker random values + click while rolling
    const tumble = setInterval(() => { setDieFaces(die); sfxTumble(); }, 70);
    const minSpin = new Promise(resolve => setTimeout(resolve, 900));

    try {
        const [response] = await Promise.all([
            fetch('/api/game/roll', { method: 'POST' }),
            minSpin
        ]);
        const data = await response.json();

        clearInterval(tumble);

        if (!data.success) {
            die.classList.remove('rolling');
            setStatus(data.error || 'Roll failed', true);
            hideDiceArea();
            return;
        }

        // Lock the result onto every face, then play the landing bounce
        setDieFaces(die, data.empty ? '—' : data.roll);
        die.classList.remove('rolling');
        const cls = data.roll_success ? 'success' : 'failure';
        die.classList.add('settle', cls);
        resultEl.classList.add(cls);
        sfxLand(data.roll_success, data.consequence && data.consequence.fumble);
        let line;
        if (data.empty) {
            line = '*click* — OUT OF AMMO';
        } else {
            line = `${data.roll} vs ${data.target} — ${data.roll_success ? 'SUCCESS' : 'FAILURE'}`;
            // Surface the mechanical bite of a failure (e.g. "−3 HP", "FUMBLE")
            if (data.consequence && data.consequence.label) {
                const c = data.consequence;
                line += `  [${c.fumble ? 'FUMBLE! ' : ''}${c.label}]`;
            }
        }
        resultEl.textContent = line;

        updateStats(data.state);
        renderResources(data.resources);
        renderCombat(data.combat);
        document.getElementById('turn-counter').textContent = data.turn;
        document.getElementById('location-display').textContent = data.location;

        // Let the result sink in, then show the outcome
        setTimeout(() => {
            const label = roll && roll.combat ? 'attack' : `roll ${data.skill} (${data.difficulty})`;
            addNarrativeTurn(
                data.turn,
                `${label}: ${data.roll} vs ${data.target}`,
                data.narrative
            );
            if (data.pending_roll) {
                // Combat continues — hand the player the next attack throw.
                showDiceArea(data.pending_roll);
            } else {
                hideDiceArea();
                refreshGameState();
            }
        }, 1200);
    } catch (error) {
        clearInterval(tumble);
        die.classList.remove('rolling');
        setStatus(error.message, true);
        hideDiceArea();
    } finally {
        rolling = false;
    }
}

// Add Narrative Turn
function addNarrativeTurn(turn, playerAction, dmResponse) {
    const narrativeContent = document.getElementById('narrative-content');

    const turnEl = document.createElement('div');
    turnEl.className = 'narrative-turn';

    const playerEl = document.createElement('div');
    playerEl.className = 'player-action';
    playerEl.textContent = `> ${playerAction}`;
    turnEl.appendChild(playerEl);

    const dmEl = document.createElement('div');
    dmEl.className = 'dm-response';
    dmEl.textContent = (dmResponse || '(The keeper considers your words...)').trim();
    turnEl.appendChild(dmEl);

    narrativeContent.appendChild(turnEl);

    const display = document.getElementById('narrative-display');
    display.scrollTop = display.scrollHeight;

    gameHistory.push({ turn, playerAction, dmResponse });
}

// Show History
function showHistory() {
    document.getElementById('narrative-display').classList.add('hidden');
    hidePanels();
    document.getElementById('history-display').classList.remove('hidden');

    const historyContent = document.getElementById('history-content');
    historyContent.innerHTML = '';

    if (gameHistory.length === 0) {
        historyContent.textContent = 'No history yet.';
        return;
    }

    gameHistory.forEach(entry => {
        const entryEl = document.createElement('div');
        entryEl.className = 'narrative-turn';

        const playerEl = document.createElement('div');
        playerEl.className = 'player-action';
        playerEl.textContent = `[${entry.turn}] > ${entry.playerAction}`;
        entryEl.appendChild(playerEl);

        const dmEl = document.createElement('div');
        dmEl.className = 'dm-response';
        dmEl.textContent = (entry.dmResponse || '').trim();
        entryEl.appendChild(dmEl);

        historyContent.appendChild(entryEl);
    });
}

// Show Narrative (back from any panel)
function showNarrative() {
    hidePanels();
    document.getElementById('narrative-display').classList.remove('hidden');
}

// Reset Game
function resetGame() {
    if (!confirm('Reset the game? All progress will be lost.')) return;

    gameStarted = false;
    gameHistory = [];
    pendingRoll = null;
    clearTimeout(imagePollTimer);
    stopHeartbeat();
    document.getElementById('game-screen').classList.remove('san-fx-1', 'san-fx-2', 'san-fx-3');
    document.getElementById('combat-bar').classList.add('hidden');
    document.getElementById('dice-area').classList.add('hidden');
    document.getElementById('action-input').disabled = false;

    document.getElementById('startup-screen').classList.remove('hidden');
    document.getElementById('game-screen').classList.add('hidden');
    hidePanels();
    document.getElementById('narrative-display').classList.remove('hidden');

    document.getElementById('narrative-content').innerHTML = '';
    document.getElementById('investigator-name').value = '';
    document.getElementById('scene-image').classList.add('hidden');
    document.getElementById('scene-placeholder').classList.remove('hidden');
    document.getElementById('turn-counter').textContent = '0';
    document.getElementById('location-display').textContent = 'Exterior - Rocky Shore';
    setStatus('');

    fetch('/api/game/reset', { method: 'POST' });
}

// Focus action input on any letter
document.addEventListener('keydown', (e) => {
    if (!gameStarted) return;
    // Space/enter throws the pending die
    if (pendingRoll && (e.key === ' ' || e.key === 'Enter')) {
        e.preventDefault();
        rollDice();
        return;
    }
    if (pendingRoll) return;
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
        const actionInput = document.getElementById('action-input');
        if (document.activeElement !== actionInput) {
            actionInput.focus();
        }
    }
});
