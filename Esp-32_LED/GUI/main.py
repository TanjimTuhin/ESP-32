"""
Main entry point for ESP32 IoT Control System
"""

import tkinter as tk
from gui import ESP32GUI

def main():
    root = tk.Tk()
    app = ESP32GUI(root)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()