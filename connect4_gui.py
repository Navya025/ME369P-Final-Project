import tkinter as tk
import time

import cv2
import numpy as np
from PIL import Image, ImageTk
import simpleaudio as sa



from read_board import CameraFeed
from connect4_solver import RED, YEL, choose_best_move, is_winner

# There are three sections of code to comment/uncomment to switch between a camera port and video file path. 
# 1) Line 24/27 Change object initialization 
# 2) Line 35/42 Change feed initialization 
# 3) Line 495/498 Change camera port/video file path 


class Connect4VideoGUI:
    @staticmethod
    def play_sound_async(path):
        sa.WaveObject.from_wave_file(path).play()
        pass

    def __init__(self, root, video_path):

    # # UNCOMMENT/COMMENT 
    # def __init__(self, root, camera_port = 0): # this line takes in the camera port instead of the video path 
        self.root = root
        self.root.title("Connect 4 Live (Webcam + AI)")
        
        # # UNCOMMENT/COMMENT to switch to camera mode 

        # Initialize camera 
        # self.feed = CameraFeed()
        # print(f"[CAMERA MODE] Using webcam index: {camera_port}") 
        # self.feed.begin_feed(camera_port)
        # #

        # # UNCOMMENT/COMMENT to switch to video file mode 

        # Initialize prerecorded video 
        self.feed = CameraFeed()
        print(f"[VIDEO FILE MODE] Using video path: {video_path}") 
        self.feed.begin_feed(video_path)
        # #

        # Initialize timer
        self.start_time = time.time()
        self.timer_running = True

        # Initialize turn counter
        self.turn_number = 0

        # Initialize game over flag - helps prevent errors once game is over 
        self.game_over = False

        # Initialize reference frame to prevent garbage collector 
        self.frame_photo = None

        # Initialize tracking stable board 
        self.stable_frames_required = 5      # number of identical frames to call it "stable"
        self.candidate_board = None          # board_state currently being checked
        self.candidate_frames = 0            # how many consecutive frames matched candidate
        self.stable_board = None             # last stable board
        self.prev_stable_board = None        # previous stable board (used to detect moves)

        # Initialize last mover - for cheating detection 
        self.last_move_color = None          # RED or YEL

        # Initialize first mover 
        self.first_mover_color = None        # set on first detected move

        # Initialize suggestion tracking 
        self.last_move_col = None            # column index of last detected move
        self.current_suggested_col = None    # AI suggestion for this frame
        self.prev_suggested_col = None       # AI suggestion for last frame 

        # Build UI and start loops
        self._build_ui()
        self._update_timer()
        self._update_video()

        # Shutdown for window close 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # Building UI 
    
    def _build_ui(self):
        # ----- Menu bar -----
        menubar = tk.Menu(self.root)

        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_command(label="Quit", command=self.on_close)
        menubar.add_cascade(label="Game", menu=game_menu)

        self.root.config(menu=menubar)

        # Top banner
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5, fill=tk.X)

        title_label = tk.Label(
            top_frame, text="Connect 4 Live",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10) # pack titel left 

        self.timer_label = tk.Label(
            top_frame, text="Time: 00:00",
            font=("Helvetica", 14)
        )
        self.timer_label.pack(side=tk.RIGHT, padx=10) # pack title right 

        self.turn_label = tk.Label(
            top_frame, text="Turn: 0",
            font=("Helvetica", 14)
        )
        self.turn_label.pack(side=tk.RIGHT, padx=10) # pack title right 

        # Status messages 
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=5, fill=tk.X) 

        self.status_label = tk.Label(
            status_frame,
            text="Initializing camera and detection...",
            font=("Helvetica", 12)
        )
        self.status_label.pack() # at the top, pack() will space things 

        self.message_label = tk.Label(
            status_frame,
            text="",
            font=("Helvetica", 11),
            fg="red"
        )
        self.message_label.pack()

        # Winner banner
        self.winner_label = tk.Label(
            status_frame,
            text="",
            font=("Helvetica", 13, "bold"),
            fg="green"
        )
        self.winner_label.pack() 

        # Video display 
        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=5)

    # Time update - min:sec

    def _update_timer(self):
        if not self.timer_running:
            return
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
        self.root.after(1000, self._update_timer)

    # Initialization of game 

    def new_game(self):
        
        # Initialize/reset turn number, text, etc when new game starts 
        self.turn_number = 0
        self.turn_label.config(text="Turn: 0")
        self.message_label.config(text="")
        self.winner_label.config(text="")
        self.status_label.config(
            text="New game started. Waiting for first move..."
        )

        # Initialize/reset board state 
        self.candidate_board = None
        self.candidate_frames = 0
        self.stable_board = None
        self.prev_stable_board = None
        self.last_move_color = None
        self.first_mover_color = None

        # Initialize/reset suggestion tracking 
        self.last_move_col = None
        self.current_suggested_col = None
        self.prev_suggested_col = None

        # Initialize/reset game voer + timer 
        self.game_over = False
        self.timer_running = True
        self.start_time = time.time()

    
    # Piece names 
    def _piece_name(self, piece):
        if piece == RED:
            return "Red"
        elif piece == YEL:
            return "Yellow"
        return "Unknown"
    
    
    # Plays sound when someone is caught cheating 
    def _play_cheat_sound(self):
        
        try:
            self.play_sound_async("you-cheat.wav")
            print("Cheater sound played!")
        except Exception as e:
            print(f"Error playing cheat sound: {e}")

    # New stable board state update 
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
    # Turn counter, check for same color moving twice 
    def _process_move_and_cheating(self, prev_board, curr_board):
        
        if prev_board is None:
            prev_board = np.zeros_like(curr_board)

        new_board = (prev_board == 0) & (curr_board != 0)
        removed_board = (prev_board != 0) & (curr_board == 0)
        recolor_board = (prev_board != 0) & (curr_board != 0) & (prev_board != curr_board)

        new_positions = np.argwhere(new_board)
        new_count = len(new_positions)

        if new_count != 1 or np.any(removed_board) or np.any(recolor_board):
            self.last_move_col = None
            return None, None

        r, c = new_positions[0]
        moved_color = int(curr_board[r, c])
        if moved_color == 0:
            self.last_move_col = None
            return None, None

        self.last_move_col = int(c)

        # Set first mover color from first move
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
    
    # Helper to find which row to land 
    def _find_landing_row(self, board, col):
        rows, _ = board.shape 
        for r in range(rows - 1, -1, -1):  # bottom to top, iterate through all the rows 
            if board[r, col] == 0: # iterate until the last 0 (or empty spot)
                return r
        return None

    # All video updates 
    def _update_video(self):
    
        if self.game_over:
            # Keep last frame + banners visible
            self.root.after(100, self._update_video)
            return

        try:
            frame, gray, keypoints = self.feed.detect_ellipse()
        except Exception as e:
            if self.game_over:
                self.root.after(100, self._update_video)
                return
            self.message_label.config(text=f"Camera error: {e}")
            self.root.after(100, self._update_video)
            return

        # this section catches errors 
        if frame is None:
            if self.game_over:
                self.root.after(100, self._update_video)
                return
            self.message_label.config(text="No frame from camera. Check connection.") 
            self.root.after(200, self._update_video)
            return

        # Draw detected blobs
        output = cv2.drawKeypoints(
            frame, keypoints, np.array([]),
            (0, 0, 255),
            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        )

        board_state, board_positions = self.feed.board_state()


        stable_changed = self._update_stable_board(board_state)
        
        # Messages to catch incomplete board 

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
                # Check for new AND stable board changes, processes the new board state 
                if stable_changed:
                    cheater, winner = self._process_move_and_cheating(
                        self.prev_stable_board, self.stable_board
                    )

                    if cheater is not None:
                        color_name = self._piece_name(cheater)
                        self.message_label.config(
                            text=f"Cheating detected: {color_name} played twice in a row!"
                        )
                        self._play_cheat_sound() # call to play sound :) 
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

                    # Checks if the person who moved first ignored the suggestion 
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
                                    f"{self.last_move_col+1}, suggested {self.prev_suggested_col+1}."
                                )
                            )
                        

                # Best move + cheating detection 
                if not self.game_over:
                    self.prev_suggested_col = self.current_suggested_col

                    try:
                        board_list = logic_board.tolist()
                        best_col, _ = choose_best_move(board_list, ai_piece=YEL, depth=4)  # call to choose_best_move
                    except Exception as e: # catch exceptions from the solver 
                        best_col = None
                        self.current_suggested_col = None
                        self.status_label.config(text="Error computing AI move.")
                        if "Cheating detected" not in self.message_label.cget("text"):
                            self.message_label.config(text=f"AI error: {e}")
                    else:
                        self.current_suggested_col = best_col

                        if best_col is None:  # potential error msgs 
                            self.status_label.config(
                                text="Board detected, but no valid moves (board full or invalid)."
                            )
                            if "Cheating detected" not in self.message_label.cget("text"):
                                self.message_label.config(
                                    text="No move available - this position is effectively terminal."
                                )
                        else:
                            self.status_label.config(
                                text=f"Board detected. AI suggests column: {best_col+1}" # need to add +1 since indexing starts at 0
                            )

                            try:
                                if logic_board is None or board_positions is None:
                                    raise ValueError("No board positions available for highlight.")

                                rows, cols = logic_board.shape
                                col = int(best_col)
                                if not (0 <= col < cols):
                                    raise ValueError(f"Best column {col} out of bounds.") # ONLY checks for columns 

                                # board_positions[row, col] = (x, y)
                                # row = 0 -> very top row in camera view
                                # cx and cy 
                                cx_top, cy_top = board_positions[0, col]
                                cx_top_i = int(round(cx_top))
                                cy_top_i = int(round(cy_top))

                                # Radius relative to grid spacing
                                if rows > 1:
                                    cy1 = board_positions[0, col][1]
                                    cy2 = board_positions[1, col][1]
                                    cell_h = abs(cy2 - cy1)
                                    radius_i = int(max(8, round(cell_h * 0.35)))
                                else:
                                    radius_i = 20

                                landing_row = self._find_landing_row(logic_board, col)

                                if landing_row is not None:
                                    x_end, y_end = board_positions[landing_row, col]
                                    x_end_i = int(round(x_end))
                                    y_end_i = int(round(y_end))

                                    # Draw arrow from topmost circle to landing circle 
                                    cv2.arrowedLine(
                                        output,
                                        (cx_top_i, cy_top_i),
                                        (x_end_i, y_end_i),
                                        (0, 255, 0),
                                        thickness=2,
                                        tipLength=0.1
                                    )
                                # Circle at top column 
                                cv2.circle(output, (cx_top_i, cy_top_i), radius_i, (0, 255, 0), thickness=-1)

                            except Exception as e:
                                if "Cheating detected" not in self.message_label.cget("text"):
                                    self.message_label.config(text=f"Highlight error: {e}")



        # Convert to Tk image
        output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(output_rgb)
        self.frame_photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=self.frame_photo)

        self.root.after(30, self._update_video)

    # Making sure it closes  

    def on_close(self):
        self.timer_running = False
        try:
            self.feed.close_feed()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # UNCOMMENT/COMMENT to put in a webcam instead of a prerecorded video file 

    # 0 = default webcam, change if needed (1, 2, ...) to whichever port you're using 
    # app = Connect4VideoGUI(root, camera_port=0)

    # UNCOMMENT/COMMENT to put in a prerecorded video file rather than a camera 
    app = Connect4VideoGUI(root, video_path="Test Videos/[VIDEO NAME].mp4")
    root.mainloop()

