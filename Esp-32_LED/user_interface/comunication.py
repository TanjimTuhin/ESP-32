#!/usr/bin/env python3
"""
ESP32 IoT Control System - Python Client
==========================================

Controls 5 LEDs and monitors 5 push buttons + potentiometer
from an ESP32 IoT server via TCP JSON protocol.

Usage:
    python client.py
"""

import socket
import json
import threading
import sys
from datetime import datetime

class ESP32Client:
    def __init__(self, host='192.168.4.1', port=8080, auth_password='IoTDevice2024'):
        self.host = host
        self.port = port
        self.auth_password = auth_password
        self.socket = None
        self.authenticated = False
        self.running = False
        self.data_lock = threading.Lock()
        self.latest_status = {}

    def connect(self):
        """Connect to ESP32 server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✓ Connected to ESP32 at {self.host}:{self.port}")

            # Wait for auth challenge
            response = self.receive_message()
            if response:
                print(f"Server: {response.get('message', 'Connected')}")

            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def authenticate(self):
        """Authenticate with the server"""
        try:
            auth_msg = {"command": "auth", "password": self.auth_password}
            self.send_message(auth_msg)

            response = self.receive_message()
            if response.get('status') == 'success':
                self.authenticated = True
                print("✓ Authentication successful")
                return True
            else:
                print(f"✗ Authentication failed: {response.get('message')}")
                return False
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False

    def send_message(self, message):
        """Send JSON message to server"""
        try:
            json_str = json.dumps(message) + '\n'
            self.socket.send(json_str.encode())
        except Exception as e:
            print(f"✗ Send error: {e}")

    def receive_message(self):
        """Receive JSON message from server"""
        try:
            data = self.socket.recv(1024).decode().strip()
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"✗ Receive error: {e}")
        return {}

    def start_monitoring(self):
        """Start background thread to monitor status updates"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("✓ Status monitoring started")

    def _monitor_loop(self):
        """Background loop to receive status updates"""
        while self.running:
            try:
                message = self.receive_message()
                if not message:
                    continue

                if message.get('type') == 'status':
                    with self.data_lock:
                        self.latest_status = message
                else:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Server: {message}")
            except:
                if self.running:
                    print("✗ Lost connection to server")
                break

    def control_led(self, led_number, state):
        """Control individual LED"""
        msg = {"command": "set_led", "led": led_number, "state": state}
        self.send_message(msg)

    def control_all_leds(self, state):
        """Control all LEDs"""
        msg = {"command": "set_all_leds", "state": state}
        self.send_message(msg)

    def get_status(self):
        """Request current status"""
        self.send_message({"command": "get_status"})

    def ping(self):
        """Send ping to test connection"""
        self.send_message({"command": "ping"})

    def print_status(self):
        """Print current system status"""
        with self.data_lock:
            if not self.latest_status:
                print("No status data available")
                return

            status = self.latest_status
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"\n{'='*50}")
            print(f"ESP32 System Status - {timestamp}")
            print(f"{'='*50}")

            # LEDs
            print("LEDs:")
            for led in status.get('leds', []):
                state = "ON " if led['state'] else "OFF"
                print(f"  LED {led['id']}: {state}")

            # Buttons
            print("\nButtons:")
            for btn in status.get('buttons', []):
                state = "PRESSED " if btn['pressed'] else "released"
                print(f"  Button {btn['id']}: {state}")

            # Potentiometer
            pot = status.get('potentiometer', {})
            if pot:
                print("\nPotentiometer:")
                print(f"  Raw: {pot.get('raw', 0)}")
                print(f"  Voltage: {pot.get('voltage', 0):.2f} V")
                print(f"  Percent: {pot.get('percent', 0)} %")

            print("="*50 + "\n")

    def close(self):
        self.running = False
        if self.socket:
            self.socket.close()
        print("✓ Disconnected")


def main():
    client = ESP32Client()

    if not client.connect():
        return
    if not client.authenticate():
        return

    client.start_monitoring()

    print("\nAvailable commands:")
    print("  led <id> on/off   -> Control individual LED (0-4)")
    print("  all on/off        -> Control all LEDs")
    print("  status            -> Show latest system status")
    print("  ping              -> Send ping to server")
    print("  exit              -> Quit program\n")

    try:
        while True:
            cmd = input(">> ").strip().lower()
            if not cmd:
                continue

            if cmd.startswith("led"):
                parts = cmd.split()
                if len(parts) == 3 and parts[1].isdigit():
                    led_id = int(parts[1])
                    state = parts[2] == "on"
                    client.control_led(led_id, state)
                else:
                    print("Usage: led <id> on/off")

            elif cmd.startswith("all"):
                parts = cmd.split()
                if len(parts) == 2:
                    state = parts[1] == "on"
                    client.control_all_leds(state)
                else:
                    print("Usage: all on/off")

            elif cmd == "status":
                client.print_status()

            elif cmd == "ping":
                client.ping()

            elif cmd == "exit":
                break

            else:
                print("Unknown command")
    except KeyboardInterrupt:
        print("\nExiting...")

    client.close()


if __name__ == "__main__":
    main()
