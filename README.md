# AutoGamer AI Framework

> **Note:** This project was developed as my final year dissertation for the Computer Science BSc course at Birmingham City University (2024-2025). This project builds upon Farama Foundation's work in stable-retro, which itself also includes third-party work. 

> **Legal:** No copyrighted game ROMs are distributed within this project. The ROMs used in this project were either available through Stable Retro or publicly available and free ‘Homebrew’ ROMs. External users of the artefact are required to supply their own ROM files for specific games they wish to integrate, which consequently rests entirely the legal responsibility for obtaining and using of these game ROMs on the end-user. Within this project, the use of emulation and game ROMs was strictly for non-commercial, academic research purposes focused on investigating AI behaviour in simulated environments.  

AutoGamer AI is a modular Python framework designed to train and evaluate reinforcement learning agents in retro video games using only visual input. It is built upon the foundational capabilities of the **[stable-retro](https://github.com/Farama-Foundation/stable-retro)** library, extending it with a structured system for managing game-specific logic, custom reward functions, and agent training pipelines.

The primary goal of this project was to address the challenge of AI generalisation by creating an adaptable framework rather than an agent optimised for a single game. It supports two primary modes of interaction: a deeply integrated mode using `stable-retro`'s environment, and a proof-of-concept mode using direct screen capture and OCR for a truly "visual-only" approach.


---

## Key Features 📋

This framework introduces a structured layer on top of `stable-retro` to streamline research and experimentation:

* **Modular, Game-Specific Architecture:** A core feature is a dynamic management system (`GameWrapperManager`) that loads game-specific Python modules at runtime. This allows for:
    * **Custom Observation Wrappers:** Tailor how game state information is presented to the AI.
    * **Custom Reward Functions:** Design sophisticated reward-shaping logic beyond simple score increases. For example, the included `NHL'94` implementation has separate reward functions for offensive and defensive strategies.
    * **Game-Specific AI Logic:** Encapsulate unique AI behaviours or logic for different games.

* **Reinforcement Learning Pipeline:**
    * Integrates **Stable Baselines3** for reliable implementations of RL algorithms like Proximal Policy Optimisation (PPO).
    * Uses a standard visual preprocessing pipeline (grayscale, resize, frame stacking) to prepare game frames for CNN-based policies.
    * Provides structured scripts for orchestrating training and evaluation workflows.

* **Screen Capture & OCR Proof-of-Concept:**
    * Includes standalone scripts that demonstrate training an agent on an external emulator window.
    * Uses `mss` for efficient screen capture and `pyautogui` for input simulation.
    * Calculates rewards in real-time by performing **Optical Character Recognition (OCR)** on specific screen regions (e.g., score, lives) using `pytesseract`.

* **GUI Launcher:**
    * Includes a user-friendly Tkinter UI (`AutoGamerUI.py`) to launch pre-configured training demos and game-specific training scripts without needing to type full commands in the terminal.

---

## Project Architecture 🏗️

The framework is logically decomposed into four interconnected modules that form the agent-environment feedback loop:

1.  **Environment Interaction Module:** Manages the interface with the `stable-retro` emulator, handling the game state, actions, and observations.
2.  **Visual Perception Module:** The Machine Vision pipeline. It processes raw visual frames from the emulator, performing grayscale conversion, resizing, and frame stacking to create a state representation for the agent.
3.  **Agent Development Module:** The "brain" of the system. It contains the Stable Baselines3 PPO agent and its CNN policy, handling both the learning process and action selection (inference).
4.  **Action Execution Module:** Translates the agent's integer-based action choice into the specific multi-binary controller input required by the `stable-retro` environment.

---

## Technologies Used 🛠️

This project leverages a powerful ecosystem of Python libraries for reinforcement learning and computer vision:

* **Core Framework:** Python 3.9 (required for `gym-retro` compatibility)
* **Game Environment:** Stable-Retro
* **Reinforcement Learning:** Stable Baselines3 (PyTorch)
* **Machine Vision & Processing:** OpenCV-Python, NumPy
* **Screen Capture & Input:** mss, PyAutoGUI, Pillow
* **OCR:** Pytesseract (wrapper for Google's Tesseract OCR Engine)

---

## How to Set Up & Run 🚀

### 1. Base Installation

This project depends entirely on **Stable-Retro**. Please follow the official installation instructions from the `stable-retro` README file first. It is recommended to use Ubuntu 22.04 (or WSL on Windows).

A `requirements.txt` file is provided to install the necessary Python libraries.

### 2. Quick Start (GUI Launcher)

The most user-friendly way to interact with the framework is via the GUI launcher. This allows you to run training demos and full training sessions for specific games.

To run the UI, execute the following command from the project's root directory:
```bash
python3 AutoGamerUI.py
```

From the UI, you can launch various pre-configured scripts that will open in a new terminal window.

### 3. Training Models (Command Line)

For more direct control, you can run the training scripts from the command line. For example, to run a full training session for Airstriker-Genesis using the general-purpose trainer:
```bash
python3 model_trainer.py --env Airstriker-Genesis --num_env 8 --num_timesteps 10000000
```

### 4. Running the Screen Capture & OCR Proof-of-Concept


This experimental feature allows the framework to "watch" and play an external emulator window.

Prerequisites: You must have an emulator running the game in a window that is visible on your desktop. The scripts are configured to look for a window with a specific title (e.g., "AutoGamer AI - Airstriker-Genesis (Ubuntu-22.04)").

External OCR Version: This script captures the window, performs OCR, and displays the results without agent interaction.
```bash
python3 capture_display.py
```
Integrated OCR Version (Manual Control): This script launches the game within an integrated display window and overlays OCR data, allowing you to play manually.

```bash
python3 airstriker_manual.py
```

