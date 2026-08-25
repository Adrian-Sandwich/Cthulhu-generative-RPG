// THE LIGHTHOUSE — state
//
// Shared client state. Loaded first: classic scripts share one
// top-level lexical scope, so these bindings are visible to every file below.

// THE LIGHTHOUSE - Client Logic

let gameStarted = false;
let gameHistory = [];
let maxHP = null; // Set from server responses (max_hp from the investigator sheet)
let imagePollTimer = null;
let archetypes = {};
let pendingRoll = null;
let rolling = false;
let firstRollSeen = false;   // show the "click the die" tip only once
