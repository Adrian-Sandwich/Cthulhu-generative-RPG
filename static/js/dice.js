// THE LIGHTHOUSE — dice
//
// Dice rolling and combat, plus history and reset.

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
    // First time a die ever appears, point the player at it.
    document.getElementById('die-tip').classList.toggle('hidden', firstRollSeen);
}

function hideDiceArea() {
    pendingRoll = null;
    document.getElementById('dice-area').classList.add('hidden');
    document.getElementById('flee-btn').classList.add('hidden');
    const actionInput = document.getElementById('action-input');
    actionInput.disabled = false;
    actionInput.focus();
    if (gameStarted) renderSuggestions('afterRoll');
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
    firstRollSeen = true;
    document.getElementById('die-tip').classList.add('hidden');
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
        if (data.ending) showEnding(data.ending);
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
    // Ask for feedback on the way out (skip is one click); then reset.
    showFeedback(true);
}

function doReset() {
    gameStarted = false;
    gameHistory = [];
    pendingRoll = null;
    clearTimeout(imagePollTimer);
    stopHeartbeat();
    stopMusic();
    gameOver = false;
    document.getElementById('ending-screen').classList.add('hidden');
    document.getElementById('action-input').disabled = false;
    musicState.corruption = 0; musicState.inCombat = false; musicState.timeRemaining = -1;
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
