// THE LIGHTHOUSE — turn
//
// The turn loop: state refresh, SSE plumbing, and action submission.

async function refreshGameState() {
    if (!gameStarted) return;

    clearTimeout(imagePollTimer);

    try {
        const response = await fetch('/api/game/state');
        if (!response.ok) {
            if (response.status === 400) {
                gameStarted = false;
                gameId = null;
                document.getElementById('startup-screen').classList.remove('hidden');
                document.getElementById('game-screen').classList.add('hidden');
            }
            return;
        }
        const data = await response.json();
        gameId = data.game_id;
        worldSuggestions = data.world_actions || [];
        updateStats(data.investigator);
        if (data.pending_roll) showDiceArea(data.pending_roll);
        if (data.ending) showEnding(data.ending);

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
    if (!done.action_id || !gameHistory.some(turn => turn.action_id === done.action_id)) {
        gameHistory.push({ turn: done.turn, playerAction: action, dmResponse: done.narrative,
                           action_id: done.action_id });
    }
    updateStats(done.state);
    if (done.sanity_recovered > 0) {
        setStatus(`Your mind steadies. +${done.sanity_recovered} SAN`);
    }
    renderNpcs(done.npcs);
    renderResources(done.resources);
    renderCombat(done.combat);
    applySanityFx(done.sanity_corruption || 0);
    if (done.ending) showEnding(done.ending);
    document.getElementById('turn-counter').textContent = done.turn;
    document.getElementById('location-display').textContent = done.location;
    if (done.pending_roll) showDiceArea(done.pending_roll);
    else renderSuggestions('explore');
    refreshGameState();
    maybePromptFeedback(done.turn);
}

// One durable command per browser tab, retained across reloads and retries.
const TURN_STORAGE_KEY = 'lighthouse.pendingTurn';
let submittingTurn = false;
let pendingTurn = null;

function rememberTurn(command) {
    // Persist before sending: if storage is unavailable, do not create a turn
    // that this tab cannot recover after a reload.
    sessionStorage.setItem(TURN_STORAGE_KEY, JSON.stringify(command));
    pendingTurn = command;
}

function forgetTurn() {
    sessionStorage.removeItem(TURN_STORAGE_KEY);
    pendingTurn = null;
}

function newActionId() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
}

async function turnRequest(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
        const response = await fetch(url, { cache: 'no-store', ...options, signal: controller.signal });
        const body = await response.json();
        return { response, body };
    } finally {
        clearTimeout(timer);
    }
}

async function recoverTurn(command) {
    setStatus('Reconnecting to your turn...');
    const deadline = Date.now() + 120000;
    for (let attempt = 0; attempt < 60 && Date.now() < deadline; attempt++) {
        try {
            const { response, body } = await turnRequest(
                `/api/game/actions/${command.action_id}?game_id=${encodeURIComponent(command.game_id)}`);
            if (response.ok && ['completed', 'failed'].includes(body.status)) {
                return body.result;
            }
            if (response.status === 409) return { error: body.error };
            if (response.status === 404) {
                // It may never have reached the server. Reuse the identical
                // command; the same ID also makes an ambiguous timeout safe.
                const retry = await turnRequest('/api/game/action', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(command),
                });
                if (retry.response.ok || [400, 409, 413, 422].includes(retry.response.status)) {
                    return retry.body;
                }
            }
        } catch (error) {
            // The receipt remains in sessionStorage while the network is down.
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    throw new Error('Still reconnecting. Submit again to check this same turn.');
}

// Submit or recover one command. Double clicks never allocate another ID.
async function submitAction(event) {
    event.preventDefault();
    if (submittingTurn) return;
    const actionInput = document.getElementById('action-input');
    const action = pendingTurn ? pendingTurn.action : actionInput.value.trim();
    if (!action) return;
    if (!pendingTurn && /^(inventory|inventario|ver inventario|mi inventario|show inventory|check inventory|what am i carrying|qu[eé] llevo)[?.!]*$/i.test(action)) {
        await showSheet();
        actionInput.value = '';
        return;
    }
    if (!pendingTurn && ROLL_REQUEST_RE.test(action)) {
        setStatus(pendingRoll ? 'Haz click en el dado. / Click the die.'
            : 'Dice appear when an action is risky. Describe what you do.');
        actionInput.select();
        return;
    }
    submittingTurn = true;
    actionInput.disabled = true;
    let turnEl;
    try {
        if (!gameId) throw new Error('Reload the game before sending an action.');
        const recovering = Boolean(pendingTurn);
        if (!pendingTurn) rememberTurn({ action, action_id: newActionId(), game_id: gameId });
        const command = pendingTurn;
        hideSuggestions();
        const view = beginTurn(action);
        turnEl = view.turnEl;
        const dmEl = view.dmEl;
        let result;
        if (recovering) {
            result = await recoverTurn(command);
        } else {
            setStatus('The keeper considers...');
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 90000);
            try {
                const resp = await fetch('/api/game/action/stream', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(command), signal: controller.signal,
                });
                if (!resp.ok || !resp.body) {
                    if ([400, 409, 413, 422].includes(resp.status)) result = await resp.json();
                    else throw new Error('stream unavailable');
                } else {
                    const reader = resp.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = '', streamed = '';
                    while (true) {
                        const packet = await reader.read();
                        if (packet.done) break;
                        buffer += decoder.decode(packet.value, { stream: true });
                        let boundary;
                        while ((boundary = buffer.indexOf('\n\n')) >= 0) {
                            const frame = parseSSE(buffer.slice(0, boundary));
                            buffer = buffer.slice(boundary + 2);
                            if (frame.event === 'done' || frame.event === 'error') {
                                result = JSON.parse(frame.data);
                            } else if (frame.data) {
                                streamed += JSON.parse(frame.data).chunk || '';
                                dmEl.textContent = streamed;
                                scrollNarrative();
                            }
                        }
                    }
                    if (!result || result.retry_status) throw new Error('check durable turn status');
                }
            } catch (error) {
                controller.abort();
                result = await recoverTurn(command);
            } finally {
                clearTimeout(timer);
            }
        }
        if (result.error) {
            turnEl.remove();
            setStatus(result.error, true);
            forgetTurn();
        } else {
            finishTurnUI(result, action, dmEl);
            actionInput.value = '';
            setStatus('');
            forgetTurn();
        }
    } catch (error) {
        if (turnEl) turnEl.remove();
        setStatus(error.message, true);
    } finally {
        submittingTurn = false;
        if (!pendingRoll) {
            actionInput.disabled = false;
            actionInput.focus();
        }
    }
}

async function restorePendingTurn() {
    try {
        const stored = sessionStorage.getItem(TURN_STORAGE_KEY);
        if (!stored) {
            const response = await fetch('/api/game/state');
            if (!response.ok) return;
            const state = await response.json();
            gameId = state.game_id;
            gameStarted = true;
            document.getElementById('startup-screen').classList.add('hidden');
            document.getElementById('game-screen').classList.remove('hidden');
            const narrative = document.createElement('div');
            narrative.className = 'narrative-turn dm-response';
            narrative.style.whiteSpace = 'pre-wrap';
            narrative.textContent = (state.narrative || []).join('\n\n');
            document.getElementById('narrative-content').replaceChildren(narrative);
            await refreshGameState();
            if (!pendingRoll && !gameOver) renderSuggestions('explore');
            return;
        }
        const command = JSON.parse(stored);
        if (!command.action_id || !command.game_id || typeof command.action !== 'string') {
            sessionStorage.removeItem(TURN_STORAGE_KEY);
            return;
        }
        pendingTurn = command;
        gameId = command.game_id;
        gameStarted = true;
        document.getElementById('startup-screen').classList.add('hidden');
        document.getElementById('game-screen').classList.remove('hidden');
        await submitAction({ preventDefault() {} });
        // Recover all current UI state as well (e.g. a die resolved in another tab).
        await refreshGameState();
    } catch (error) {
        setStatus('Could not recover the turn. Check the connection and reload.', true);
    }
}

window.addEventListener('DOMContentLoaded', restorePendingTurn);
