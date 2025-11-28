import pytest

from connect4_solver import (
    EMPTY,
    RED,
    YEL,
    choose_best_move,
    is_winner,
    drop_piece_copy,
    count_immediate_wins,
    score_position,
)


def make_empty_board(rows=6, cols=7):
    return [[EMPTY for _ in range(cols)] for _ in range(rows)]




def test_immediate_horizontal_win_bottom():
  
    board = make_empty_board()
    # bottom row is index 5
    board[5][0] = YEL
    board[5][1] = YEL
    board[5][2] = YEL

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=3)
    assert best_col == 3

    new_board = drop_piece_copy(board, best_col, YEL)
    assert is_winner(new_board, YEL)


def test_immediate_vertical_win():

    board = make_empty_board()

    board[5][2] = YEL
    board[4][2] = YEL
    board[3][2] = YEL

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=3)
    assert best_col == 2

    new_board = drop_piece_copy(board, best_col, YEL)
    assert is_winner(new_board, YEL)


def test_immediate_positive_diagonal_win():
  
    board = make_empty_board()


    board[2][0] = YEL  # (2,0)
    board[3][1] = YEL  # (3,1)
    board[4][2] = YEL  # (4,2)

    board[3][0] = RED  # under (2,0)
    board[4][1] = RED  # under (3,1)
    board[5][2] = RED  # under (4,2)

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=4)
    assert best_col == 3

    new_board = drop_piece_copy(board, best_col, YEL)
    assert is_winner(new_board, YEL)


def test_immediate_negative_diagonal_win():

    board = make_empty_board()


    board[2][6] = YEL  
    board[3][5] = YEL  
    board[4][4] = YEL  

    board[3][6] = RED  
    board[4][5] = RED  
    board[5][4] = RED  

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=4)
    assert best_col == 3

    new_board = drop_piece_copy(board, best_col, YEL)
    assert is_winner(new_board, YEL)




def test_block_opponent_horizontal():

    board = make_empty_board()
    board[5][0] = RED
    board[5][1] = RED
    board[5][2] = RED


    best_col, score = choose_best_move(board, ai_piece=YEL, depth=4)
    assert best_col == 3

    blocked_board = drop_piece_copy(board, best_col, YEL)
    opp_wins_next = count_immediate_wins(blocked_board, RED)
    assert opp_wins_next == 0


def test_block_opponent_vertical():

    board = make_empty_board()
    board[5][5] = RED
    board[4][5] = RED
    board[3][5] = RED

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=4)
    assert best_col == 5

    blocked_board = drop_piece_copy(board, best_col, YEL)
    opp_wins_next = count_immediate_wins(blocked_board, RED)
    assert opp_wins_next == 0




def test_center_preference_on_empty_board():

    board = make_empty_board()
    best_col, score = choose_best_move(board, ai_piece=YEL, depth=3)
    assert best_col == 3




def test_count_immediate_wins_double_threat():

    board = make_empty_board()

    board[5][1] = YEL
    board[4][1] = YEL
    board[3][1] = YEL

    board[5][5] = YEL
    board[4][5] = YEL
    board[3][5] = YEL

    wins_next = count_immediate_wins(board, YEL)
    assert wins_next == 2

    for winning_col in (1, 5):
        child = drop_piece_copy(board, winning_col, YEL)
        assert child is not None
        assert is_winner(child, YEL)


def test_double_threat_board_scored_higher_than_single_threat():


    board_single = make_empty_board()
    board_single[5][1] = YEL
    board_single[4][1] = YEL
    board_single[3][1] = YEL

    wins_single = count_immediate_wins(board_single, YEL)
    assert wins_single == 1

    board_double = [row[:] for row in board_single]
    board_double[5][5] = YEL
    board_double[4][5] = YEL
    board_double[3][5] = YEL

    wins_double = count_immediate_wins(board_double, YEL)
    assert wins_double == 2

    score_single = score_position(board_single, YEL)
    score_double = score_position(board_double, YEL)

    assert score_double > score_single




def test_faster_win_preferred_over_slow_win():

    board = make_empty_board()

    board[5][0] = YEL
    board[5][1] = YEL
    board[5][2] = YEL

    board[4][4] = YEL
    board[3][4] = YEL
    board[2][4] = YEL  

    best_col, score = choose_best_move(board, ai_piece=YEL, depth=5)
    assert best_col == 3

    new_board = drop_piece_copy(board, best_col, YEL)
    assert is_winner(new_board, YEL)
