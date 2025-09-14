import argparse
import time
import cv2 # For preprocessing (used by WarpFrame)
import numpy as np
import pygame # For display and input
import pytesseract # For OCR
import retro # Import the gym-retro library
import signal # To handle termination gracefully
import sys
import gymnasium as gym # Use Gymnasium standard
from gymnasium import spaces
from collections import deque # For frame stacking
# Removed PPO and DummyVecEnv imports
from stable_baselines3.common.atari_wrappers import WarpFrame
import os

# --- OCR Configuration ---
# IMPORTANT: Ensure Tesseract OCR is installed in your WSL environment:
# sudo apt update && sudo apt install tesseract-ocr
# If Tesseract is installed elsewhere, set the command path explicitly:
# pytesseract.pytesseract.tesseract_cmd = r'/path/to/your/tesseract'
# --- End OCR Configuration ---

# --- Configuration ---
DEFAULT_GAME = "Airstriker-Genesis"
DEFAULT_STATE = retro.State.DEFAULT
DISPLAY_SCALE = 3 # Scale factor for the game window
TARGET_FPS = 60 # Target FPS for the main loop (emulator runs at 60)
FRAME_WIDTH = 84 # Target width for processed frames
FRAME_HEIGHT = 84 # Target height for processed frames
NUM_STACKED_FRAMES = 4 # Number of frames to stack for state

# --- Genesis Controller Mapping (Pygame Keys) ---
PYGAME_KEY_MAP = {
    pygame.K_x: 0, pygame.K_z: 1, pygame.K_TAB: 2, pygame.K_RETURN: 3,
    pygame.K_UP: 4, pygame.K_DOWN: 5, pygame.K_LEFT: 6, pygame.K_RIGHT: 7,
    pygame.K_c: 8, pygame.K_a: 9, pygame.K_s: 10, pygame.K_d: 11,
}
# ---

# --- Global variables ---
base_env_global = None # Use separate name to avoid conflict with vec_env 'env'
# vec_env_global = None # Removed VecEnv
processed_env_global = None # Keep track of the fully wrapped env
pygame_initialized = False
screen = None
running = True # Global flag to control main loop

def signal_handler(sig, frame):
    """Handles termination signals like Ctrl+C."""
    global running
    print('Termination signal received, shutting down...')
    running = False # Signal the main loop to stop

# --- OCR Helper Functions ---
# (parse_ocr_number, preprocess_for_ocr, crop_region remain the same)
def parse_ocr_number(text):
    import re
    numbers = re.findall(r'\d+', text)
    try: return int("".join(numbers)) if numbers else None
    except ValueError: return None

def preprocess_for_ocr(img_region):
    if img_region is None or img_region.size == 0: return None
    gray = cv2.cvtColor(img_region, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return thresh

def crop_region(frame, region_dict):
    if frame is None: return None
    if len(frame.shape) != 3: return None
    h, w, _ = frame.shape
    x1, y1 = region_dict['left'], region_dict['top']
    x2, y2 = x1 + region_dict['width'], y1 + region_dict['height']
    x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(w, x2), min(h, y2)
    if x1 >= x2 or y1 >= y2: return None
    return frame[y1:y2, x1:x2]

# --- Custom Gymnasium Wrappers ---
# (CustomRewardWrapper and VisualPreprocessingWrapper remain the same)
# Note: CustomRewardWrapper is kept mainly to easily access the raw frame
# before preprocessing for display purposes. OCR logic within it is optional now.
class CustomRewardWrapper(gym.Wrapper):
    """
    Wrapper primarily used here to store the raw frame before preprocessing.
    Also performs OCR for demonstration.
    """
    def __init__(self, env):
        super().__init__(env)
        self.current_raw_frame = None
        self.last_score = 0
        self.last_lives = 3
        # --- OCR Regions ---
        self.lives_region_coords = {'left': 70, 'top': 13, 'width': 10, 'height': 12}
        self.score_region_coords = {'left': 150, 'top': 13, 'width': 30, 'height': 12}
        # ---

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        if observation is not None: self.current_raw_frame = observation.copy()
        else: self.current_raw_frame = None
        # OCR is done externally in the loop now if desired
        return observation, reward, terminated, truncated, info # Return original reward/done

    def reset(self, **kwargs):
        observation, info = self.env.reset(**kwargs)
        if observation is not None: self.current_raw_frame = observation.copy()
        else: self.current_raw_frame = None
        self.last_score = 0; self.last_lives = 3
        # Optional: Initial OCR read
        score, lives = self._perform_ocr(self.current_raw_frame)
        info['ocr_score'] = score if score is not None else self.last_score
        info['ocr_lives'] = lives if lives is not None else self.last_lives
        return observation, info

    def _perform_ocr(self, frame): # Keep OCR logic internal if needed later
        current_score = None; current_lives = None
        if frame is None: return None, None
        try:
            score_img = crop_region(frame, self.score_region_coords)
            processed_score_img = preprocess_for_ocr(score_img)
            if processed_score_img is not None:
                score_text = pytesseract.image_to_string(processed_score_img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                current_score = parse_ocr_number(score_text)
            lives_img = crop_region(frame, self.lives_region_coords)
            processed_lives_img = preprocess_for_ocr(lives_img)
            if processed_lives_img is not None:
                 lives_text = pytesseract.image_to_string(processed_lives_img, config='--psm 7 -c tessedit_char_whitelist=0123456789')
                 current_lives = parse_ocr_number(lives_text)
        except pytesseract.TesseractNotFoundError:
             if not hasattr(self, '_tesseract_error_printed'): print("OCR Error: Tesseract not found."); self._tesseract_error_printed = True
             return None, None
        except Exception as e: print(f"OCR error: {e}")
        return current_score, current_lives

class VisualPreprocessingWrapper(gym.ObservationWrapper):
    """ Applies WarpFrame (resize+grayscale) and Frame Stacking. """
    def __init__(self, env, width=FRAME_WIDTH, height=FRAME_HEIGHT, num_stacked=NUM_STACKED_FRAMES):
        super().__init__(env)
        self._width = width; self._height = height; self._num_stacked = num_stacked
        self._frames = deque([], maxlen=num_stacked)
        self.observation_space = spaces.Box(low=0, high=255, shape=(self._num_stacked, self._height, self._width), dtype=np.uint8)
        class DummyWarpEnv(gym.Env):
             def __init__(self, obs_shape): self.observation_space = spaces.Box(low=0, high=255, shape=obs_shape, dtype=np.uint8); self.action_space = spaces.Discrete(1)
             def step(self, action): return self.observation_space.sample(), 0, False, False, {}
             def reset(self, seed=None, options=None): return self.observation_space.sample(), {}
        try: initial_shape = env.observation_space.shape
        except AttributeError: initial_shape = (240, 320, 3)
        self._warp_frame = WarpFrame(DummyWarpEnv(initial_shape), width=self._width, height=self._height)

    def observation(self, observation):
        if observation is None: processed = np.zeros((self._height, self._width), dtype=np.uint8)
        else:
            if len(observation.shape) == 2: observation = cv2.cvtColor(observation, cv2.COLOR_GRAY2RGB)
            elif observation.shape[2] == 4: observation = cv2.cvtColor(observation, cv2.COLOR_BGRA2RGB)
            self._warp_frame.observation_space = spaces.Box(low=0, high=255, shape=observation.shape, dtype=np.uint8)
            processed_with_channel = self._warp_frame.observation(observation)
            processed = np.squeeze(processed_with_channel)
            if len(processed.shape) == 3 and processed.shape[-1] == 1: processed = np.squeeze(processed, axis=-1)
            if processed.shape != (self._height, self._width): processed = cv2.resize(processed, (self._width, self._height), interpolation=cv2.INTER_AREA)
        self._frames.append(processed)
        return processed # Return single (H, W) frame

    def _get_observation(self):
        assert len(self._frames) == self._num_stacked, f"Frame stack size incorrect: {len(self._frames)} != {self._num_stacked}"
        return np.array(self._frames, dtype=np.uint8)

    def reset(self, **kwargs):
        observation, info = self.env.reset(**kwargs)
        processed = self.observation(observation)
        for _ in range(self._num_stacked - 1): self._frames.append(processed)
        return self._get_observation(), info

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        _ = self.observation(observation)
        return self._get_observation(), reward, terminated, truncated, info
# --- End Wrappers ---


# --- Main Game Loop Function ---
def run_game_loop(game, state, fps, args):
    """Runs the main game loop with Pygame display/input and visual pipeline."""
    global base_env_global, processed_env_global, pygame_initialized, screen, running
    frame_delay = 1.0 / fps if fps > 0 else 0
    last_print_time = time.time()

    try:
        print(f"Attempting to launch game: {game}, state: {state}")
        # 1. Create base environment
        base_env_global = retro.make(game=game, state=state, render_mode="rgb_array")

        # 2. Wrap for accessing raw frame
        reward_env = CustomRewardWrapper(base_env_global) # Using this just to easily get raw frame

        # 3. Wrap for Visual Preprocessing
        processed_env_global = VisualPreprocessingWrapper(reward_env, width=FRAME_WIDTH, height=FRAME_HEIGHT, num_stacked=NUM_STACKED_FRAMES)
        env = processed_env_global # Use the fully wrapped env for stepping

        print("Environment stack initialized.")
        print(f"Action Space: {env.action_space}")
        print(f"Observation Space (Processed): {env.observation_space.shape} {env.observation_space.dtype}")

        # Initialize Pygame
        initial_obs_render, _ = base_env_global.reset()
        if initial_obs_render is None: raise Exception("Failed to get initial frame for Pygame setup.")
        frame_height_render, frame_width_render, _ = initial_obs_render.shape
        window_size = (frame_width_render * DISPLAY_SCALE, frame_height_render * DISPLAY_SCALE)
        pygame.init(); pygame.display.set_caption(f"AutoGamer AI - {game}"); screen = pygame.display.set_mode(window_size); pygame_initialized = True
        print("Pygame window initialized.")

        # --- Manual Control / Display Loop ---
        print("\n--- Running Manual Control Loop (Use Keyboard, ESC to Quit) ---")
        processed_obs, info = env.reset() # Get initial processed observation

        while running:
            loop_start_time = time.time()

            # --- Pygame Input Handling ---
            manual_action = np.zeros(env.action_space.shape, dtype=env.action_space.dtype)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False; break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False; break
            if not running: break

            pressed_keys = pygame.key.get_pressed()
            for key_code, action_index in PYGAME_KEY_MAP.items():
                if pressed_keys[key_code]:
                    manual_action[action_index] = 1
            # --- End Input Handling ---

            # --- Step Environment with Manual Action ---
            processed_obs, reward, terminated, truncated, info = env.step(manual_action)
            done = terminated or truncated
            # ---

            # --- Display & Print Info ---
            # Get the raw frame stored by the reward wrapper for display
            raw_frame_to_display = env.env.current_raw_frame # Access base env frame

            if raw_frame_to_display is not None:
                try:
                    frame_pygame = np.transpose(raw_frame_to_display, (1, 0, 2))
                    game_surface = pygame.surfarray.make_surface(frame_pygame)
                    scaled_surface = pygame.transform.scale(game_surface, window_size)
                    screen.blit(scaled_surface, (0, 0))
                    pygame.display.flip()
                except Exception as e: print(f"Error during Pygame drawing: {e}")

                current_time = time.time()
                if current_time - last_print_time >= 1.0:
                     # Optionally perform OCR here if desired
                     score, lives = env.env._perform_ocr(raw_frame_to_display) # Call OCR on raw frame
                     print(f"[{time.strftime('%H:%M:%S')}] Processed Obs Shape: {processed_obs.shape} | OCR Score: {score} | OCR Lives: {lives} | Env Reward: {reward:.4f}")
                     last_print_time = current_time
            else: print(f"  Warning: Raw frame for display is None.")

            if done:
                print("Episode finished. Resetting...")
                processed_obs, info = env.reset()
            # ---

            # Maintain FPS
            elapsed = time.time() - loop_start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0: time.sleep(sleep_time)
        # --- End Manual Control Loop ---

    except Exception as e: print(f"An error occurred: {e}"); import traceback; traceback.print_exc()
    finally: signal_handler(None, None) # Ensure cleanup

# --- Main Execution ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler); signal.signal(signal.SIGTERM, signal_handler)
    parser = argparse.ArgumentParser(description="Run retro game with Pygame display/input and visual pipeline test (WSL).")
    parser.add_argument("--game", type=str, default=DEFAULT_GAME)
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--fps", type=int, default=TARGET_FPS)
    parser.add_argument("--timesteps", type=int, default=50_000)
    parser.add_argument("--save_freq", type=int, default=10_000)
    parser.add_argument("--model_dir", type=str, default="./wsl_capture_models")
    parser.add_argument("--model_name", type=str, default="ppo_airstriker_wsl_ocr")
    parser.add_argument("--load_model", action="store_true")
    parser.add_argument("--run_only", action="store_true")
    args = parser.parse_args()
    state_arg_value = args.state
    state_to_load = retro.State.DEFAULT if isinstance(args.state, str) and args.state.upper() == 'DEFAULT' else state_arg_value
    run_game_loop(args.game, state_to_load, args.fps, args)
    print("Main script finished.")

