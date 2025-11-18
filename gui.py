import tkinter as tk
import time

import cv2
import numpy as np
from PIL import Image, ImageTk

from read_board import CameraFeed
from connect4_solver import RED, YEL, choose_best_move, is_winner


class Connect4VideoGUI:
    def __init__(self, root, video_path):
        self.root = root
        self.root.title("Connect 4 Live (Video Feed + AI)")

        # initializing video file 
        self.feed = CameraFeed()
        print(f"[VIDEO MODE] Using video file: {video_path}")
        self.feed.begin_feed(video_path)

        # initialize timer 
        self.start_time = time.time()
        self.timer_running = True

        # initialize turn counter 
        self.turn_number = 0

        # initialize game over flag 
        self.game_over = False

        # initialize frame of reference 
        self.frame_photo = None

        # factors checking for stable board 
        self.stable_frames_required = 5      # number of identical frames to call it "stable"
        self.candidate_board = None          # board_state currently being checked
        self.candidate_frames = 0            # how many consecutive frames matched candidate
        self.stable_board = None             # last stable board
        self.prev_stable_board = None        # previous stable board (used to detect moves)

        # initialize who moved last (for cheating detection) 
        self.last_move_color = None          # RED or YEL

        # initialize first mover 
        self.first_mover_color = None        # set on first detected move

        # move + suggesstion tracking 
        self.last_move_col = None            # column index of last detected move
        self.current_suggested_col = None    # AI suggestion for *this* frame
        self.prev_suggested_col = None       # AI suggestion shown *before* last move

        # building UI, initializing timer + video 
        self._build_ui()
        self._update_timer()
        self._update_video()

        # shuts down when window closes 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # UI stuff 

    def _build_ui(self):
        # manu
        menubar = tk.Menu(self.root)

        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.on_close)
        menubar.add_cascade(label="Game", menu=game_menu)

        self.root.config(menu=menubar)

        # top banner 
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5, fill=tk.X)

        title_label = tk.Label(
            top_frame, text="Connect 4 Live",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)

        self.timer_label = tk.Label(
            top_frame, text="Time: 00:00",
            font=("Helvetica", 14)
        )
        self.timer_label.pack(side=tk.RIGHT, padx=10)

        self.turn_label = tk.Label(
            top_frame, text="Turn: 0",
            font=("Helvetica", 14)
        )
        self.turn_label.pack(side=tk.RIGHT, padx=10)

        # messages 
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5, fill=tk.X)

        self.status_label = tk.Label(
            status_frame,
            text="Initializing video and detection...",
            font=("Helvetica", 12)
        )
        self.status_label.pack()

        self.message_label = tk.Label(
            status_frame,
            text="",
            font=("Helvetica", 11),
            fg="red"
        )
        self.message_label.pack()

        # winner banner 
        self.winner_label = tk.Label(
            status_frame,
            text="",
            font=("Helvetica", 13, "bold"),
            fg="green"
        )
        self.winner_label.pack()

        # video 
        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=5)

    # timer

    def _update_timer(self):
        if not self.timer_running:
            return
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
        self.root.after(1000, self._update_timer)

    # how to make a new game (menu) 
    def new_game(self):
        self.turn_number = 0
        self.turn_label.config(text="Turn: 0")
        self.message_label.config(text="")
        self.winner_label.config(text="")
        self.status_label.config(
            text="New game started. Waiting for first move..."
        )

        # reset stable-board / cheating state
        self.candidate_board = None
        self.candidate_frames = 0
        self.stable_board = None
        self.prev_stable_board = None
        self.last_move_color = None
        self.first_mover_color = None

        # reset move/suggestion tracking
        self.last_move_col = None
        self.current_suggested_col = None
        self.prev_suggested_col = None

        # reset game-over + timer
        self.game_over = False
        self.timer_running = True
        self.start_time = time.time()

    # define color names 

    def _piece_name(self, piece):
        if piece == RED:
            return "Red"
        elif piece == YEL:
            return "Yellow"
        return "Unknown"
    # updating stable board 
    def _update_stable_board(self, board_state):
       
        if board_state is None:
            self.candidate_board = None
            self.candidate_frames = 0
            return False

        if self.candidate_board is None or not np.array_equal(board_state, self.candidate_board):
            self.candidate_board = board_state.copy()
            self.candidate_frames = 1
            return False

        self.candidate_frames += 1

        if self.candidate_frames < self.stable_frames_required:
            return False

        if self.stable_board is None or not np.array_equal(self.stable_board, self.candidate_board):
            self.prev_stable_board = self.stable_board.copy() if self.stable_board is not None else None
            self.stable_board = self.candidate_board.copy()
            return True

        return False
    # cheating detection 
    def _process_move_and_cheating(self, prev_board, curr_board):
      
        if prev_board is None:
            prev_board = np.zeros_like(curr_board)

        new_mask = (prev_board == 0) & (curr_board != 0)
        removed_mask = (prev_board != 0) & (curr_board == 0)
        recolor_mask = (prev_board != 0) & (curr_board != 0) & (prev_board != curr_board)

        new_positions = np.argwhere(new_mask)
        new_count = len(new_positions)

        if new_count != 1 or np.any(removed_mask) or np.any(recolor_mask):
            self.last_move_col = None
            return None, None

        r, c = new_positions[0]
        moved_color = int(curr_board[r, c])
        if moved_color == 0:
            self.last_move_col = None
            return None, None

        self.last_move_col = int(c)

        # finding which color moved first 
        if self.first_mover_color is None:
            self.first_mover_color = moved_color

        self.turn_number += 1
        self.turn_label.config(text=f"Turn: {self.turn_number}")

        cheater_color = None
        if self.last_move_color is not None and moved_color == self.last_move_color:
            cheater_color = moved_color

        self.last_move_color = moved_color

        winner_color = None
        try:
            if is_winner(curr_board.tolist(), moved_color):
                winner_color = moved_color
        except Exception:
            winner_color = None

        return cheater_color, winner_color

    # all video updates 

    def _update_video(self):
      
        if self.game_over:
            # Keeping frames, banners 
            self.root.after(100, self._update_video)
            return

        try:
            frame, gray, keypoints = self.feed.detect_ellipse()
        except Exception as e:
            if self.game_over:
                self.root.after(100, self._update_video)
                return
            self.message_label.config(text=f"Video error: {e}")
            self.root.after(100, self._update_video)
            return

        if frame is None:
            if self.game_over:
                self.root.after(100, self._update_video)
                return
            self.message_label.config(text="End of video or cannot read frame.")
            self.root.after(200, self._update_video)
            return

        # draw detected blobs
        output = cv2.drawKeypoints(
            frame, keypoints, np.array([]),
            (0, 0, 255),
            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        )

        board_state = self.feed.board_state()
        board_positions = self.feed.board_positions()
        stable_changed = self._update_stable_board(board_state)

        if board_state is None and self.stable_board is None:
            self.status_label.config(text="Board not detected.")
            self.message_label.config(
                text="Invalid / incomplete board (need 42 circles). Adjust lighting/position."
            )
        else:
            logic_board = self.stable_board if self.stable_board is not None else board_state

            if logic_board is None:
                self.status_label.config(text="Board not detected.")
            else:
                # checking for new, stable board state 
                if stable_changed:
                    cheater, winner = self._process_move_and_cheating(
                        self.prev_stable_board, self.stable_board
                    )

                    if cheater is not None:
                        color_name = self._piece_name(cheater)
                        self.message_label.config(
                            text=f"Cheating detected: {color_name} played twice in a row!"
                        )
                        self.timer_running = False
                        self.game_over = True

                    if winner is not None:
                        color_name = self._piece_name(winner)
                        self.winner_label.config(
                            text=f"Winner: {color_name}!"
                        )
                        self.timer_running = False
                        self.game_over = True

                    if cheater is None and winner is None:
                        if "Cheating detected" not in self.message_label.cget("text"):
                            self.message_label.config(text="")

                    # flag for ignoring suggestion (first player only)
                    if cheater is None and winner is None:
                        if (
                            self.prev_suggested_col is not None and
                            self.last_move_col is not None and
                            self.first_mover_color is not None and
                            self.last_move_color == self.first_mover_color and
                            self.last_move_col != self.prev_suggested_col
                        ):
                            self.message_label.config(
                                text=(
                                    f"First player ignored AI: played column "
                                    f"{self.last_move_col}, suggested {self.prev_suggested_col}."
                                )
                            )

                # best move, column highlighting
                self.prev_suggested_col = self.current_suggested_col

                try:
                    board_list = logic_board.tolist()
                    best_col, _ = choose_best_move(board_list, ai_piece=YEL, depth=4)
                except Exception as e:
                    best_col = None
                    self.current_suggested_col = None
                    self.status_label.config(text="Error computing AI move.")
                    if "Cheating detected" not in self.message_label.cget("text"):
                        self.message_label.config(text=f"AI error: {e}")
                else:
                    self.current_suggested_col = best_col

                    if best_col is None:
                        self.status_label.config(
                            text="Board detected, but no valid moves (board full or invalid)."
                        )
                        if "Cheating detected" not in self.message_label.cget("text"):
                            self.message_label.config(
                                text="No move available - this position is effectively terminal."
                            )
                    else:
                        self.status_label.config(
                            text=f"Board detected. AI suggests column: {best_col+1}"
                        )

                        try:
                            rows, cols = logic_board.shape
                            col = int(best_col)

                            if keypoints:
                                xs = [kp.pt[0] for kp in keypoints]
                                ys = [kp.pt[1] for kp in keypoints]
                                min_x, max_x = min(xs), max(xs)
                                min_y, max_y = min(ys), max(ys)
                                board_width = max_x - min_x
                                board_height = max_y - min_y

                                cx = int(min_x + (col + 0.5) * board_width / cols)
                                row_height = board_height / rows
                                cy = int(min_y - 0.4 * row_height)
                                cy = max(cy, 0)

                                radius = int(0.4 * (board_width / cols))
                            else:
                                h, w, _ = output.shape
                                cx = int((col + 0.5) * w / cols)
                                cy = int(0.05 * h)
                                radius = int(0.4 * (w / cols))

                            cv2.circle(output, (cx, cy), radius, (0, 255, 0), thickness=3)
                        except Exception as e:
                            if "Cheating detected" not in self.message_label.cget("text"):
                                self.message_label.config(text=f"Highlight error: {e}")

        # Convert to Tk image
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(output_rgb)
        self.frame_photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=self.frame_photo)

        self.root.after(30, self._update_video)

    # closing actions - stop timer 

    def on_close(self):
        self.timer_running = False
        try:
            self.feed.close_feed()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Connect4VideoGUI(root, video_path="test_video_red_cheats.mp4")
    root.mainloop()
