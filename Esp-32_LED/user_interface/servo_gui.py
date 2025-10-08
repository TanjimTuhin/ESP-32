#!/usr/bin/env python3
"""
ESP32 Servo Control - Minimal GUI Client (with Last IP Memory)
- Connect to ESP32 over TCP
- Control servo angle with slider
- Remembers last IP and Port
"""

import socket
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os


class ESP32Client:
    def __init__(self, host, port=8080, auth_password="IoTDevice2024"):
        self.host = host
        self.port = port
        self.auth_password = auth_password
        self.socket = None
        self.authenticated = False

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            self.receive_message()  # auth challenge
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")
            return False

    def authenticate(self) -> bool:
        try:
            self.send_message({"command": "auth", "password": self.auth_password})
            time.sleep(0.5)
            response = self.receive_message()
            if response and response.get("status") == "success":
                self.authenticated = True
                return True
            else:
                messagebox.showerror("Auth Failed", str(response))
                return False
        except Exception as e:
            messagebox.showerror("Auth Error", str(e))
            return False

    def send_message(self, message: dict) -> None:
        try:
            if self.socket:
                self.socket.send((json.dumps(message) + "\n").encode())
        except Exception as e:
            print(f"Send error: {e}")

    def receive_message(self) -> dict:
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

    def control_servo(self, angle: int) -> None:
        self.send_message({"command": "set_servo", "angle": angle})

    def close(self) -> None:
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.authenticated = False


class ServoGUI:
    LAST_IP_FILE = "last_ip.txt"

    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Servo Control")
        self.client = None
        self.connected = False

        # Connection panel
        conn_frame = ttk.Frame(root)
        conn_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(conn_frame, text="IP:").pack(side="left")
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.pack(side="left", padx=5)

        ttk.Label(conn_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(conn_frame, width=6)
        self.port_entry.pack(side="left", padx=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_esp32)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_from_esp32, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)

        # Load last IP and Port if available
        self.load_last_ip()

        # Servo control panel
        servo_frame = ttk.LabelFrame(root, text="Servo Control")
        servo_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(servo_frame, text="Angle:").pack(side="left")

        self.servo_var = tk.IntVar(value=90)
        self.servo_scale = ttk.Scale(
            servo_frame,
            from_=0,
            to=180,
            variable=self.servo_var,
            orient="horizontal",
            length=300,
            command=self.on_servo_scale_change
        )
        self.servo_scale.pack(side="left", padx=10)

        self.servo_value_label = ttk.Label(servo_frame, text="90°")
        self.servo_value_label.pack(side="left")

    def load_last_ip(self):
        """Load last IP and Port from file"""
        if os.path.exists(self.LAST_IP_FILE):
            try:
                with open(self.LAST_IP_FILE, "r") as f:
                    data = f.read().strip().split(":")
                    if len(data) == 2:
                        ip, port = data
                        self.ip_entry.insert(0, ip)
                        self.port_entry.insert(0, port)
                        return
            except:
                pass
        # default values if no file
        self.ip_entry.insert(0, "192.168.1.100")
        self.port_entry.insert(0, "8080")

    def save_last_ip(self, ip, port):
        """Save last IP and Port to file"""
        try:
            with open(self.LAST_IP_FILE, "w") as f:
                f.write(f"{ip}:{port}")
        except:
            pass

    def connect_to_esp32(self):
        if self.connected:
            return

        host = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())

        self.client = ESP32Client(host, port)

        if self.client.connect() and self.client.authenticate():
            self.connected = True
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.save_last_ip(host, port)
            messagebox.showinfo("Connected", f"Connected to ESP32 at {host}:{port}")

    def disconnect_from_esp32(self):
        if not self.connected:
            return

        if self.client:
            self.client.close()
            self.client = None

        self.connected = False
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        messagebox.showinfo("Disconnected", "Disconnected from ESP32")

    def on_servo_scale_change(self, value):
        """Send servo angle whenever slider moves"""
        angle = int(float(value))
        self.servo_value_label.config(text=f"{angle}°")

        if self.connected and self.client:
            self.client.control_servo(angle)

    def on_closing(self):
        if self.connected:
            self.disconnect_from_esp32()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ServoGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
