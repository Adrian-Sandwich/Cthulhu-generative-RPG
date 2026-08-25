// THE LIGHTHOUSE — turn
//
// The turn loop: state refresh, SSE plumbing, and action submission.

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
    if (done.ending) showEnding(done.ending);
    document.getElementById('turn-counter').textContent = done.turn;
    document.getElementById('location-display').textContent = done.location;
    if (done.pending_roll) showDiceArea(done.pending_roll);
    else renderSuggestions('explore');
    refreshGameState();
    maybePromptFeedback(done.turn);
}

// Submit Player Action — streams the DM narration over SSE, falls back to the
// plain JSON endpoint if streaming isn't available.
async function submitAction(event) {
    event.preventDefault();

    const actionInput = document.getElementById('action-input');
    const action = actionInput.value.trim();
    if (!action) return;

    // "Lanza el dado" is a question about the controls, not an action.
    if (ROLL_REQUEST_RE.test(action)) {
        setStatus(pendingRoll
            ? 'Haz click en el dado. / Click the die.'
            : 'Los dados salen solos cuando algo es riesgoso — describe qué haces. '
              + '/ Dice appear on their own when an action is risky — describe what you do.');
        actionInput.select();
        return;
    }

    setStatus('The keeper considers…');
    actionInput.disabled = true;
    hideSuggestions();
    const { turnEl, dmEl } = beginTurn(action);

    // Abort a stalled turn before the tunnel/proxy kills the connection (~100s),
    // so the player gets a clean retry instead of the game appearing to close.
    const ac = new AbortController();
    const watchdog = setTimeout(() => ac.abort(), 90000);

    try {
        const resp = await fetch('/api/game/action/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
            signal: ac.signal
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
        // Streaming failed/timed out — try the plain endpoint; if THAT also
        // fails, keep the game alive with a retry prompt (never a dead UI).
        const ok = await submitActionFallback(action);
        if (!ok) {
            setStatus('The connection wavered. Your action wasn\'t lost — try again.', true);
            renderSuggestions('explore');
        }
    } finally {
        clearTimeout(watchdog);
        if (!pendingRoll) {
            actionInput.disabled = false;
            actionInput.focus();
        }
    }
}

// Non-streaming fallback (original JSON endpoint). Returns true on success so
// the caller can show a retry prompt if this also fails.
async function submitActionFallback(action) {
    const ac = new AbortController();
    const watchdog = setTimeout(() => ac.abort(), 95000);
    try {
        const response = await fetch('/api/game/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
            signal: ac.signal
        });
        const data = await response.json();
        if (data.success) {
            addNarrativeTurn(data.turn, action, data.narrative);
            updateStats(data.state);
            renderNpcs(data.npcs);
            renderResources(data.resources);
            renderCombat(data.combat);
            applySanityFx(data.sanity_corruption || 0);
            if (data.ending) showEnding(data.ending);
            document.getElementById('turn-counter').textContent = data.turn;
            document.getElementById('location-display').textContent = data.location;
            document.getElementById('action-input').value = '';
            setStatus(data.sanity_recovered > 0
                ? `Your mind steadies. +${data.sanity_recovered} SAN` : '');
            if (data.pending_roll) showDiceArea(data.pending_roll);
            else renderSuggestions('explore');
            refreshGameState();
            return true;
        }
        setStatus(data.error || 'Action failed', true);
        return false;
    } catch (error) {
        return false;
    } finally {
        clearTimeout(watchdog);
    }
}
