import math
import random
from copy import deepcopy


EMPTY = 0
RED   = 1  
YEL   = 2   


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
    for r in range(rows-1, -1, -1):
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

    
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c+i] == piece for i in range(4)):
                return True

   
    for c in range(cols):
        for r in range(rows - 3):
            if all(board[r+i][c] == piece for i in range(4)):
                return True

   
    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True

    
    for r in range(3, rows):
        for c in range(cols - 3):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True

    return False

def is_terminal(board):
    valid = get_valid_locations(board)
    if len(valid) == 0:
        return True
    if is_winner(board, RED) or is_winner(board, YEL):
        return True
    return False

def evaluate_window(window, ai_piece):
    opp_piece = RED if ai_piece == YEL else YEL
    score = 0

    if window.count(ai_piece) == 4:
        score += 100000
    elif window.count(ai_piece) == 3 and window.count(EMPTY) == 1:
        score += 100
    elif window.count(ai_piece) == 2 and window.count(EMPTY) == 2:
        score += 10

   
    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 120  

    return score

def score_position(board, ai_piece):
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

    return score

def minimax(board, depth, alpha, beta, maximizing_player, ai_piece):
    valid_locations = get_valid_locations(board)
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if is_winner(board, ai_piece):
                return (None, math.inf)
            elif is_winner(board, RED if ai_piece == YEL else YEL):
                return (None, -math.inf)
            else:
                return (None, 0)  
        else:
            return (None, score_position(board, ai_piece))

    if maximizing_player:
        value = -math.inf
        best_col = random.choice(valid_locations) 
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
        opp_piece = RED if ai_piece == YEL else YEL
        best_col = random.choice(valid_locations)
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
    col, val = minimax(board, depth, -math.inf, math.inf, True, ai_piece)
    return col, val



