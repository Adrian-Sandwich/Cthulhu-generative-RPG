// THE LIGHTHOUSE - Client Logic

let gameStarted = false;
let gameHistory = [];
let maxHP = 14; // Replaced with the investigator's starting HP on game start
let imagePollTimer = null;
let archetypes = {};
let pendingRoll = null;
let rolling = false;

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

    try {
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, archetype })
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

// Submit Player Action
async function submitAction(event) {
    event.preventDefault();

    const actionInput = document.getElementById('action-input');
    const action = actionInput.value.trim();

    if (!action) return;

    setStatus('...');
    actionInput.disabled = true;

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
            document.getElementById('turn-counter').textContent = data.turn;
            document.getElementById('location-display').textContent = data.location;

            actionInput.value = '';
            setStatus('');

            // DM asked for a roll: hand the die to the player
            if (data.pending_roll) {
                showDiceArea(data.pending_roll);
            }

            // Update location image (may trigger generation server-side)
            refreshGameState();
        } else {
            setStatus(data.error || 'Action failed', true);
        }
    } catch (error) {
        setStatus(error.message, true);
    } finally {
        if (!pendingRoll) {
            actionInput.disabled = false;
            actionInput.focus();
        }
    }
}

// ---- Dice rolling ----

function showDiceArea(roll) {
    pendingRoll = roll;
    document.getElementById('action-input').disabled = true;

    const die = document.getElementById('pixel-die');
    die.textContent = '?';
    die.className = '';

    document.getElementById('dice-label').textContent =
        `ROLL: ${roll.skill} (${roll.difficulty}) — target ${roll.target}`;
    const result = document.getElementById('dice-result');
    result.textContent = '';
    result.className = '';

    document.getElementById('dice-area').classList.remove('hidden');
}

function hideDiceArea() {
    pendingRoll = null;
    document.getElementById('dice-area').classList.add('hidden');
    const actionInput = document.getElementById('action-input');
    actionInput.disabled = false;
    actionInput.focus();
}

async function rollDice() {
    if (!pendingRoll || rolling) return;
    rolling = true;

    const die = document.getElementById('pixel-die');
    const resultEl = document.getElementById('dice-result');
    die.classList.add('rolling');

    // Pixel die tumbles with random faces while the server rolls
    const tumble = setInterval(() => {
        die.textContent = 1 + Math.floor(Math.random() * 100);
    }, 70);
    const minSpin = new Promise(resolve => setTimeout(resolve, 900));

    try {
        const [response] = await Promise.all([
            fetch('/api/game/roll', { method: 'POST' }),
            minSpin
        ]);
        const data = await response.json();

        clearInterval(tumble);
        die.classList.remove('rolling');

        if (!data.success) {
            setStatus(data.error || 'Roll failed', true);
            hideDiceArea();
            return;
        }

        // Settle on the server's number
        die.textContent = data.roll;
        const cls = data.roll_success ? 'success' : 'failure';
        die.classList.add(cls);
        resultEl.classList.add(cls);
        resultEl.textContent =
            `${data.roll} vs ${data.target} — ${data.roll_success ? 'SUCCESS' : 'FAILURE'}`;

        updateStats(data.state);
        document.getElementById('turn-counter').textContent = data.turn;
        document.getElementById('location-display').textContent = data.location;

        // Let the result sink in, then show the DM's consequence
        setTimeout(() => {
            addNarrativeTurn(
                data.turn,
                `roll ${data.skill} (${data.difficulty}): ${data.roll} vs ${data.target}`,
                data.narrative
            );
            hideDiceArea();
            refreshGameState();
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
