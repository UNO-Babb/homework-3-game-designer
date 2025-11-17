from __future__ import annotations
import json
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
STATE_FILE = Path("events.json")

# ----- Game config -----
ROWS = 8
COLS = 10
TOWNHALL_COLOR_DEFAULT = "#8e44ad"  # purple
PLAYER_1 = {"id": 1, "name": "Artist", "color": "#e74c3c"}
PLAYER_2 = {"id": 2, "name": "Business Owner", "color": "#3498db"}

# Compute the 2x2 center block (top-left anchor) for Town Hall
CENTER_R = ROWS // 2 - 1
CENTER_C = COLS // 2 - 1
TOWNHALL_CELLS = {(CENTER_R, CENTER_C), (CENTER_R, CENTER_C + 1),
                  (CENTER_R + 1, CENTER_C), (CENTER_R + 1, CENTER_C + 1)}

DEFAULT_STATE = {
    "game_name": "Fight for Town Hall",
    "setup_text": "",  # under-title story/setup (fill this string if you want text shown)
    "board_rows": ROWS,
    "board_cols": COLS,
    "players": [
        {"id": PLAYER_1["id"], "name": PLAYER_1["name"], "color": PLAYER_1["color"], "score": 0},
        {"id": PLAYER_2["id"], "name": PLAYER_2["name"], "color": PLAYER_2["color"], "score": 0},
    ],
    "turn": PLAYER_1["id"],          # whose turn (player id)
    "pieces": [],                    # list of {"row": int, "col": int, "player": 1|2}
    "bonus_available": False,        # if True, same player may place 1 extra square this round
    "bonus_player": None,            # which player has the bonus (if any)
    "game_over": False,
    "winner": None,                  # 1 or 2 or "tie" or None
    "townhall_color": TOWNHALL_COLOR_DEFAULT
}

def load_state():
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(json.dumps(DEFAULT_STATE))  # deep-ish copy

def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def cell_taken(state, r, c):
    return any(p["row"] == r and p["col"] == c for p in state["pieces"])

def is_townhall_cell(r, c):
    return (r, c) in TOWNHALL_CELLS

def clickable_cell(r, c):
    return (0 <= r < ROWS) and (0 <= c < COLS) and not is_townhall_cell(r, c)

def occupancy_map(state):
    """Return dict[(r,c)] = player_id for quick lookups."""
    occ = {}
    for p in state["pieces"]:
        occ[(p["row"], p["col"])] = p["player"]
    return occ

def count_in_direction(occ, r, c, dr, dc, pid):
    """Count contiguous stones of pid starting at (r,c) and moving (dr,dc) (excluding start)."""
    cnt = 0
    rr, cc = r + dr, c + dc
    while 0 <= rr < ROWS and 0 <= cc < COLS and not is_townhall_cell(rr, cc) and occ.get((rr, cc)) == pid:
        cnt += 1
        rr += dr
        cc += dc
    return cnt

def made_five_in_a_row(state, r, c, pid):
    """Check if placing at (r,c) for pid makes any 5-in-a-row (any orientation)."""
    occ = occupancy_map(state)
    occ[(r, c)] = pid  # include the new stone for evaluation

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        left = count_in_direction(occ, r, c, -dr, -dc, pid)
        right = count_in_direction(occ, r, c, dr, dc, pid)
        if 1 + left + right >= 5:
            return True
    return False

def total_clickable_cells():
    return ROWS * COLS - len(TOWNHALL_CELLS)  # Town Hall occupies 4 cells

def filled_board(state):
    return len(state["pieces"]) >= total_clickable_cells()

def finalize_game_if_complete(state):
    """When the board is full, decide winner by majority of claimed squares, color Town Hall."""
    if not filled_board(state):
        return
    # Count claims
    counts = {PLAYER_1["id"]: 0, PLAYER_2["id"]: 0}
    for p in state["pieces"]:
        counts[p["player"]] += 1
    if counts[PLAYER_1["id"]] > counts[PLAYER_2["id"]]:
        state["winner"] = PLAYER_1["id"]
        state["townhall_color"] = PLAYER_1["color"]
    elif counts[PLAYER_2["id"]] > counts[PLAYER_1["id"]]:
        state["winner"] = PLAYER_2["id"]
        state["townhall_color"] = PLAYER_2["color"]
    else:
        state["winner"] = "tie"
        state["townhall_color"] = TOWNHALL_COLOR_DEFAULT
    state["game_over"] = True

@app.get("/")
def home():
    state = load_state()
    return render_template_string("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{{ state.game_name }}</title>
  <style>
    :root { --gap: 4px; --cell: 46px; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto;}
    body { margin: 20px; background:#fafafa; color:#222; }
    h1 { margin: 0 0 6px; }
    .setup { color:#555; margin: 0 0 16px; min-height: 1.2em; }
    .hud { display:flex; gap:12px; align-items:center; margin: 8px 0 14px; }
    .pill { padding:4px 10px; border-radius:999px; background:#eee; }
    .wrap { display:grid; grid-template-columns: 220px auto 220px; gap: 16px; align-items: start; }
    .sidebar { background:white; border:1px solid #e5e7eb; border-radius:12px; padding:12px; box-shadow:0 1px 2px rgba(0,0,0,.05); display:flex; flex-direction:column; gap:6px; align-items:center; }
    .player-dot { width:18px; height:18px; border-radius:50%; box-shadow:0 1px 3px rgba(0,0,0,.25) inset; }
    .player-name { font-weight:600; }
    .player-score { color:#555; }
    .board-shell { display:flex; flex-direction:column; gap:10px; align-items:center; }
    .grid {   display: grid; grid-gap: var(--gap); grid-template-columns: repeat({{ state.board_cols }}, var(--cell)); grid-auto-rows: var(--cell); width: fit-content; background: #ddd; padding: var(--gap); border-radius: 12px; }
    .cell { width:var(--cell); height:var(--cell); background:white; border-radius:8px; display:flex; align-items:center; justify-content:center; cursor:pointer; user-select:none; transition: transform .05s ease; }
    .cell:hover { transform: scale(1.035); }
    .cell.disabled { cursor:not-allowed; filter: grayscale(30%); }
    .piece { width:70%; height:70%; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,.25) inset; }
    .townhall { background: {{ state.townhall_color }}; border-radius:8px; display:flex; align-items:center; justify-content:center; color:white; font-weight:700; grid-row: span 2; grid-column: span 2; align-self: stretch; justify-self: stretch; font-size: clamp(1.2rem, 2.2vw, 1.6rem); line-height: 1.1; text-align: center; z-index: 2; cursor:not-allowed; }
    .buttons { display:flex; gap:8px; }
    button { padding:6px 10px; border-radius:8px; border:1px solid #ddd; background:white; cursor:pointer;}
    .winner { font-weight:700; }
  </style>
</head>
<body>
  <h1>{{ state.game_name }}</h1>
  <div class="setup">{{ state.setup_text }}</div>

  <div class="hud">
    <div class="pill">Turn: <strong id="turn"></strong></div>
    <div id="status"></div>
    <div class="buttons">
      <button id="resetBtn">Reset</button>
      <button id="saveBtn">Save</button>
      <button id="loadBtn">Load</button>
    </div>
  </div>

  <div class="wrap">
    <aside class="sidebar" id="leftPlayer"></aside>
    <div class="board-shell">
      <div id="grid" class="grid" role="grid" aria-label="Board"></div>
    </div>
    <aside class="sidebar" id="rightPlayer"></aside>
  </div>

  <script>
    const ROWS = {{ state.board_rows }};
    const COLS = {{ state.board_cols }};
    const grid = document.getElementById("grid");
    const turnEl = document.getElementById("turn");
    const statusEl = document.getElementById("status");
    const leftEl = document.getElementById("leftPlayer");
    const rightEl = document.getElementById("rightPlayer");
    const resetBtn = document.getElementById("resetBtn");
    const saveBtn = document.getElementById("saveBtn");
    const loadBtn = document.getElementById("loadBtn");

    // Town Hall anchor (top-left of 2x2) — these are plain integers rendered by Jinja:
    const TH_R = {{ th_r|int }};
    const TH_C = {{ th_c|int }};

    function cellId(r, c) { return `r${r}c${c}`; }

    function renderSidebars() {
      const [p1, p2] = state.players;
      leftEl.innerHTML = `
        <div class="player-dot" style="background:${p1.color}"></div>
        <div class="player-name">${p1.name}</div>
        <div class="player-score">Tiles Owned: ${p1.score}</div>`;
      rightEl.innerHTML = `
        <div class="player-dot" style="background:${p2.color}"></div>
        <div class="player-name">${p2.name}</div>
        <div class="player-score">Tiles Owned: ${p2.score}</div>`;
    }

    function drawBoard() {
        grid.innerHTML = "";

        // build every normal cell
        for (let r = 0; r < ROWS; r++) {
            for (let c = 0; c < COLS; c++) {
            const div = document.createElement("div");
            div.className = "cell";
            div.id = cellId(r, c);
            div.onclick = () => place(r, c);
            if (state.game_over) div.classList.add("disabled");
            grid.appendChild(div);
            }
        }

        // overlay Town Hall spanning 2×2
        const th = document.createElement("div");
        th.className = "townhall";
        th.textContent = "Town Hall";
        th.style.background = state.townhall_color;
        th.style.gridRowStart = TH_R + 1;
        th.style.gridColumnStart = TH_C + 1;
        grid.appendChild(th);

        // render pieces
        for (const p of state.pieces) {
            const cell = document.getElementById(cellId(p.row, p.col));
            if (!cell) continue;
            const piece = document.createElement("div");
            const player = state.players.find(pl => pl.id === p.player);
            piece.className = "piece";
            piece.style.background = player.color;
            piece.title = player.name;
            cell.appendChild(piece);
        }

        const current = state.players.find(pl => pl.id === state.turn);
        turnEl.textContent = `${current.name}`;
        turnEl.style.color = current.color;
        renderSidebars(); // if you have this
        }

    async function fetchState() {
      const res = await fetch("/state");
      state = await res.json();
      drawBoard();
    }

    async function place(r, c) {
      if (state.game_over) return;
      const res = await fetch("/move", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({row: r, col: c})
      });
      if (res.ok) {
        state = await res.json();
        drawBoard();
      } else {
        alert(await res.text());
      }
    }

    resetBtn.onclick = async () => {
      const res = await fetch("/reset", { method: "POST" });
      state = await res.json();
      drawBoard();
    };
    saveBtn.onclick = async () => { await fetch("/save", { method: "POST" }); alert("Saved to events.json"); };
    loadBtn.onclick = async () => { await fetchState(); };

    let state = null;
    fetchState();
  </script>
</body>
</html>
""", state=state, th_r=CENTER_R, th_c=CENTER_C)


@app.get("/state")
def get_state():
    return jsonify(load_state())

@app.post("/save")
def save():
    state = load_state()
    save_state(state)
    return ("", 204)

@app.post("/reset")
def reset():
    state = json.loads(json.dumps(DEFAULT_STATE))
    save_state(state)
    return jsonify(state)

@app.post("/move")
def move():
    payload = request.get_json(force=True)
    r = int(payload["row"])
    c = int(payload["col"])
    state = load_state()

    if state["game_over"]:
        return ("Game is over.", 400)

    if not clickable_cell(r, c):
        return ("That square is not clickable.", 400)
    if cell_taken(state, r, c):
        return ("Cell already taken", 400)

    # Current player
    pid = state["turn"]

    # Place piece
    state["pieces"].append({"row": r, "col": c, "player": pid})

    # +1 score for placement
    for pl in state["players"]:
        if pl["id"] == pid:
            pl["score"] += 1
            break

    # Check 5-in-a-row
    five = made_five_in_a_row(state, r, c, pid)

    # Bonus logic: Grant a single extra placement if 5-in-a-row achieved and no bonus already pending
    if five and not state["bonus_available"]:
        state["bonus_available"] = True
        state["bonus_player"] = pid
        # Do NOT switch turns — same player gets one extra square this round
    else:
        # If a bonus was available and this move was the bonus move, consume it and then switch.
        if state["bonus_available"] and state["bonus_player"] == pid:
            state["bonus_available"] = False
            state["bonus_player"] = None
            # after consuming bonus, switch turn
            state["turn"] = 2 if pid == 1 else 1
        else:
            # normal switch
            state["turn"] = 2 if pid == 1 else 1

    # If board is now full, finalize winner & town hall color
    finalize_game_if_complete(state)

    save_state(state)
    return jsonify(state)

if __name__ == "__main__":
    # Run:  pip install Flask  ->  python BoardGame.py
    app.run(host="0.0.0.0", port=5000, debug=True)
