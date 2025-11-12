import numpy as np
from connect4_solver import choose_best_move, YEL  

def to_ai_encoding(cv_board_np: np.ndarray):

    mapping = {0: 0, 1: 2, 2: 1}
    return np.vectorize(mapping.get)(cv_board_np).tolist()

def pretty(board_np):
    s = "\n".join(" ".join(str(x) for x in row) for row in board_np)
    return s + "\n" + "-"*(2*board_np.shape[1]-1) + "\n" + " ".join(str(c) for c in range(board_np.shape[1])) + "\n"

def run_case(name, cv_board_np, expect=None, depth=5):
    board_list = to_ai_encoding(cv_board_np)
    best_col, score = choose_best_move(board_list, ai_piece=YEL, depth=depth)
    print(f"\n=== {name} ===")
    print(pretty(cv_board_np))
    print(f"AI picks column: {best_col} (score={score})")
    if expect is not None:
        print(f"Expected: {expect} -> {'PASS' if best_col == expect else 'CHECK'}")

def main():
    case1 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [1,1,1,0,0,0,0],
    ], dtype=int)
    run_case("Immediate horizontal win (bottom)", case1, expect=3, depth=3)

    case2 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,1,0,0,0,0],
        [0,0,1,0,0,0,0],
        [0,0,1,0,0,0,0],
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Immediate vertical win (col 2)", case2, expect=2, depth=3)

    case3 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,1,0,0,0,0,0],
        [0,0,1,0,0,0,0],
        [0,0,0,1,0,0,0],
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Immediate positive diagonal (\\) win", case3, expect=0, depth=4)

    case4 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0],  # (2,4)
        [0,0,0,1,0,0,0],  # (3,3)
        [0,0,1,0,0,0,0],  # (4,2)
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Immediate negative diagonal (/) win", case4, expect=1, depth=4)

    case5 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [2,2,2,0,0,0,0],
    ], dtype=int)
    run_case("Block opponent horizontal", case5, expect=3, depth=4)

    case6 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0],
        [0,0,0,0,0,2,0],
        [0,0,0,0,0,2,0],
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Block opponent vertical (col 5)", case6, expect=5, depth=4)

    case7 = np.zeros((6,7), dtype=int)
    run_case("Center preference (empty board)", case7, expect=3, depth=3)

    case8 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,2,0,0,0,0],  # some mid support
        [0,1,2,1,0,0,0],  # scattered
        [0,2,1,2,0,0,0],
        [1,1,2,0,2,0,0],
    ], dtype=int)
    run_case("Complex mixed (forky) position", case8, expect=None, depth=5)

    case9 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,1,0,0,0],  # (2,3)=1
        [0,0,0,0,1,0,0],  # (3,4)=1
        [0,0,0,0,0,1,0],  # (4,5)=1
        [0,0,0,0,0,0,0],
    ], dtype=int)
    case9[5,6] = 2  # opponent piece as floor
    case9b = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,1,0,0,0,0,0],  # (2,1)
        [0,0,1,0,0,0,0],  # (3,2)
        [0,0,0,1,0,0,0],  # (4,3)
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Positive diagonal (\\) with proper supports", case9b, expect=0, depth=4)

    case10 = np.array([
        [0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0],  # (2,4)
        [0,0,0,1,0,0,0],  # (3,3)
        [0,0,1,0,0,0,0],  # (4,2)
        [0,0,0,0,0,0,0],
    ], dtype=int)
    run_case("Negative diagonal (/) with proper supports", case10, expect=1, depth=4)

if __name__ == "__main__":
    main()
