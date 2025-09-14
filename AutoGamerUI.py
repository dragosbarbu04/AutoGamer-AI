import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import sys
import os

# --- Configuration ---
# Define the paths to your scripts relative to this UI script
# Or provide absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Assumes scripts are in the same dir or subdirs

# --- Paths to your scripts ---
# Adjust these paths as necessary!
# Assuming 'retro/examples/ppo.py' is a generic PPO script that can take game/state args
GENERAL_PPO_SCRIPT = os.path.join(SCRIPT_DIR, "retro/examples/ppo.py") 
MODEL_TRAINER_SCRIPT = os.path.join(SCRIPT_DIR, "model_trainer.py") # General purpose trainer
MODEL_VS_GAME_SCRIPT = os.path.join(SCRIPT_DIR, "model_vs_game.py")

# Game specific trainer scripts
MK2_TRAINER_SCRIPT = os.path.join(SCRIPT_DIR, "mk2_trainer.py")
NHL_TRAINER_SCRIPT = os.path.join(SCRIPT_DIR, "nhl941on1_trainer.py")
WWF_TRAINER_SCRIPT = os.path.join(SCRIPT_DIR, "wwf_trainer.py")
# Note: STANDARD_TRAINER_SCRIPT was previously used for Airstriker. 
# If Airstriker has its own dedicated trainer script like the others, define it here.
# Otherwise, model_trainer.py will be used with Airstriker-specific args.


# --- Default arguments for scripts ---
AIRSTRIKER_PPO_DEMO_ARGS = {
    "--game": "NHL941on1-Genesis", # Example game for a quick demo
    "--state": "PenguinsVsSenators", # Example state for a quick demo
    # Add any other specific args for a quick demo, like fewer timesteps
}

MK2_PPO_DEMO_ARGS = {
    "--game": "MortalKombatII-Genesis",
    "--state": "Level1.LiuKangVsJax", # Example state for a quick demo
    # Add any other specific args for a quick demo
}

# Args for the "Train Airstriker Model" button (using the general model_trainer.py)
AIRSTRIKER_FULL_TRAIN_ARGS = {
    "--env": "Airstriker-Genesis", # model_trainer.py might use --env
    # "--game": "Airstriker-Genesis", # if model_trainer.py uses --game
    "--num_env": "8", 
    "--num_timesteps": "10000000", # Reduced for practicality if it was 100M
    # Add other relevant args for model_trainer.py, e.g., --alg, --nn
    # "--play": "", # This arg might be for playing after training, confirm its use
}

# For game-specific trainers, they often parse their own detailed arguments.
# EMPTY_ARGS is fine if the trainer scripts have reasonable internal defaults
# or if you expect users to modify the scripts themselves for specific model paths etc.
EMPTY_ARGS = {} 

# Example for Model vs Game (if you want to add it back)
# DEFAULT_MODEL_VS_GAME_ARGS = {
#     "--env": "NHL941on1-Genesis",
#     "--state": "PenguinsVsSenators",
#     "--model_1": "./models/DefenseZone", # Ensure this path is correct
#     "--model_2": "./models/ScoreGoal",   # Ensure this path is correct
#     "--nn": "MlpPolicy",
#     "--rf": "General"
# }

# --- Function to run scripts ---
def run_script(script_path, args_dict):
    """Launches a python script in a new terminal window."""
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"Script not found:\n{script_path}")
        return

    python_executable = sys.executable or "python3" # Use current python or fallback

    command = [python_executable, script_path]
    for arg, value in args_dict.items():
        command.append(arg)
        if value is not None and value != "": # Handle flags and arguments with values
            command.append(str(value))
        elif value == "": # Handle arguments that are flags meant to be present without a value
            pass # The key itself is the flag

    print(f"Running command: {' '.join(command)}") 

    try:
        if sys.platform == "win32":
            subprocess.Popen(['start', 'cmd', '/k'] + command, shell=True)
        elif sys.platform == "darwin":
            # For macOS, construct the command string for osascript
            cmd_str = " ".join(f"'{c}'" if " " in c else c for c in command) # Handle spaces in paths/args
            osascript_cmd = f'tell app "Terminal" to do script "{cmd_str}"'
            subprocess.Popen(['osascript', '-e', osascript_cmd])
        else: # Linux (including WSL)
            terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'xterm']
            terminal_found = False
            for term in terminals:
                try:
                    if term == 'xterm':
                        cmd_str = " ".join(command)
                        # Keep xterm open after command finishes
                        subprocess.Popen([term, '-hold', '-e', 'bash', '-c', cmd_str])
                    elif term == 'gnome-terminal' or term == 'konsole' or term == 'xfce4-terminal':
                         # These terminals usually take '--' to separate terminal options from the command
                        subprocess.Popen([term, '--'] + command)
                    else: # Fallback for other terminals if needed
                        subprocess.Popen([term, '-e'] + command) # Common for older/simpler terms
                    terminal_found = True
                    break
                except FileNotFoundError:
                    continue
            if not terminal_found:
                messagebox.showerror("Error", "Could not find a compatible terminal.\nPlease run the script manually.")
                return
        messagebox.showinfo("Launched", f"Attempting to launch script:\n{os.path.basename(script_path)}\nCheck the new terminal window.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch script:\n{script_path}\n\nError: {e}")

# --- UI Setup ---
root = tk.Tk()
root.title("AutoGamer AI Framework Launcher")
root.geometry("600x500")

# Style
style = ttk.Style()
try:
    style.theme_use('clam') 
except tk.TclError:
    print("Clam theme not available, using default.")

style.configure("TButton", padding=8, relief="flat", font=('Helvetica', 10))
style.configure("TLabel", padding=5, font=('Helvetica', 11))
style.configure("Header.TLabel", padding=(5, 10, 5, 5), font=('Helvetica', 12, 'bold')) # Main title style
style.configure("SubHeader.TLabel", padding=(5, 15, 5, 5), font=('Helvetica', 11, 'underline')) # Sub-title style


# --- Main Title ---
main_title_label = ttk.Label(root, text="AutoGamer AI Menu", style="Header.TLabel", anchor="center")
main_title_label.pack(pady=(10,0), fill=tk.X)

# --- Frame for Demo Training Buttons ---
demo_buttons_frame = ttk.Frame(root, padding="15 5 15 10")
demo_buttons_frame.pack(fill=tk.X, padx=10)

airstriker_demo_button = ttk.Button(
    demo_buttons_frame,
    text="Airstriker PPO Training Demo",
    command=lambda: run_script(GENERAL_PPO_SCRIPT, AIRSTRIKER_PPO_DEMO_ARGS)
)
airstriker_demo_button.pack(pady=5, fill=tk.X)

mk2_demo_button = ttk.Button(
    demo_buttons_frame,
    text="Mortal Kombat II PPO Training Demo",
    command=lambda: run_script(GENERAL_PPO_SCRIPT, MK2_PPO_DEMO_ARGS)
)
mk2_demo_button.pack(pady=5, fill=tk.X)


# --- Second Title for Game Specific Trainers ---
specific_trainers_title_label = ttk.Label(root, text="Game Specific Trainers", style="SubHeader.TLabel", anchor="center")
specific_trainers_title_label.pack(pady=(15,0), fill=tk.X) # Add some top padding

# --- Frame for Game Specific Trainer Buttons ---
specific_trainers_frame = ttk.Frame(root, padding="15 5 15 10")
specific_trainers_frame.pack(fill=tk.X, expand=True, padx=10) # expand=True if you want this section to take more space

train_airstriker_button = ttk.Button(
    specific_trainers_frame,
    text="Train Full Airstriker Model", # Uses model_trainer.py
    command=lambda: run_script(MODEL_TRAINER_SCRIPT, AIRSTRIKER_FULL_TRAIN_ARGS)
)
train_airstriker_button.pack(pady=5, fill=tk.X)

train_wwf_button = ttk.Button(
    specific_trainers_frame,
    text="Train WWF Model",
    command=lambda: run_script(WWF_TRAINER_SCRIPT, EMPTY_ARGS)
)
train_wwf_button.pack(pady=5, fill=tk.X)

train_nhl_button = ttk.Button(
    specific_trainers_frame,
    text="Train NHL941on1 Model",
    command=lambda: run_script(NHL_TRAINER_SCRIPT, EMPTY_ARGS)
)
train_nhl_button.pack(pady=5, fill=tk.X)

train_mk2_button = ttk.Button(
    specific_trainers_frame,
    text="Train Mortal Kombat II Model",
    command=lambda: run_script(MK2_TRAINER_SCRIPT, EMPTY_ARGS)
)
train_mk2_button.pack(pady=5, fill=tk.X)

# --- Run ---
root.mainloop()