import argparse
import time
import cv2
import mss
import numpy as np
import pyautogui
import pygetwindow as gw
import pytesseract
import torch
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.atari_wrappers import WarpFrame
from stable_baselines3.common.vec_env import DummyVecEnv
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DEFAULT_WINDOW_TITLE = "AutoGamer AI - Airstriker-Genesis (Ubuntu-22.04)" # Title of the window to capture
TARGET_FPS = 10 # fps for capturing and displaying frames

SCORE_REGION_COORDS = {'left': 470, 'top': 95, 'width': 150, 'height': 50} 
LIVES_REGION_COORDS = {'left': 230, 'top': 95, 'width': 50, 'height': 50} 
GAME_OVER_REGION_COORDS = {'left': 390, 'top': 410, 'width': 220, 'height': 40} 

# For visual preprocessing example (like WarpFrame)
FRAME_WIDTH = 84
FRAME_HEIGHT = 84

class WindowCaptureDisplay:
    """Handles finding window, capturing frames, performing OCR, and displaying."""
    def __init__(self, window_title):
        self.window_title = window_title
        self.window = None
        self.sct = mss.mss()
        self.monitor = None
        self.score_region = SCORE_REGION_COORDS
        self.lives_region = LIVES_REGION_COORDS
        self.game_over_region = GAME_OVER_REGION_COORDS

        if not self._find_window():
            print(f"Warning: Window '{self.window_title}' not found on initialization.")

    def _find_window(self):
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                self.window = windows[0]
                # Check if window is valid and not minimized
                if self.window.width > 0 and self.window.height > 0 and not self.window.isMinimized:
                    self.monitor = {'top': self.window.top, 'left': self.window.left, 
                                    'width': self.window.width, 'height': self.window.height}
                    print(f"Found window: '{self.window_title}' at L:{self.monitor['left']}, T:{self.monitor['top']}, W:{self.monitor['width']}, H:{self.monitor['height']}")
                    return True
                else:
                    # Found window but it's minimized or invalid size
                    print(f"Window '{self.window_title}' found but is minimized or has invalid dimensions.")
                    self.window = None # Reset window if not usable
                    self.monitor = None
                    return False
            else:
                self.window = None
                self.monitor = None
                return False
        except Exception as e:
            print(f"Error finding window '{self.window_title}': {e}")
            self.window = None
            self.monitor = None
            return False

    def capture_frame(self):
        if not self.window or not self.monitor or self.window.isMinimized:
            if not self._find_window(): # Try to find it again
                return None
            if not self.window or not self.monitor or self.window.isMinimized: # Still not found or invalid
                 # print("Target window not available for capture.")
                return None
        
        # Update monitor dictionary if window moved/resized (basic check)
        if self.window.top != self.monitor['top'] or \
           self.window.left != self.monitor['left'] or \
           self.window.width != self.monitor['width'] or \
           self.window.height != self.monitor['height']:
            if not self._find_window(): # Re-find to update coordinates
                return None

        try:
            sct_img = self.sct.grab(self.monitor)
            frame = np.array(sct_img)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame_bgr
        except mss.exception.ScreenShotError as e:
            print(f"MSS ScreenShotError: {e}. Window might be closed or obstructed.")
            # Attempt to re-find the window as it might have been closed and reopened, or its state changed.
            self._find_window()
            return None
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None

    def _crop_region(self, frame, region_dict):
        if frame is None or region_dict is None: return None
        h, w, _ = frame.shape
        x1, y1 = region_dict['left'], region_dict['top']
        crop_w, crop_h = region_dict['width'], region_dict['height']
        
        # Adjust relative coordinates to absolute if they are based on the captured window size
        # Assuming region_dict provides coordinates relative to the captured window
        abs_x1 = x1
        abs_y1 = y1

        abs_x2 = abs_x1 + crop_w
        abs_y2 = abs_y1 + crop_h

        # Ensure crop coordinates are within the frame dimensions
        abs_x1, abs_y1 = max(0, abs_x1), max(0, abs_y1)
        abs_x2, abs_y2 = min(w, abs_x2), min(h, abs_y2)

        if abs_x1 >= abs_x2 or abs_y1 >= abs_y2:
            # print(f"Cannot crop region {region_dict}, invalid dimensions after boundary check.")
            return None
        return frame[abs_y1:abs_y2, abs_x1:abs_x2]


    def _preprocess_for_ocr(self, img_region): #
        if img_region is None or img_region.size == 0: return None
        gray = cv2.cvtColor(img_region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # You might want to add more preprocessing here like blurring or morphology
        # kernel = np.ones((1, 1), np.uint8)
        # thresh = cv2.dilate(thresh, kernel, iterations=1)
        # thresh = cv2.erode(thresh, kernel, iterations=1)
        return thresh

    def _parse_ocr_number(self, text): #
        import re
        numbers = re.findall(r'\d+', text)
        try:
            return int("".join(numbers)) if numbers else None
        except ValueError:
            return None

    def perform_ocr_on_regions(self, frame):
        ocr_results = {}
        if frame is None:
            return {"score_text": "N/A", "lives_text": "N/A", "game_over_text": "N/A"}

        # Score OCR
        score_img_cropped = self._crop_region(frame, self.score_region)
        processed_score_img = self._preprocess_for_ocr(score_img_cropped)
        if processed_score_img is not None:
            try:
                score_text = pytesseract.image_to_string(processed_score_img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                ocr_results['score_text'] = score_text.strip()
                # ocr_results['score_value'] = self._parse_ocr_number(score_text)
            except Exception as e:
                # print(f"Score OCR error: {e}")
                ocr_results['score_text'] = "OCR Error"
        else:
            ocr_results['score_text'] = "No Score Img"

        # Lives OCR
        lives_img_cropped = self._crop_region(frame, self.lives_region)
        processed_lives_img = self._preprocess_for_ocr(lives_img_cropped)
        if processed_lives_img is not None:
            try:
                lives_text = pytesseract.image_to_string(processed_lives_img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                ocr_results['lives_text'] = lives_text.strip()
                # ocr_results['lives_value'] = self._parse_ocr_number(lives_text)
            except Exception as e:
                # print(f"Lives OCR error: {e}")
                ocr_results['lives_text'] = "OCR Error"
        else:
            ocr_results['lives_text'] = "No Lives Img"

        # Game Over OCR
        game_over_img_cropped = self._crop_region(frame, self.game_over_region)
        processed_game_over_img = self._preprocess_for_ocr(game_over_img_cropped)
        if processed_game_over_img is not None:
            try:
                game_over_text = pytesseract.image_to_string(processed_game_over_img, config='--psm 6') # Wider region, more general text
                ocr_results['game_over_text'] = game_over_text.strip()
            except Exception as e:
                # print(f"Game Over OCR error: {e}")
                ocr_results['game_over_text'] = "OCR Error"
        else:
            ocr_results['game_over_text'] = "No GO Img"
            
        return ocr_results

    def draw_ocr_regions(self, display_frame):
        if display_frame is None: return
        # Score Region
        sr = self.score_region
        cv2.rectangle(display_frame, (sr['left'], sr['top']), 
                      (sr['left'] + sr['width'], sr['top'] + sr['height']), 
                      (0, 255, 0), 1) # Green
        cv2.putText(display_frame, "Score", (sr['left'], sr['top'] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        # Lives Region
        lr = self.lives_region
        cv2.rectangle(display_frame, (lr['left'], lr['top']), 
                      (lr['left'] + lr['width'], lr['top'] + lr['height']), 
                      (255, 0, 0), 1) # Blue
        cv2.putText(display_frame, "Lives", (lr['left'], lr['top'] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        # Game Over Region
        go = self.game_over_region
        cv2.rectangle(display_frame, (go['left'], go['top']), 
                      (go['left'] + go['width'], go['top'] + go['height']), 
                      (0, 0, 255), 1) # Red
        cv2.putText(display_frame, "Game Over", (go['left'], go['top'] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

    def preprocess_frame_for_agent(self, frame):
        """Applies WarpFrame-like preprocessing."""
        if frame is None:
            # Return a black frame of the target size
            return np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)

        # 1. Convert to Grayscale (WarpFrame does this effectively)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif len(frame.shape) == 3 and frame.shape[2] == 4: # BGRA
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        elif len(frame.shape) == 2: # Already grayscale
            processed_frame = frame
        else: # Unexpected format, return black
            return np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
            
        # 2. Resize
        processed_frame = cv2.resize(processed_frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        return processed_frame # This is a single (H, W) frame

    def close(self):
        self.sct.close()
        cv2.destroyAllWindows()
        print("Capture display closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture, display, and OCR a game window.")
    parser.add_argument("--window_title", type=str, default=DEFAULT_WINDOW_TITLE, 
                        help="Exact title of the window to capture.")
    parser.add_argument("--fps", type=int, default=TARGET_FPS, 
                        help="Target capture and display FPS.")
    args = parser.parse_args()

    capture_tool = WindowCaptureDisplay(args.window_title)
    frame_delay = 1.0 / args.fps if args.fps > 0 else 0
    
    print(f"Starting capture for window: '{args.window_title}'")
    print(f"Displaying OCR regions for Score (Green), Lives (Blue), Game Over (Red).")
    print("Press 'q' in the display window to quit.")

    last_terminal_print_time = time.time()

    try:
        while True:
            loop_start_time = time.time()

            raw_frame = capture_tool.capture_frame()

            if raw_frame is not None:
                display_frame = raw_frame.copy()
                capture_tool.draw_ocr_regions(display_frame)
                
                # Scale display_frame if it's too large for comfortable viewing
                max_display_width = 1000
                h, w, _ = display_frame.shape
                if w > max_display_width:
                    scale_ratio = max_display_width / w
                    new_w = int(w * scale_ratio)
                    new_h = int(h * scale_ratio)
                    display_frame_scaled = cv2.resize(display_frame, (new_w, new_h))
                else:
                    display_frame_scaled = display_frame

                cv2.imshow("Region Display", display_frame_scaled)

                # Perform OCR and get processed agent frame
                ocr_data = capture_tool.perform_ocr_on_regions(raw_frame)
                agent_processed_frame = capture_tool.preprocess_frame_for_agent(raw_frame)

                # Print to terminal periodically
                current_time = time.time()
                if current_time - last_terminal_print_time >= 1.0: # Print every 1 second
                    print("--- OCR Data ---")
                    print(f"  Score Text: '{ocr_data.get('score_text', 'N/A')}'")
                    print(f"  Lives Text: '{ocr_data.get('lives_text', 'N/A')}'")
                    print(f"  Game Over Text: '{ocr_data.get('game_over_text', 'N/A')}'")
                    print("--- Processed Agent Frame Data ---")
                    print(f"  Shape: {agent_processed_frame.shape}, Dtype: {agent_processed_frame.dtype}")
                    print("-" * 30)
                    last_terminal_print_time = current_time

            else:
                # Handle case where frame is None (window not found/minimized)
                # You could display a placeholder or just skip cv2.imshow
                # print("Waiting for window...") # Avoid flooding console
                time.sleep(0.5) # Wait a bit before retrying find_window implicitly in next capture_frame

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            elapsed = time.time() - loop_start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Exiting due to KeyboardInterrupt.")
    finally:
        capture_tool.close()
