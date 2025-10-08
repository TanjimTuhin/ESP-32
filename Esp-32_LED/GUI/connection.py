"""
ESP32 connection and communication handling
"""

import socket
import json
import threading
import time

class ESP32Client:
    def __init__(self, host, port=8080, auth_password="IoTDevice2024"):
        self.host = host
        self.port = port
        self.auth_password = auth_password
        self.socket = None
        self.authenticated = False
        self.running = False
        self.latest_status = {}
        self.lock = threading.Lock()
        self.connection_callbacks = []
        self.status_callbacks = []

    def register_connection_callback(self, callback):
        """Register a callback for connection events"""
        self.connection_callbacks.append(callback)

    def register_status_callback(self, callback):
        """Register a callback for status updates"""
        self.status_callbacks.append(callback)

    def _notify_connection_event(self, connected, message=""):
        """Notify all registered connection callbacks"""
        for callback in self.connection_callbacks:
            callback(connected, message)

    def _notify_status_update(self, status):
        """Notify all registered status callbacks"""
        for callback in self.status_callbacks:
            callback(status)

    def connect(self):
        """Establish connection to ESP32"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            print(f"Connected to ESP32 at {self.host}:{self.port}")
            self.receive_message()  # read auth challenge
            return True
        except Exception as e:
            error_msg = f"Could not connect: {e}"
            self._notify_connection_event(False, error_msg)
            return False

    def authenticate(self):
        """Authenticate with ESP32"""
        try:
            self.send_message({"command": "auth", "password": self.auth_password})
            time.sleep(0.5)
            response = self.receive_message()
            if response and response.get("status") == "success":
                self.authenticated = True
                self._notify_connection_event(True, "Authentication successful")
                return True
            else:
                error_msg = f"Authentication failed: {response}"
                self._notify_connection_event(False, error_msg)
                return False
        except Exception as e:
            error_msg = f"Authentication error: {e}"
            self._notify_connection_event(False, error_msg)
            return False

    def send_message(self, message):
        """Send a message to ESP32"""
        try:
            if self.socket:
                self.socket.send((json.dumps(message) + "\n").encode())
        except Exception as e:
            print(f"Send error: {e}")

    def receive_message(self):
        """Receive a message from ESP32"""
        try:
            if self.socket:
                data = self.socket.recv(1024).decode()
                if not data:
                    return {}
                for line in data.strip().splitlines():
                    try:
                        return json.loads(line)
                    except:
                        continue
        except Exception as e:
            print(f"Receive error: {e}")
            return {}
        return {}

    def start_monitoring(self):
        """Start monitoring for status updates"""
        self.running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        threading.Thread(target=self._keep_alive, daemon=True).start()

    def _monitor_loop(self):
        """Monitor loop for receiving status updates"""
        buffer = ""
        while self.running:
            try:
                if not self.socket:
                    break
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                        if msg.get("type") == "status":
                            with self.lock:
                                self.latest_status = msg
                            self._notify_status_update(msg)
                        else:
                            print("Server:", msg)
                    except Exception as e:
                        print(f"JSON parse error: {e}")
                        continue
            except Exception as e:
                print("Lost connection:", e)
                self._notify_connection_event(False, f"Lost connection: {e}")
                break

    def _keep_alive(self):
        """Send periodic keep-alive messages"""
        while self.running and self.authenticated:
            time.sleep(25)
            self.ping()

    def control_led(self, led_number, state):
        """Control an individual LED"""
        self.send_message({"command": "set_led", "led": led_number, "state": state})
        time.sleep(0.1)
        self.get_status()

    def control_all_leds(self, state):
        """Control all LEDs at once"""
        self.send_message({"command": "set_all_leds", "state": state})
        time.sleep(0.1)
        self.get_status()

    def control_servo(self, angle):
        """Control servo position"""
        self.send_message({"command": "set_servo", "angle": angle})
        time.sleep(0.1)
        self.get_status()

    def get_status(self):
        """Request current status from ESP32"""
        self.send_message({"command": "get_status"})

    def ping(self):
        """Send ping to ESP32"""
        self.send_message({"command": "ping"})

    def close(self):
        """Close connection to ESP32"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.authenticated = False
        self._notify_connection_event(False, "Disconnected")