import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
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
        self.fail_count = 0

        # Set a high-contrast theme
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TButton', font=('Helvetica', 12), foreground='white', background='#333333')
        self.style.configure('TLabel', font=('Helvetica', 12), foreground='white', background='#333333')
        self.style.configure('TFrame', background='#333333')
        self.style.configure('TScrolledText', font=('Helvetica', 10), foreground='white', background='#222222')
        
        self.root.configure(background='#333333')

        # GUI Elements
        main_frame = ttk.Frame(root, padding="10 10 10 10")
        main_frame.pack(fill='both', expand=True)

        self.log = scrolledtext.ScrolledText(main_frame, height=20, width=50, wrap=tk.WORD, font=('Helvetica', 10), bg='#222222', fg='white', insertbackground='white')
        self.log.grid(row=0, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(main_frame, text="Start", command=self.start_script)
        self.start_button.grid(row=1, column=0, pady=5, sticky='ew')

        self.stop_button = ttk.Button(main_frame, text="Stop", command=self.stop_script, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=1, pady=5, sticky='ew')

        self.keybind_label = ttk.Label(main_frame, text=f"Start Keybind: {self.keybind_start}, Stop Keybind: {self.keybind_stop}")
        self.keybind_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Register fixed keybindings
        self.register_keybindings()

    def register_keybindings(self):
        keyboard.add_hotkey(self.keybind_start, self.start_script)
        keyboard.add_hotkey(self.keybind_stop, self.stop_script)

    def start_script(self):
        if not self.running:
            self.running = True
            self.fail_count = 0
            self.start_button.state(['disabled'])
            self.stop_button.state(['!disabled'])
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
            self.start_button.state(['!disabled'])
            self.stop_button.state(['disabled'])
            if hasattr(self, 'script_thread') and self.script_thread.is_alive():
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
                self.fail_count = 0
                button_x = max_loc[0] + reference_image.shape[1] // 2
                button_y = max_loc[1] + reference_image.shape[0] // 2
                self.log_message(f'Button found at: ({button_x}, {button_y}) with match confidence: {max_val}')
                pyautogui.moveTo(button_x, button_y)
                pyautogui.click()
                time.sleep(1)  # Sleep to avoid too rapid clicks
            else:
                self.fail_count += 1
                self.log_message(f'Button not found. Max confidence: {max_val}. Fail count: {self.fail_count}')
                if self.fail_count >= 5:
                    pyautogui.moveRel(1, 1)  # Move the mouse slightly
                    self.log_message('Mouse moved slightly to refresh pointer.')
                    self.fail_count = 0
                time.sleep(1)  # Sleep before retrying

        self.log_message("Script stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonFinderApp(root)
    root.mainloop()
