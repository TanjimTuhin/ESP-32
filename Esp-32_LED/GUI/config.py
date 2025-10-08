"""
Configuration management for ESP32 IoT Control System
"""

import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "host": "192.168.1.100",
    "port": 8080,
    "password": "IoTDevice2024",
    "window_geometry": "700x800"
}

def load_config():
    """Load configuration from file or return defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError:
        return False