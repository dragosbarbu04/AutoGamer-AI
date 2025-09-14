"""
Display - Modified to only show game screen
"""

from os import environ
import gymnasium as gym
import numpy as np
# Removed unused reward function imports
from game_wrappers.nhl941on1_gamestate import NHL941on1GameState # Keep if needed by step/reset
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame # pylint: disable=wrong-import-position,wrong-import-order
import pygame.freetype # pylint: disable=wrong-import-position,wrong-import-order


class NHL94GameDisplayEnv(gym.Wrapper):
    # __init__ remains mostly the same, but remove attributes only used for drawing extra info if desired
    def __init__(self, env, args, total_params, nn_type, button_names):
        gym.Wrapper.__init__(self, env)

        # Keep necessary dimensions for window creation
        self.FB_WIDTH = 1920 # Base surface width (can be simplified if not drawing info)
        self.FB_HEIGHT = 1080 # Base surface height
        self.GAME_WIDTH = 320 * 4 # Scaled game width
        self.GAME_HEIGHT = 240 * 4 # Scaled game height

        # Init Window
        pygame.init()
        flags = pygame.RESIZABLE
        if args.fullscreen:
            flags |= pygame.FULLSCREEN
        # Set window size based on desired display size
        self.screen = pygame.display.set_mode((args.display_width, args.display_height), flags)
        # main_surf might not be needed if not drawing overlays
        # self.main_surf = pygame.Surface((self.FB_WIDTH, self.FB_HEIGHT))
        # self.main_surf.set_colorkey((0,0,0))

        # Keep font if needed for window title or future simple text
        self.font = pygame.freetype.SysFont('symbol', 30)
        self.font.antialiased = True
        
        self.args = args
        # Store button names if needed for action mapping during manual input capture
        self.button_names = button_names 
        self.player_actions = [0] * 12 # For capturing player input

        # Attributes for drawing extra info (can be removed)
        # self.num_params = total_params
        # self.nn_type = nn_type
        # self.action_probabilities = None
        # self.frameRewardList = [0.0] * 200
        # self.game_state = NHL941on1GameState()
        # self.model_in_use = 0
        # self.model_params = [None, None, None]
        # self.model_names = ["CODE", "DEFENSE ZONE", "SCORING OPP"]
        
        self.scr_count = 0 # Keep if screenshot functionality is desired

    def reset(self, **kwargs):
        # Reset the underlying environment
        return self.env.reset(**kwargs)

    # Removed set_reward as it was only used for the reward graph

    def step(self, ac):
        # Step the underlying environment
        ob, rew, done, info = self.env.step(ac)

        # Get the latest frame buffer for display
        framebuffer = self.render() # Assumes render() gets the raw frame

        # Draw *only* the game frame
        self.draw_frame(framebuffer) # Pass only the frame

        # Still need to process input events for window management and player input
        self.get_input() 
        keystate = self.get_input()
        self.ProcessKeyState(keystate) # Processes quit keys and player actions

        return ob, rew, done, info # Return original env results

    def seed(self, s):
        # Pass seeding down if necessary, though might not be used in Wrapper
        # self.rng.seed(s) # Need to define self.rng if used
        pass

    # Removed draw_string, draw_contact_info, draw_basic_info, draw_ai_overview,
    # draw_model, draw_game_stats, DrawFrameRewardHistogram, set_ai_sys_info
    # as they were only used for drawing extra info.

    def draw_frame(self, frame_img):
        """ Draws only the scaled game frame to the screen. """
        if frame_img is None:
            # Handle case where frame is missing (optional: display placeholder)
            self.screen.fill((0, 0, 0)) # Fill black
            pygame.display.flip()
            return
            
        try:
            self.screen.fill((0, 0, 0)) # Clear screen
            
            # Transpose frame (H, W, C) -> (W, H, C) for Pygame surface
            emu_screen = np.transpose(frame_img, (1,0,2))
            surf = pygame.surfarray.make_surface(emu_screen)

            # Scale the game surface to the display window size
            scaled_surf = pygame.transform.scale(surf, (self.args.display_width, self.args.display_height))
            
            # Blit the scaled surface onto the screen
            self.screen.blit(scaled_surf, (0, 0))

            # Update the display
            pygame.display.flip()
        except Exception as e:
            print(f"Error drawing frame: {e}")


    def ProcessKeyState(self, keystate):
        """ Processes keyboard state for quitting and player actions. """
        if keystate[pygame.K_q] or keystate[pygame.K_ESCAPE]:
            # Instead of exit(), signal the main loop to stop gracefully
            # This requires modification in player_vs_model.py's loop
            print("Quit key pressed. Signalling loop to stop.")
            # Set a flag or raise a specific exception perhaps?
            # For now, we keep exit() but ideally the main loop handles termination
            pygame.quit() # Clean up pygame
            sys.exit() # Exit script

        # Capture player 2's actions (assuming player 1 is AI)
        self.player_actions[0] = 1 if keystate[pygame.K_x] else 0      # B
        self.player_actions[1] = 1 if keystate[pygame.K_z] else 0      # A
        self.player_actions[2] = 1 if keystate[pygame.K_TAB] else 0    # MODE
        self.player_actions[3] = 1 if keystate[pygame.K_RETURN] else 0 # START
        self.player_actions[4] = 1 if keystate[pygame.K_UP] else 0     # UP
        self.player_actions[5] = 1 if keystate[pygame.K_DOWN] else 0   # DOWN
        self.player_actions[6] = 1 if keystate[pygame.K_LEFT] else 0   # LEFT
        self.player_actions[7] = 1 if keystate[pygame.K_RIGHT] else 0  # RIGHT
        self.player_actions[8] = 1 if keystate[pygame.K_c] else 0      # C
        self.player_actions[9] = 1 if keystate[pygame.K_a] else 0      # Y (maps to key A)
        self.player_actions[10] = 1 if keystate[pygame.K_s] else 0     # X (maps to key S)
        self.player_actions[11] = 1 if keystate[pygame.K_d] else 0     # Z (maps to key D)


        if keystate[pygame.K_i]: # Screenshot functionality
            self.scr_count += 1
            try:
                 pygame.image.save(self.screen, f"screenshot_pvm_{self.scr_count:03d}.png")
                 print(f"Saved screenshot_pvm_{self.scr_count:03d}.png")
            except Exception as e:
                 print(f"Error saving screenshot: {e}")


    def get_input(self):
        """ Pumps Pygame events and gets keyboard state. """
        # It's important to pump events to keep the window responsive
        pygame.event.pump() 
        keystate = pygame.key.get_pressed()
        return keystate

