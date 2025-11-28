import math
from copy import deepcopy

EMPTY = 0
RED   = 1
YEL   = 2

WIN_SCORE = 1_000_000  # base score for outright wins/losses


def make_board(rows=6, cols=7):
    return [[EMPTY for _ in range(cols)] for _ in range(rows)]


def print_board(board):
    rows, cols = len(board), len(board[0])
    for r in range(rows):
        print(" ".join(str(board[r][c]) for c in range(cols)))
    print("─" * (2*cols-1))
    print(" ".join(str(c) for c in range(cols)))
    print()


def get_valid_locations(board):
    rows, cols = len(board), len(board[0])
    return [c for c in range(cols) if board[0][c] == EMPTY]


def is_valid_location(board, col):
    return board[0][col] == EMPTY


def get_next_open_row(board, col):
    rows, cols = len(board), len(board[0])
    for r in range(rows - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None


def drop_piece_inplace(board, row, col, piece):
    board[row][col] = piece


def drop_piece_copy(board, col, piece):
    if not is_valid_location(board, col):
        return None
    r = get_next_open_row(board, col)
    if r is None:
        return None
    new_b = deepcopy(board)
    new_b[r][col] = piece
    return new_b


def is_winner(board, piece):
    rows, cols = len(board), len(board[0])

    # Horizontal
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True

    # Vertical
    for c in range(cols):
        for r in range(rows - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True

    # Positive diagonal (\)
    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True

    # Negative diagonal (/)
    for r in range(3, rows):
        for c in range(cols - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True

    return False


def is_terminal(board):
    if is_winner(board, RED) or is_winner(board, YEL):
        return True
    if len(get_valid_locations(board)) == 0:
        return True
    return False


def evaluate_window(window, ai_piece):
    """
    Score a 4-cell window for the AI.
    Bigger positive = good for AI, negative = good for opponent.
    """
    opp_piece = RED if ai_piece == YEL else YEL
    score = 0

    ai_count = window.count(ai_piece)
    opp_count = window.count(opp_piece)
    empty_count = window.count(EMPTY)

    # Heuristic weights
    if ai_count == 4:
        score += 10_000


    elif ai_count == 3 and empty_count == 1:
        score += 200
    elif ai_count == 2 and empty_count == 2:
        score += 20

   
    if opp_count == 3 and empty_count == 1:
        score -= 300
    elif opp_count == 2 and empty_count == 2:
        score -= 25

    return score


def count_immediate_wins(board, piece):
    """
    Count how many legal moves for `piece` would result in an immediate win.
    This is used to detect 'double threats' (forks).
    """
    count = 0
    for col in get_valid_locations(board):
        child = drop_piece_copy(board, col, piece)
        if child is not None and is_winner(child, piece):
            count += 1
    return count


def score_position(board, ai_piece):
    """
    Heuristic score of board for ai_piece.
    This is only used when we are NOT at a terminal node.
    """
    rows, cols = len(board), len(board[0])
    opp_piece = RED if ai_piece == YEL else YEL
    score = 0

    
    center_col = cols // 2
    center_array = [board[r][center_col] for r in range(rows)]
    score += center_array.count(ai_piece) * 6


    for r in range(rows):
        row_array = board[r]
        for c in range(cols - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, ai_piece)


    for c in range(cols):
        col_array = [board[r][c] for r in range(rows)]
        for r in range(rows - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, ai_piece)


    for r in range(rows - 3):
        for c in range(cols - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_piece)

    for r in range(3, rows):
        for c in range(cols - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, ai_piece)

    wins_next = count_immediate_wins(board, ai_piece)
    if wins_next >= 2:
        
        score += 6000 * (wins_next - 1)

    opp_wins_next = count_immediate_wins(board, opp_piece)
    if opp_wins_next >= 2:
       
        score -= 6500 * (opp_wins_next - 1)

    return score


def ordered_valid_locations(board):
    """
    Order moves by closeness to center to help alpha-beta and human-like play.
    """
    valid = get_valid_locations(board)
    cols = len(board[0])
    center = cols // 2
    return sorted(valid, key=lambda c: abs(c - center))


def minimax(board, depth, alpha, beta, maximizing_player, ai_piece):
    """
    Depth-aware minimax with alpha-beta pruning.
    Faster wins are scored higher; slower losses are less bad.
    """
    opp_piece = RED if ai_piece == YEL else YEL
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if is_winner(board, ai_piece):
                # Prefer wins that happen earlier 
                return (None, WIN_SCORE + depth)
            elif is_winner(board, opp_piece):
               
                return (None, -WIN_SCORE - depth)
            else:
                # Draw
                return (None, 0)
        else:
            
            return (None, score_position(board, ai_piece))

    valid_locations = ordered_valid_locations(board)

    if maximizing_player:
        value = -math.inf
        best_col = valid_locations[0]  

        for col in valid_locations:
            child = drop_piece_copy(board, col, ai_piece)
            if child is None:
                continue

            _, new_score = minimax(child, depth-1, alpha, beta, False, ai_piece)

            if new_score > value:
                value = new_score
                best_col = col

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return best_col, value

    else:
        value = math.inf
        best_col = valid_locations[0]

        for col in valid_locations:
            child = drop_piece_copy(board, col, opp_piece)
            if child is None:
                continue

            _, new_score = minimax(child, depth-1, alpha, beta, True, ai_piece)

            if new_score < value:
                value = new_score
                best_col = col

            beta = min(beta, value)
            if beta <= alpha:
                break

        return best_col, value


def choose_best_move(board, ai_piece=YEL, depth=5):
    """
    Top-level API: returns (best_column, score).

    - First, check for any **immediate winning move** and take it.
    - Otherwise, run minimax.
    """
    rows, cols = len(board), len(board[0])

   
    for col in ordered_valid_locations(board):
        child = drop_piece_copy(board, col, ai_piece)
        if child is not None and is_winner(child, ai_piece):
           
            return col, WIN_SCORE + depth


    col, val = minimax(board, depth, -math.inf, math.inf, True, ai_piece)
    return col, val
