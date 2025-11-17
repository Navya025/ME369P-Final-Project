import cv2
import numpy as np
import time
import os

class CameraFeed():
    def __init__(self):
        params = cv2.SimpleBlobDetector_Params()

        params.minThreshold = 10
        params.maxThreshold = 200

        params.blobColor = 255

        params.filterByArea = True
        params.minArea = 800
        params.maxArea = 2500

        params.filterByCircularity = True 
        params.minCircularity = 0.4

        params.filterByConvexity = True
        params.minConvexity = 0.8
            
        params.filterByInertia = True
        params.minInertiaRatio = 0.4

        self.detector = cv2.SimpleBlobDetector_create(params)

    def begin_feed(self, port):
        self.cap = cv2.VideoCapture(port)

    def close_feed(self):
        self.cap.release()

    def capture_frame(self):
        ret, frame = self.cap.read()
        return frame
    
    def detect_ellipse(self):
        frame = self.capture_frame().copy()
        weights = np.array([0.1, 0.8, 1.0])
        img_float = frame.copy().astype(np.float32)
        gray_custom = np.dot(img_float, weights)
        gray_custom = np.clip(gray_custom, 0, 255).astype(np.uint8)
        gray = gray_custom.copy()
        keypoints = self.detector.detect(frame)

        return frame, gray, keypoints

    def board_state(self):
        columns = 7
        rows = 6
        frame, gray, keypoints = self.detect_ellipse()

        if len(keypoints) != 42:
            return None
        
        params = cv2.CirclesGridFinderParameters()

        revals, centers = cv2.findCirclesGrid(image = gray, 
                                              patternSize=(rows,columns),
                                              flags = cv2.CALIB_CB_SYMMETRIC_GRID,
                                              blobDetector=self.detector,
                                              parameters=params)
        
        if len(centers) != 42:
            return None
        
        board_state = np.zeros((columns,rows))
        pos_array = np.array([[point.pt[0], point.pt[1]] for point in keypoints])
        for i, center in enumerate(centers):
            keypoint_idx = np.argmin(np.linalg.norm(pos_array - center, axis=1))
            keypoint = keypoints[keypoint_idx]
            color = self.average_color(frame, keypoint)
            BG_COLOR = np.array([125,140,150])
            RD_COLOR = np.array([0,22,150])
            YL_COLOR = np.array([8,140,180])
            color_map = np.array([BG_COLOR,RD_COLOR,YL_COLOR])
            color_idx = np.argmin(np.linalg.norm(color_map - color, axis=1))
            board_state[i // rows, i % rows] = color_idx

        return board_state.T
    
    def average_color(self, frame, keypoint):
        x, y = keypoint.pt
        r = int(keypoint.size / 2)

        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (int(x), int(y)), r, 255, -1)

        mean_color = cv2.mean(frame, mask=mask)
        return mean_color[:3] 

feed = CameraFeed()
feed.begin_feed(0)
while True:
    frame, gray, keypoints = feed.detect_ellipse()
    output = cv2.drawKeypoints(frame, keypoints, np.array([]), (0, 0, 255),
                          cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    cv2.imshow("Camera Feed", output)
    cv2.imshow("Computer Vision", gray)
    board_state = feed.board_state()
    os.system('cls')
    print(board_state)
    # time.sleep(0.2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
