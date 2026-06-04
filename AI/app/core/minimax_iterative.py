import random
import time
from .gameNumpy import Game
from .constants import TEAM_ID, TEAMS, ACTIONS_COMBINED, LEVEL_WIN, LEVEL_BRICK, BOARD_SIZE

ZOBRIST_TABLE = {}
def init_zobrist():
    random.seed(42)
    players = ["beatriz", "karin", "claro", "rey"]
    for name in players:
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                ZOBRIST_TABLE[("char", name, y, x)] = random.getrandbits(64)
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            for lvl in range(0, LEVEL_BRICK + 1):
                ZOBRIST_TABLE[("board", y, x, lvl)] = random.getrandbits(64)
    ZOBRIST_TABLE["turn1"] = random.getrandbits(64)
    ZOBRIST_TABLE["turn2"] = random.getrandbits(64)

init_zobrist()

def get_full_zobrist(game):
    h = 0
    for name, (y, x) in game.char_positions.items():
        h ^= ZOBRIST_TABLE[("char", name, y, x)]
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            h ^= ZOBRIST_TABLE[("board", y, x, game.board[y][x])]
    h ^= ZOBRIST_TABLE[f"turn{game.turn_team_id}"]
    return h

# Tabelas Globais
TRANSPOSITION_TABLE = {}
KILLER_MOVES = {}

def get_valid_moves_fast(game):
    valid_moves = []
    current_team_name = TEAM_ID[game.turn_team_id]
    my_chars = TEAMS[current_team_name]
    char_positions = game.char_positions
    board = game.board
    occupied = set(char_positions.values())

    for char_idx, char_name in enumerate(my_chars):
        y, x = char_positions[char_name]
        curr_level = board[y][x]
        for act_idx, act in enumerate(ACTIONS_COMBINED):
            my, mx = act["move"]
            ny, nx = y + my, x + mx
            if 0 <= ny < BOARD_SIZE and 0 <= nx < BOARD_SIZE:
                target_lvl = board[ny][nx]
                if target_lvl < LEVEL_BRICK and target_lvl <= (curr_level + 1) and (ny, nx) not in occupied:
                    uy_off, ux_off = act["upgrade"]
                    uy, ux = ny + uy_off, nx + ux_off
                    if 0 <= uy < BOARD_SIZE and 0 <= ux < BOARD_SIZE:
                        is_build_occupied = False
                        if (uy, ux) == (ny, nx):
                            is_build_occupied = True
                        else:
                            for p_pos in occupied:
                                if p_pos == (uy, ux) and p_pos != (y, x):
                                    is_build_occupied = True
                                    break
                        
                        if board[uy][ux] < LEVEL_BRICK and not is_build_occupied:
                            valid_moves.append(char_idx * 64 + act_idx)
    return valid_moves

def make_move(game, action_id, current_hash):
    team_name = TEAM_ID[game.turn_team_id]
    char_names = TEAMS[team_name]
    char_idx = action_id // 64
    char_name = char_names[char_idx]
    action = ACTIONS_COMBINED[action_id % 64]
    
    old_pos = game.char_positions[char_name]
    ny, nx = old_pos[0] + action["move"][0], old_pos[1] + action["move"][1]
    uy, ux = ny + action["upgrade"][0], nx + action["upgrade"][1]
    
    new_hash = current_hash
    new_hash ^= ZOBRIST_TABLE[("char", char_name, old_pos[0], old_pos[1])]
    new_hash ^= ZOBRIST_TABLE[("char", char_name, ny, nx)]
    
    old_lvl = game.board[uy][ux]
    new_lvl = old_lvl + 1
    new_hash ^= ZOBRIST_TABLE[("board", uy, ux, old_lvl)]
    new_hash ^= ZOBRIST_TABLE[("board", uy, ux, new_lvl)]
    
    new_hash ^= ZOBRIST_TABLE[f"turn{game.turn_team_id}"]
    new_hash ^= ZOBRIST_TABLE[f"turn{3 - game.turn_team_id}"]

    undo_data = {
        "char_name": char_name, "old_pos": old_pos, "upgrade_pos": (uy, ux),
        "old_status": game.status, "old_winner": game.winner
    }
    
    game.char_positions[char_name] = (ny, nx)
    game.board[uy][ux] = new_lvl
    
    # VITÓRIA: Se moveu para o nível 3
    if game.board[ny][nx] == LEVEL_WIN:
        game.status = "FINISHED"
        game.winner = team_name
    
    game.turn_team_id = 3 - game.turn_team_id
    game.turn_count += 1
    return undo_data, new_hash

def unmake_move(game, undo_data):
    game.char_positions[undo_data["char_name"]] = undo_data["old_pos"]
    uy, ux = undo_data["upgrade_pos"]
    game.board[uy][ux] -= 1
    game.status = undo_data["old_status"]
    game.winner = undo_data["old_winner"]
    game.turn_team_id = 3 - game.turn_team_id
    game.turn_count -= 1

def evaluate_board(game, team_id):
    """HEURÍSTICA AGRESSIVA OTIMIZADA"""
    if game.status == "FINISHED":
        if game.winner == TEAM_ID[team_id]: return 1000000
        else: return -1000000

    score = 0
    my_team_name = TEAM_ID[team_id]
    enemy_team_name = TEAM_ID[3 - team_id]
    board = game.board
    char_positions = game.char_positions
    
    # 1. Minha Altura (Agressividade)
    for name in TEAMS[my_team_name]:
        y, x = char_positions[name]
        lvl = board[y][x]
        score += lvl * 400
        if lvl == 2: score += 500
        if lvl == 3: score += 10000 # Vitória imediata
        
        # bonus por proximidade do centro
        score += (2 - max(abs(y-2), abs(x-2))) * 50

    for name in TEAMS[enemy_team_name]:
        y, x = char_positions[name]
        lvl = board[y][x]
        score -= lvl * 300
        if lvl == 3: score -= 9000 

    return score

def minimax_alpha_beta(game, depth, alpha, beta, is_maximizing, team_id, start_time, time_limit, current_hash, killers):
    if time.time() - start_time > time_limit: raise TimeoutError()

    if current_hash in TRANSPOSITION_TABLE:
        cached_d, cached_v, cached_m = TRANSPOSITION_TABLE[current_hash]
        if cached_d >= depth: return cached_v, cached_m

    if depth == 0 or game.status == "FINISHED":
        return evaluate_board(game, team_id), None

    valid_moves = get_valid_moves_fast(game)
    if not valid_moves: return evaluate_board(game, team_id), None

    pv_move = None
    if current_hash in TRANSPOSITION_TABLE: pv_move = TRANSPOSITION_TABLE[current_hash][2]
    
    depth_killers = killers.get(depth, [])
    def move_priority(m):
        if m == pv_move: return 100000
        if m in depth_killers: return 10000
        char_idx, act_idx = m // 64, m % 64
        char_name = TEAMS[TEAM_ID[game.turn_team_id]][char_idx]
        pos = game.char_positions[char_name]
        off = ACTIONS_COMBINED[act_idx]["move"]
        return game.board[pos[0]+off[0]][pos[1]+off[1]] * 100

    valid_moves.sort(key=move_priority, reverse=True)
    best_move = valid_moves[0]

    first_move = True
    if is_maximizing:
        max_v = -float('inf')
        for m in valid_moves:
            undo, next_hash = make_move(game, m, current_hash)
            try:
                if first_move:
                    v, _ = minimax_alpha_beta(game, depth-1, alpha, beta, False, team_id, start_time, time_limit, next_hash, killers)
                else:
                    v, _ = minimax_alpha_beta(game, depth-1, alpha, alpha+1, False, team_id, start_time, time_limit, next_hash, killers)
                    if v > alpha and v < beta:
                        v, _ = minimax_alpha_beta(game, depth-1, v, beta, False, team_id, start_time, time_limit, next_hash, killers)
                
                unmake_move(game, undo)
                if v > max_v:
                    max_v = v
                    best_move = m
                alpha = max(alpha, v)
                first_move = False
                if beta <= alpha:
                    killers[depth] = ([m] + depth_killers)[:2]
                    break
            except TimeoutError: unmake_move(game, undo); raise TimeoutError()
        TRANSPOSITION_TABLE[current_hash] = (depth, max_v, best_move)
        return max_v, best_move
    else:
        min_v = float('inf')
        for m in valid_moves:
            undo, next_hash = make_move(game, m, current_hash)
            try:
                if first_move:
                    v, _ = minimax_alpha_beta(game, depth-1, alpha, beta, True, team_id, start_time, time_limit, next_hash, killers)
                else:
                    v, _ = minimax_alpha_beta(game, depth-1, beta-1, beta, True, team_id, start_time, time_limit, next_hash, killers)
                    if v < beta and v > alpha:
                        v, _ = minimax_alpha_beta(game, depth-1, alpha, v, True, team_id, start_time, time_limit, next_hash, killers)
                
                unmake_move(game, undo)
                if v < min_v:
                    min_v = v
                    best_move = m
                beta = min(beta, v)
                first_move = False
                if beta <= alpha:
                    killers[depth] = ([m] + depth_killers)[:2]
                    break
            except TimeoutError: unmake_move(game, undo); raise TimeoutError()
        TRANSPOSITION_TABLE[current_hash] = (depth, min_v, best_move)
        return min_v, best_move

def iterative_deepening_minimax(game, team_id, time_limit=4.0):
    global TRANSPOSITION_TABLE
    if len(TRANSPOSITION_TABLE) > 1000000: TRANSPOSITION_TABLE = {}
    killers = {}
    
    start_time = time.time()
    current_hash = get_full_zobrist(game)
    v_moves = get_valid_moves_fast(game)
    if not v_moves: return None, 0
    best_m = v_moves[0]

    depth = 1
    while True:
        try:
            _, m = minimax_alpha_beta(game, depth, -float('inf'), float('inf'), True, team_id, start_time, time_limit, current_hash, killers)
            if m is not None: best_m = m
            depth += 1
            if depth > 40: break
        except TimeoutError: 
            depth -= 1
            break
    return best_m, depth

def play_match(time_limit=4.0, match_num=1):
    game = Game()
    game.start()
    while game.status == "PLAYING":
        if game.turn_team_id == 1:
            move, depth = iterative_deepening_minimax(game, 1, time_limit=time_limit)
        else:
            v = get_valid_moves_fast(game)
            move = random.choice(v) if v else None
            
        if move is not None:
           
            try:
                game.apply_action(move)
            except AttributeError:
                undo, _ = make_move(game, move, 0)
                pass
        else:
            break
    print(f"Rodada {match_num}: Vencedor: {game.winner}")
    return game.winner

if __name__ == "__main__":
    results = {TEAM_ID[1]: 0, TEAM_ID[2]: 0}
    for i in range(1, 6):
        w = play_match(time_limit=4.0, match_num=i)
        if w: results[w] = results.get(w, 0) + 1
    print(f"\nResultados: {results}")
