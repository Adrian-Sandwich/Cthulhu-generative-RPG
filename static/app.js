// Cthulhu Lighthouse Game - Client Logic

let gameStarted = false;
let currentScene = null;
let gameHistory = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Game initialized');
    fetchScenes();
});

// Start Game
async function startGame(event) {
    event.preventDefault();

    const name = document.getElementById('investigator-name').value;
    const archetype = document.getElementById('investigator-archetype').value;

    const statusEl = document.getElementById('action-status');
    statusEl.textContent = 'Initializing...';

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

            // Hide startup, show game screen
            document.getElementById('startup-screen').classList.add('hidden');
            document.getElementById('game-screen').classList.remove('hidden');
            document.getElementById('action-input-area').classList.remove('hidden');

            // Update character info
            updateCharacterInfo(data.investigator);

            // Show initial scene
            showScene();

            statusEl.textContent = data.message;
        } else {
            statusEl.textContent = '❌ Error: ' + (data.error || 'Unknown error');
        }
    } catch (error) {
        statusEl.textContent = '❌ Connection error: ' + error.message;
    }
}

// Update Character Info
function updateCharacterInfo(investigator) {
    document.getElementById('character-info').classList.remove('hidden');
    document.getElementById('char-name').textContent = investigator.name;
    document.getElementById('char-archetype').textContent = investigator.archetype.toUpperCase();

    updateStats(investigator);
}

// Update Stats Bars
function updateStats(stats) {
    const maxHP = 14; // Standard Call of Cthulhu
    const maxSAN = 99;
    const maxLuck = 100;

    // HP
    const hpPercent = (stats.HP / maxHP) * 100;
    document.getElementById('hp-bar').style.width = hpPercent + '%';
    document.getElementById('hp-value').textContent = stats.HP + '/' + maxHP;

    // SAN
    const sanPercent = (stats.SAN / maxSAN) * 100;
    document.getElementById('san-bar').style.width = sanPercent + '%';
    document.getElementById('san-value').textContent = stats.SAN + '/' + maxSAN;

    // Luck
    const luckPercent = (stats.Luck / maxLuck) * 100;
    document.getElementById('luck-bar').style.width = luckPercent + '%';
    document.getElementById('luck-value').textContent = stats.Luck + '/' + maxLuck;
}

// Fetch Scenes (for preloading)
async function fetchScenes() {
    try {
        const response = await fetch('/api/scenes');
        const data = await response.json();
        console.log('Available scenes:', data.scenes);
    } catch (error) {
        console.error('Error fetching scenes:', error);
    }
}

// Show Scene
async function showScene() {
    if (!gameStarted) return;

    const statusEl = document.getElementById('action-status');
    statusEl.textContent = 'Loading scene...';

    try {
        // For now, show exterior_storm as example
        // In future, this will be determined by game state
        const sceneKey = 'exterior_storm';

        const response = await fetch(`/api/scene/${sceneKey}`);
        const data = await response.json();

        if (data.content) {
            document.getElementById('scene-content').textContent = data.content;
            currentScene = sceneKey;
            statusEl.textContent = '';
        }
    } catch (error) {
        statusEl.textContent = '❌ Error loading scene: ' + error.message;
    }
}

// Submit Player Action
async function submitAction(event) {
    event.preventDefault();

    const actionInput = document.getElementById('action-input');
    const action = actionInput.value.trim();

    if (!action) return;

    const statusEl = document.getElementById('action-status');
    statusEl.textContent = 'Processing action...';
    actionInput.disabled = true;

    try {
        const response = await fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });

        const data = await response.json();

        if (data.success) {
            // Add to narrative
            addNarrativeTurn(data.turn, action, data.narrative);

            // Update stats
            updateStats(data.state);

            // Update turn counter
            document.getElementById('turn-counter').textContent = data.turn;

            // Update location
            document.getElementById('location-display').textContent = data.location;

            // Clear input
            actionInput.value = '';
            statusEl.textContent = '';

            // Scroll to bottom of narrative
            const narrativeContent = document.getElementById('narrative-content');
            narrativeContent.scrollTop = narrativeContent.scrollHeight;
        } else {
            statusEl.textContent = '❌ ' + (data.error || 'Action failed');
        }
    } catch (error) {
        statusEl.textContent = '❌ ' + error.message;
    } finally {
        actionInput.disabled = false;
        actionInput.focus();
    }
}

// Add Narrative Turn
function addNarrativeTurn(turn, playerAction, dmResponse) {
    const narrativeContent = document.getElementById('narrative-content');

    const turnEl = document.createElement('div');
    turnEl.className = 'narrative-turn';

    const turnLabel = document.createElement('div');
    turnLabel.className = 'turn-label';
    turnLabel.textContent = `⏱️ Turn ${turn}`;
    turnEl.appendChild(turnLabel);

    const playerEl = document.createElement('div');
    playerEl.className = 'player-action';
    playerEl.textContent = `You: ${playerAction}`;
    turnEl.appendChild(playerEl);

    const dmEl = document.createElement('div');
    dmEl.className = 'dm-response';
    dmEl.textContent = dmResponse || '(The keeper considers your words...)';
    turnEl.appendChild(dmEl);

    narrativeContent.appendChild(turnEl);

    // Add to history
    gameHistory.push({
        turn,
        playerAction,
        dmResponse
    });
}

// Show History
function showHistory() {
    document.getElementById('narrative-display').classList.add('hidden');
    document.getElementById('history-display').classList.remove('hidden');

    const historyContent = document.getElementById('history-content');
    historyContent.innerHTML = '';

    if (gameHistory.length === 0) {
        historyContent.innerHTML = '<p style="color: var(--text-secondary);">No history yet.</p>';
        return;
    }

    gameHistory.forEach(entry => {
        const entryEl = document.createElement('div');
        entryEl.className = 'narrative-turn';

        const turnLabel = document.createElement('div');
        turnLabel.className = 'turn-label';
        turnLabel.textContent = `⏱️ Turn ${entry.turn}`;
        entryEl.appendChild(turnLabel);

        const playerEl = document.createElement('div');
        playerEl.className = 'player-action';
        playerEl.textContent = `You: ${entry.playerAction}`;
        entryEl.appendChild(playerEl);

        const dmEl = document.createElement('div');
        dmEl.className = 'dm-response';
        dmEl.textContent = entry.dmResponse;
        entryEl.appendChild(dmEl);

        historyContent.appendChild(entryEl);
    });
}

// Show Narrative (back from history)
function showNarrative() {
    document.getElementById('narrative-display').classList.remove('hidden');
    document.getElementById('history-display').classList.add('hidden');
}

// Reset Game
function resetGame() {
    if (!confirm('Reset the game? All progress will be lost.')) return;

    gameStarted = false;
    gameHistory = [];
    currentScene = null;

    // Show startup, hide game
    document.getElementById('startup-screen').classList.remove('hidden');
    document.getElementById('game-screen').classList.add('hidden');
    document.getElementById('action-input-area').classList.add('hidden');
    document.getElementById('history-display').classList.add('hidden');
    document.getElementById('narrative-display').classList.remove('hidden');

    // Clear content
    document.getElementById('narrative-content').innerHTML = '';
    document.getElementById('investigator-name').value = '';
    document.getElementById('character-info').classList.add('hidden');

    // Reset display
    document.getElementById('turn-counter').textContent = '0';
    document.getElementById('location-display').textContent = 'Exterior - Rocky Shore';

    // Call reset API
    fetch('/api/game/reset', { method: 'POST' });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!gameStarted) return;

    // Focus action input on any letter
    if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
        const actionInput = document.getElementById('action-input');
        if (document.activeElement !== actionInput) {
            actionInput.focus();
        }
    }
});
