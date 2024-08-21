import tkinter as tk
from tkinter import scrolledtext
import threading
import pyautogui
import cv2
import numpy as np
import time
import keyboard
import sys
import os

class ButtonFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Button Finder")

        # Make window always on top
        self.root.attributes('-topmost', True)

        # Initialize state
        self.running = False
        self.keybind_start = 'space'
        self.keybind_stop = 'esc'

        # GUI Elements
        self.log = scrolledtext.ScrolledText(root, height=20, width=50)
        self.log.pack(pady=10)

        self.start_button = tk.Button(root, text="Start", command=self.start_script)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_script, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.keybind_label = tk.Label(root, text=f"Start Keybind: {self.keybind_start}, Stop Keybind: {self.keybind_stop}")
        self.keybind_label.pack(pady=5)

        # Register fixed keybindings
        self.register_keybindings()

    def register_keybindings(self):
        keyboard.add_hotkey(self.keybind_start, self.start_script)
        keyboard.add_hotkey(self.keybind_stop, self.stop_script)

    def start_script(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_message("Script started.")
            if not hasattr(self, 'script_thread') or not self.script_thread.is_alive():
                self.script_thread = threading.Thread(target=self.run_script)
                self.script_thread.start()
        else:
            self.log_message("Script is already running.")

    def stop_script(self):
        if self.running:
            self.log_message("Stopping script...")
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if hasattr(self, 'script_thread'):
                self.script_thread.join()
            self.log_message("Script stopped.")
        else:
            self.log_message("Script is not running.")

    def log_message(self, message):
        # Ensure GUI updates are made in the main thread
        self.root.after(0, lambda: self.log.insert(tk.END, f"{message}\n"))
        self.root.after(0, lambda: self.log.yview(tk.END))

    def run_script(self):
        # Determine the path for the reference image
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(__file__)

        reference_image_path = os.path.join(application_path, 'slow download.png')
        reference_image = cv2.imread(reference_image_path, cv2.IMREAD_UNCHANGED)

        if reference_image is None:
            self.log_message(f"Failed to load reference image from {reference_image_path}")
            return

        if len(reference_image.shape) == 3 and reference_image.shape[2] == 4:
            reference_image = cv2.cvtColor(reference_image, cv2.COLOR_BGRA2GRAY)
        elif len(reference_image.shape) == 3 and reference_image.shape[2] == 3:
            reference_image = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)

        threshold = 0.7

        while self.running:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

            result = cv2.matchTemplate(screenshot, reference_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                button_x = max_loc[0] + reference_image.shape[1] // 2
                button_y = max_loc[1] + reference_image.shape[0] // 2
                self.log_message(f'Button found at: ({button_x}, {button_y}) with match confidence: {max_val}')
                cv2.rectangle(screenshot, max_loc, (max_loc[0] + reference_image.shape[1], max_loc[1] + reference_image.shape[0]), (0, 255, 0), 2)
                pyautogui.moveTo(button_x, button_y)
                pyautogui.click()
                time.sleep(1)  # Sleep to avoid too rapid clicks
            else:
                self.log_message(f'Button not found. Max confidence: {max_val}')
                time.sleep(1)  # Sleep before retrying

        self.log_message("Script stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonFinderApp(root)
    root.mainloop()
