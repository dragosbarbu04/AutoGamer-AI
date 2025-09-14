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
from stable_baselines3 import PPO # <<< Import PPO
from stable_baselines3.common.vec_env import DummyVecEnv # <<< Import VecEnv
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
# This map is now only used for potential debug/manual override, not primary control
PYGAME_KEY_MAP = {
    pygame.K_x: 0, pygame.K_z: 1, pygame.K_TAB: 2, pygame.K_RETURN: 3,
    pygame.K_UP: 4, pygame.K_DOWN: 5, pygame.K_LEFT: 6, pygame.K_RIGHT: 7,
    pygame.K_c: 8, pygame.K_a: 9, pygame.K_s: 10, pygame.K_d: 11,
}
# ---

# --- Global variables ---
base_env_global = None # Keep track of the base env for raw frames
processed_env_global = None # Keep track of the fully wrapped env for SB3
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
class CustomRewardWrapper(gym.Wrapper):
    """ Wrapper to calculate reward based on OCR and store raw frame. """
    def __init__(self, env):
        super().__init__(env)
        self.current_raw_frame = None; self.last_score = 0; self.last_lives = 3
        self.score_region_coords = {'left': 150, 'top': 13, 'width': 30, 'height': 12} # Airstriker Score
        self.lives_region_coords = {'left': 70, 'top': 13, 'width': 10, 'height': 12} # Airstriker Lives
        self.game_over_region_coords = {'left': 100, 'top': 100, 'width': 150, 'height': 30} # Example

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        if observation is not None: self.current_raw_frame = observation.copy()
        else: self.current_raw_frame = None
        ocr_reward, ocr_done = self._calculate_reward_and_done_ocr(self.current_raw_frame)
        final_terminated = terminated or ocr_done
        info['ocr_score'] = self.last_score; info['ocr_lives'] = self.last_lives; info['ocr_reward'] = ocr_reward
        return observation, ocr_reward, final_terminated, truncated, info

    def reset(self, **kwargs):
        observation, info = self.env.reset(**kwargs)
        if observation is not None: self.current_raw_frame = observation.copy()
        else: self.current_raw_frame = None
        self.last_score = 0; self.last_lives = 3
        score, lives = self._perform_ocr(self.current_raw_frame)
        if score is not None: self.last_score = score
        if lives is not None: self.last_lives = lives
        info['ocr_score'] = self.last_score; info['ocr_lives'] = self.last_lives
        return observation, info

    def _calculate_reward_and_done_ocr(self, frame):
        if frame is None: return 0.0, True
        reward, done = 0.0, False; current_score, current_lives = self._perform_ocr(frame)
        if current_score is not None:
            if current_score > self.last_score: reward += (current_score - self.last_score) * 0.01
            self.last_score = current_score
        if current_lives is not None:
            if current_lives < self.last_lives: reward -= 0.5
            self.last_lives = current_lives
            if current_lives <= 0: done = True; reward -= 1.0
        if not done:
             game_over_img = crop_region(frame, self.game_over_region_coords)
             processed_go_img = preprocess_for_ocr(game_over_img)
             if processed_go_img is not None:
                 try:
                     game_over_text = pytesseract.image_to_string(processed_go_img, config='--psm 6')
                     if "GAME OVER" in game_over_text.upper(): done = True; reward -= 1.0
                 except pytesseract.TesseractNotFoundError: pass
                 except Exception as e: print(f"Game Over OCR error: {e}")
        return reward, done

    def _perform_ocr(self, frame):
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
        return processed

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
    """Runs the main game loop with Pygame display, OCR, and PPO."""
    global base_env_global, processed_env_global, pygame_initialized, screen, running
    frame_delay = 1.0 / fps if fps > 0 else 0
    last_ocr_print_time = time.time()
    model = None
    vec_env = None # Use vec_env for SB3 interaction

    try:
        print(f"Attempting to launch game: {game}, state: {state}")
        # 1. Create base environment
        base_env_global = retro.make(game=game, state=state, render_mode="rgb_array")

        # 2. Wrap for accessing raw frame and calculating OCR reward
        reward_env = CustomRewardWrapper(base_env_global)

        # 3. Wrap for Visual Preprocessing
        processed_env_global = VisualPreprocessingWrapper(reward_env, width=FRAME_WIDTH, height=FRAME_HEIGHT, num_stacked=NUM_STACKED_FRAMES)

        # 4. Wrap for SB3 compatibility
        vec_env = DummyVecEnv([lambda: processed_env_global])
        # We interact with vec_env from now on for SB3

        print("Environment stack initialized.")
        print(f"Action Space: {vec_env.action_space}")
        print(f"Observation Space (Processed): {vec_env.observation_space.shape} {vec_env.observation_space.dtype}")

        # Initialize Pygame using base env's initial frame
        initial_obs_render, _ = base_env_global.reset()
        if initial_obs_render is None: raise Exception("Failed to get initial frame for Pygame setup.")
        frame_height_render, frame_width_render, _ = initial_obs_render.shape
        window_size = (frame_width_render * DISPLAY_SCALE, frame_height_render * DISPLAY_SCALE)
        pygame.init(); pygame.display.set_caption(f"AutoGamer AI - {game}"); screen = pygame.display.set_mode(window_size); pygame_initialized = True
        print("Pygame window initialized.")

        # --- Load or Create PPO Model ---
        model_save_path = os.path.join(args.model_dir, args.model_name)
        os.makedirs(args.model_dir, exist_ok=True)
        model_load_fullpath = f"{model_save_path}.zip"

        if args.load_model or args.run_only:
            if os.path.exists(model_load_fullpath):
                print(f"--- Loading Model from {model_load_fullpath} ---")
                model = PPO.load(model_load_fullpath, env=vec_env) # Load with vec_env
                print("Model loaded successfully.")
            else:
                print(f"Error: Model file not found at {model_load_fullpath}")
                if args.run_only: return
                print("Creating a new model instead."); args.load_model = False

        if not (args.load_model or args.run_only):
            print("--- Creating New PPO Model ---")
            model = PPO( "CnnPolicy", vec_env, verbose=1, n_steps=128, batch_size=32, n_epochs=4, gamma=0.99, gae_lambda=0.95, clip_range=0.1, ent_coef=0.01, learning_rate=2.5e-4, tensorboard_log="./ppo_tensorboard/" ) # Log to different dir

        # --- Train or Run ---
        if not args.run_only and model:
            print("--- Starting Training ---")
            # Training loop using model.learn()
            try:
                total_target_steps = args.timesteps
                num_saves = total_target_steps // args.save_freq
                steps_per_save = args.save_freq
                for i in range(1, num_saves + 1):
                     if not running: break
                     model.learn(total_timesteps=steps_per_save, log_interval=1, tb_log_name="PPO_WSL_OCR", reset_num_timesteps=(i==1 and not args.load_model), progress_bar=True)
                     current_total_step = i * steps_per_save
                     save_path_step = f"{model_save_path}_step_{current_total_step}"
                     model.save(save_path_step); print(f"--- Checkpoint Saved to {save_path_step}.zip ---")
                remaining_steps = total_target_steps % args.save_freq
                if remaining_steps > 0 and running:
                    model.learn(total_timesteps=remaining_steps, log_interval=1, tb_log_name="PPO_WSL_OCR", reset_num_timesteps=False, progress_bar=True)
                if running:
                    print(f"--- Training Finished ({total_target_steps} steps attempted) ---")
                    model.save(model_save_path); print(f"--- Final Model Saved to {model_save_path}.zip ---")
            except KeyboardInterrupt: print("\nTraining interrupted."); model.save(model_save_path + "_interrupted")
            except Exception as e: print(f"Training error: {e}"); model.save(model_save_path + "_error"); raise(e)

        if model:
            print("\n--- Running Inference Loop (Press Esc in Pygame window to stop) ---")
            obs = vec_env.reset() # Get initial observation from vec_env
            while running:
                loop_start_time = time.time()

                # --- Get Action from PPO Agent ---
                action, _states = model.predict(obs, deterministic=True)
                # ---

                # --- Pygame Events (for quitting) ---
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False; break
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False; break
                if not running: break
                # ---

                # --- Step Environment with Agent's Action ---
                obs, reward, done, info_list = vec_env.step(action) # Step the vec_env
                info = info_list[0] # Get info dict from the wrapped env
                # ---

                # --- Display Raw Frame & Print OCR Info ---
                # Access the raw frame stored by the reward wrapper
                # vec_env -> DummyVecEnv -> processed_env (VisualPreprocessingWrapper) -> reward_env (CustomRewardWrapper)
                raw_frame_to_display = vec_env.envs[0].env.current_raw_frame

                if raw_frame_to_display is not None:
                    try:
                        frame_pygame = np.transpose(raw_frame_to_display, (1, 0, 2))
                        game_surface = pygame.surfarray.make_surface(frame_pygame)
                        scaled_surface = pygame.transform.scale(game_surface, window_size)
                        screen.blit(scaled_surface, (0, 0))
                        pygame.display.flip()
                    except Exception as e: print(f"Error during Pygame drawing: {e}")

                    current_time = time.time()
                    if current_time - last_ocr_print_time >= 1.0:
                         score = info.get('ocr_score', 'N/A'); lives = info.get('ocr_lives', 'N/A')
                         print(f"[{time.strftime('%H:%M:%S')}] OCR - Score: {score}, Lives: {lives}, Step Reward: {reward[0]:.4f}")
                         last_ocr_print_time = current_time
                else: print(f"  Warning: Raw frame for display is None.")
                # ---

                if done.any(): # Check the done flag from vec_env
                    print("Episode finished. Resetting...")
                    obs = vec_env.reset()
                # ---

                # Maintain FPS
                elapsed = time.time() - loop_start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0: time.sleep(sleep_time)
        else: print("No model available to run.")


    except Exception as e: print(f"An error occurred: {e}"); import traceback; traceback.print_exc()
    finally: signal_handler(None, None) # Ensure cleanup

# --- Main Execution ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler); signal.signal(signal.SIGTERM, signal_handler)
    parser = argparse.ArgumentParser(description="Run retro game with Pygame display, OCR, and PPO (WSL).")
    parser.add_argument("--game", type=str, default=DEFAULT_GAME)
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--fps", type=int, default=TARGET_FPS)
    parser.add_argument("--timesteps", type=int, default=50_000)
    parser.add_argument("--save_freq", type=int, default=10_000)
    parser.add_argument("--model_dir", type=str, default="./wsl_models") # Renamed model dir
    parser.add_argument("--model_name", type=str, default="ppo_airstriker_wsl_ocr")
    parser.add_argument("--load_model", action="store_true")
    parser.add_argument("--run_only", action="store_true")
    args = parser.parse_args()
    state_arg_value = args.state
    state_to_load = retro.State.DEFAULT if isinstance(args.state, str) and args.state.upper() == 'DEFAULT' else state_arg_value
    run_game_loop(args.game, state_to_load, args.fps, args)
    print("Main script finished.")

