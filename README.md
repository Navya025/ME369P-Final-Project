Here is a **single, clean, complete README.md** with **everything included**, including the `requirements.txt` section, fully integrated and formatted.

---

# 📌 Connect 4 Live – Computer Vision + Minimax AI

A fully automated Connect 4 assistant that:

* Uses **computer vision** (OpenCV) to detect the live physical board
* Uses a **minimax AI with alpha–beta pruning** to pick the best move
* Detects **cheating**, illegal moves, and when the first player ignores the AI
* Displays everything in a polished **Tkinter GUI**, including AI move highlights
* Includes an **optional GUI for prerecorded videos** to test the system without a camera

 **Main file to run the live game:** `connect4_gui.py`

---

#  Requirements

Install all dependencies via:

```bash
pip install -r requirements.txt
```

### `requirements.txt`

```txt
numpy
opencv-python
Pillow
```

(`tkinter` comes bundled with Python and does not need to be installed.)

---

# 📁 Project Structure

| File                               | Purpose                                            |
| ---------------------------------- | -------------------------------------------------- |
| `connect4_solver.py`               | Core Connect 4 logic + minimax AI                  |
| `read_board.py`                    | Computer vision pipeline for detecting board state |
| `test_connect-4.py`                | Offline AI tests using synthetic boards            |
| `connect4_gui.py`                  | **Main live webcam GUI**                           |
|         |

---

#  `connect4_solver.py` – Game Logic & Minimax AI

This module contains the Connect 4 rules and the AI strategy.

### Piece Encoding

```
EMPTY = 0
RED   = 1
YEL   = 2
```

### Board Utility Functions

* **`make_board()`** – Creates a 6×7 empty board
* **`print_board()`** – Pretty prints the board with column numbers
* **`get_valid_locations()`** – Returns playable columns
* **`is_valid_location()`** – Checks if a column has space
* **`get_next_open_row()`** – Finds the lowest empty cell
* **`drop_piece_inplace()`** – Modifies the board directly
* **`drop_piece_copy()`** – Returns a modified *copy* (used by minimax)

### Win + Terminal State Checking

* **`is_winner(board, piece)`** – Checks for horizontal, vertical, or diagonal 4-in-a-row
* **`is_terminal(board)`** – True if:

  * Someone has won
  * No moves remain

### Scoring Heuristic

* **`evaluate_window(window, ai_piece)`** – Scores 4-cell windows
* **`score_position(board, ai_piece)`** – Scores entire board based on:

  * Center column priority
  * Threats
  * 2/3/4 in-a-row opportunities

### Minimax + Alpha–Beta Pruning

* **`minimax(...)`** – Full depth-limited minimax search
* **`choose_best_move(board, ai_piece=YEL, depth=5)`** – Picks best column

---

#  `read_board.py` – Computer Vision Detection

This module uses **OpenCV** to turn camera/video frames into a **6×7 numeric board**.

### `CameraFeed` Class

* Blob detection via `SimpleBlobDetector`
* Supports:

  * Webcam index (`0`, `1`, etc.)
  * Video file path (`"test_video.mp4"`)

### Pipeline

1. **Capture frame**
2. **Detect circular blobs** (Connect 4 holes/pieces)
3. **Use `cv2.findCirclesGrid`** to order blobs into a 7×6 grid
4. **Read average color** of each blob
5. **Classify color** into:

   * `0` empty
   * `1` red
   * `2` yellow
6. **Return board as a 6×7 NumPy array**

Includes a debug mode that overlays blobs and prints board state continuously.

---

#  `test_connect-4.py` – AI Unit Tests (No Camera)

This script runs the AI against predefined board scenarios.

It:

* Converts CV-format boards → AI-format
* Runs `choose_best_move()`
* Prints:

  * Test name
  * Board
  * AI’s chosen move
  * Pass/fail if an expected answer is given

Run via:

```bash
python test_connect-4.py
```

---

# 🖥️ `connect4_gui.py` – Main GUI (Live Webcam)

This is the **primary file to run the full game**:

```bash
python connect4_gui.py
```

### Features

* Live webcam feed
* Real-time detection of 42 circles (6 rows × 7 columns)
* Stability filtering (must appear identical for several frames)
* Move detection:

  * Detects exactly *one* new piece
  * No disappearing or recoloring allowed
* Cheating detection:

  * Same player moves twice
  * Multiple changes between frames
  * Removing/adding extra pieces
* Winner detection
* AI move recommendation
* Green highlight above the recommended column
* Timer + turn counter
* "New Game" menu option

### Logic Overview

* `_update_video()` runs at ~30 FPS:

  * Reads frame
  * Runs CV detection
  * Updates stable board
  * Checks for:

    * New piece
    * Cheating
    * Winner
  * Gets AI recommendation
  * Draws highlight circle
  * Updates Tkinter image

---


# ▶How to Run Everything

### 1. Install requirements

```bash
pip install -r requirements.txt
```

### 2. Run the live webcam version (**main**)

```bash
python connect4_gui.py
```
Comment/Uncomment line 483 to run using video stream or live board. 
Test videos are in the Test Videos folder

### 4. Run AI test cases

```bash
pytest -q
```

